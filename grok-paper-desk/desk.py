
"""Grok Paper Desk loop. Paper execution only."""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from dotenv import load_dotenv

from agent import Agent
from ledger import EXECUTION_MODE, Ledger, LedgerError
from market import Market

ROOT = Path(__file__).resolve().parent


def compute_performance(nav: float, starting_nav: float, spy_return_since_start: float) -> dict[str, float]:
    """Desk NAV return vs starting NAV, SPY (audit key: spx_return_since_start), and excess."""
    start = float(starting_nav)
    desk_ret = (float(nav) / start) - 1.0 if start > 0 else 0.0
    spy_ret = float(spy_return_since_start)
    return {
        "desk_return_since_start": desk_ret,
        "spx_return_since_start": spy_ret,  # SPY-based; name kept for audit continuity
        "excess_return": desk_ret - spy_ret,
    }


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    # Force paper regardless of file contents.
    cfg["execution_mode"] = "paper"
    if EXECUTION_MODE != "paper":
        raise RuntimeError("Live mode blocked.")
    return cfg


def in_market_hours(cfg: dict) -> bool:
    tz = ZoneInfo(cfg.get("timezone", "America/Los_Angeles"))
    now = datetime.now(tz)
    if now.weekday() >= 5:
        return False
    open_h, open_m = map(int, str(cfg["market_open"]).split(":"))
    close_h, close_m = map(int, str(cfg["market_close"]).split(":"))
    start = now.replace(hour=open_h, minute=open_m, second=0, microsecond=0)
    end = now.replace(hour=close_h, minute=close_m, second=0, microsecond=0)
    return start <= now <= end


def run_tick(cfg: dict, *, dry_run: bool = False) -> None:
    load_dotenv(ROOT / ".env")
    ledger = Ledger(
        db_path=ROOT / cfg.get("db_path", "data/desk.db"),
        audit_log_path=ROOT / cfg.get("audit_log_path", "logs/decisions.jsonl"),
        starting_cash=float(cfg.get("starting_cash", 100_000)),
    )
    market = Market(benchmark=str(cfg.get("benchmark", "SPY")))
    market.clear_cache()
    agent = Agent(cfg)

    state0 = ledger.get_state()
    held = list(state0.positions.keys())
    universe = [t.upper() for t in cfg.get("universe", [])]
    tickers = sorted(set(universe) | set(held) | {cfg.get("benchmark", "SPY").upper()})
    prices = market.get_prices(tickers)
    snap = ledger.snapshot(prices)
    spx_return = market.get_benchmark_return(state0.started_at or datetime.now(timezone.utc).date().isoformat())

    decision = agent.decide(snap, prices, spx_return, dry_run=dry_run)
    applied = False
    reject_code = decision.reason_code if decision.reason_code != "OK" else None
    price_used = None

    try:
        if decision.action in {"buy", "sell"} and decision.reason_code == "OK":
            if decision.ticker not in prices:
                raise LedgerError("UNKNOWN_TICKER", f"No market price for {decision.ticker}")
            price_used = prices[decision.ticker]
            if decision.action == "buy":
                ledger.buy(
                    decision.ticker,
                    decision.shares,
                    price_used,
                    nav=float(snap["nav"]),
                    min_cash_buffer=float(cfg.get("min_cash_buffer", 0.01)),
                    max_position_weight=float(cfg.get("max_position_weight", 0.60)),
                    reasoning=decision.reasoning,
                )
            else:
                ledger.sell(
                    decision.ticker,
                    decision.shares,
                    price_used,
                    reasoning=decision.reasoning,
                )
            applied = True
        elif decision.action == "hold":
            applied = True
            reject_code = decision.reason_code if decision.reason_code != "OK" else "HOLD"
    except LedgerError as err:
        applied = False
        reject_code = err.code
        ledger.record_reject(
            decision.action,
            decision.ticker or None,
            decision.shares,
            price_used,
            decision.reasoning,
            err.code,
        )

    prices2 = market.get_prices(tickers)
    snap2 = ledger.snapshot(prices2)
    perf = compute_performance(float(snap2["nav"]), ledger.starting_cash, spx_return)
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": decision.action,
        "ticker": decision.ticker or None,
        "shares": decision.shares,
        "price": price_used,
        "nav": snap2["nav"],
        "cash": snap2["cash"],
        "desk_return_since_start": perf["desk_return_since_start"],
        "spx_return_since_start": perf["spx_return_since_start"],  # SPY-based
        "excess_return": perf["excess_return"],
        "applied": applied and decision.action in {"buy", "sell"},
        "held": decision.action == "hold",
        "reason_code": reject_code or ("APPLIED" if applied else "UNKNOWN"),
        "reasoning": decision.reasoning,
        "execution_mode": "paper",
    }
    ledger.log_decision(payload)
    print(
        f"NAV ${snap2['nav']:,.2f} | cash ${snap2['cash']:,.2f} | "
        f"desk {perf['desk_return_since_start']:+.2%} | "
        f"SPY {perf['spx_return_since_start']:+.2%} | "
        f"excess {perf['excess_return']:+.2%} | "
        f"{decision.action} {decision.ticker} {decision.shares} | "
        f"{payload['reason_code']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Grok Paper Desk (paper only)")
    parser.add_argument("--loop", action="store_true", help="Run on a schedule during market hours")
    parser.add_argument("--dry-run", action="store_true", help="Stub hold; do not call xAI")
    parser.add_argument("--config", default=str(ROOT / "config.yaml"))
    args = parser.parse_args()
    cfg = load_config(Path(args.config))

    if not args.loop:
        run_tick(cfg, dry_run=args.dry_run)
        return

    tick_seconds = int(cfg.get("tick_minutes", 15)) * 60
    print("Paper desk loop started. Ctrl+C to stop.")
    while True:
        if in_market_hours(cfg):
            try:
                run_tick(cfg, dry_run=args.dry_run)
            except Exception as exc:
                print(f"Tick error: {type(exc).__name__}: {exc}")
        else:
            print("Outside market hours; sleeping.")
        time.sleep(tick_seconds)


if __name__ == "__main__":
    main()
