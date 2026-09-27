
"""SQLite paper ledger. Paper execution only. No broker path."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXECUTION_MODE = "paper"  # hardcoded; do not add a live flag in v1


@dataclass
class Position:
    ticker: str
    shares: float
    avg_cost: float


@dataclass
class State:
    cash: float
    positions: dict[str, Position]
    started_at: str | None = None


class LedgerError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class Ledger:
    def __init__(self, db_path: str | Path, audit_log_path: str | Path, starting_cash: float = 100_000.0):
        if EXECUTION_MODE != "paper":
            raise RuntimeError("Live execution is not permitted in v1.")
        self.db_path = Path(db_path)
        self.audit_log_path = Path(audit_log_path)
        self.starting_cash = float(starting_cash)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS cash (
                  id INTEGER PRIMARY KEY CHECK (id = 1),
                  balance REAL NOT NULL CHECK (balance >= 0)
                );
                CREATE TABLE IF NOT EXISTS positions (
                  ticker TEXT PRIMARY KEY,
                  shares REAL NOT NULL CHECK (shares >= 0),
                  avg_cost REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS trades (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ts TEXT NOT NULL,
                  action TEXT NOT NULL,
                  ticker TEXT,
                  shares REAL,
                  price REAL,
                  reasoning TEXT,
                  reason_code TEXT
                );
                CREATE TABLE IF NOT EXISTS meta (
                  key TEXT PRIMARY KEY,
                  value TEXT NOT NULL
                );
                """
            )
            row = conn.execute("SELECT balance FROM cash WHERE id = 1").fetchone()
            if row is None:
                conn.execute("INSERT INTO cash (id, balance) VALUES (1, ?)", (self.starting_cash,))
                conn.execute(
                    "INSERT OR IGNORE INTO meta (key, value) VALUES ('started_at', ?)",
                    (datetime.now(timezone.utc).isoformat(),),
                )

    def get_state(self) -> State:
        with self._connect() as conn:
            cash = float(conn.execute("SELECT balance FROM cash WHERE id = 1").fetchone()["balance"])
            pos_rows = conn.execute("SELECT ticker, shares, avg_cost FROM positions WHERE shares > 0").fetchall()
            started = conn.execute("SELECT value FROM meta WHERE key = 'started_at'").fetchone()
        positions = {
            r["ticker"]: Position(ticker=r["ticker"], shares=float(r["shares"]), avg_cost=float(r["avg_cost"]))
            for r in pos_rows
        }
        return State(cash=cash, positions=positions, started_at=started["value"] if started else None)

    def buy(
        self,
        ticker: str,
        shares: float,
        price: float,
        *,
        nav: float,
        min_cash_buffer: float,
        max_position_weight: float,
        reasoning: str = "",
    ) -> None:
        ticker = ticker.upper()
        if shares <= 0 or price <= 0:
            raise LedgerError("SCHEMA_FAIL", "Buy requires positive shares and price.")
        cost = shares * price
        state = self.get_state()
        buffer = nav * min_cash_buffer
        if cost > state.cash - buffer + 1e-9:
            raise LedgerError("INSUFFICIENT_CASH", "Insufficient cash after buffer.")
        existing = state.positions.get(ticker)
        new_shares = (existing.shares if existing else 0.0) + shares
        new_cost_basis = (
            ((existing.shares * existing.avg_cost) if existing else 0.0) + cost
        )
        avg_cost = new_cost_basis / new_shares
        post_value = new_shares * price
        if nav > 0 and post_value / nav > max_position_weight + 1e-9:
            raise LedgerError("WEIGHT_CAP", "Position would exceed max_position_weight.")
        ts = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            try:
                conn.execute("BEGIN")
                conn.execute("UPDATE cash SET balance = balance - ? WHERE id = 1", (cost,))
                bal = conn.execute("SELECT balance FROM cash WHERE id = 1").fetchone()["balance"]
                if bal < -1e-9:
                    raise LedgerError("INSUFFICIENT_CASH", "Cash would go negative.")
                conn.execute(
                    """
                    INSERT INTO positions (ticker, shares, avg_cost) VALUES (?, ?, ?)
                    ON CONFLICT(ticker) DO UPDATE SET
                      shares = excluded.shares,
                      avg_cost = excluded.avg_cost
                    """,
                    (ticker, new_shares, avg_cost),
                )
                conn.execute(
                    "INSERT INTO trades (ts, action, ticker, shares, price, reasoning, reason_code) VALUES (?, 'buy', ?, ?, ?, ?, 'APPLIED')",
                    (ts, ticker, shares, price, reasoning),
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def sell(self, ticker: str, shares: float, price: float, *, reasoning: str = "") -> None:
        ticker = ticker.upper()
        if shares <= 0 or price <= 0:
            raise LedgerError("SCHEMA_FAIL", "Sell requires positive shares and price.")
        state = self.get_state()
        pos = state.positions.get(ticker)
        if pos is None or shares > pos.shares + 1e-9:
            raise LedgerError("INSUFFICIENT_SHARES", "Cannot sell more shares than held.")
        proceeds = shares * price
        remaining = pos.shares - shares
        ts = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            try:
                conn.execute("BEGIN")
                conn.execute("UPDATE cash SET balance = balance + ? WHERE id = 1", (proceeds,))
                if remaining <= 1e-9:
                    conn.execute("DELETE FROM positions WHERE ticker = ?", (ticker,))
                else:
                    conn.execute(
                        "UPDATE positions SET shares = ? WHERE ticker = ?",
                        (remaining, ticker),
                    )
                conn.execute(
                    "INSERT INTO trades (ts, action, ticker, shares, price, reasoning, reason_code) VALUES (?, 'sell', ?, ?, ?, ?, 'APPLIED')",
                    (ts, ticker, shares, price, reasoning),
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def snapshot(self, prices: dict[str, float]) -> dict[str, Any]:
        state = self.get_state()
        positions_mtm = []
        equity = 0.0
        for t, p in state.positions.items():
            px = float(prices.get(t, p.avg_cost))
            value = p.shares * px
            equity += value
            unrealized = (px - p.avg_cost) * p.shares
            weight = 0.0
            positions_mtm.append(
                {
                    "ticker": t,
                    "shares": p.shares,
                    "avg_cost": p.avg_cost,
                    "price": px,
                    "value": value,
                    "unrealized_pnl": unrealized,
                }
            )
        nav = state.cash + equity
        for row in positions_mtm:
            row["weight"] = (row["value"] / nav) if nav else 0.0
        return {
            "cash": state.cash,
            "nav": nav,
            "equity": equity,
            "positions": positions_mtm,
            "started_at": state.started_at,
        }

    def log_decision(self, payload: dict[str, Any]) -> None:
        # Never log secrets; caller must not put API keys in payload.
        line = json.dumps(payload, ensure_ascii=True)
        if "XAI_API_KEY" in line or "xai-" in line.lower():
            raise RuntimeError("Refusing to write payload that may contain API credentials.")
        with self.audit_log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def record_reject(self, action: str, ticker: str | None, shares: float | None, price: float | None, reasoning: str, code: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO trades (ts, action, ticker, shares, price, reasoning, reason_code) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ts, action, ticker, shares, price, reasoning, code),
            )
