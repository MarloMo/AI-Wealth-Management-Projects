
"""Grok decision agent. Validates JSON strictly. Does not execute trades."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

import httpx

TICKER_RE = re.compile(r"^[A-Z]{1,5}$")
ALLOWED_ACTIONS = {"buy", "sell", "hold"}


@dataclass
class Decision:
    action: str
    ticker: str
    shares: float
    reasoning: str
    reason_code: str = "OK"
    raw: str | None = None


def _force_hold(code: str, reasoning: str, raw: str | None = None) -> Decision:
    return Decision(action="hold", ticker="", shares=0.0, reasoning=reasoning[:500], reason_code=code, raw=raw)


def parse_and_validate(
    text: str,
    *,
    universe: set[str],
    held: set[str],
    whole_shares_only: bool,
    max_reasoning_chars: int,
) -> Decision:
    raw = text.strip()
    if raw.startswith("```"):
        # Reject fenced output; force hold after retry at caller.
        return _force_hold("SCHEMA_FAIL", "Model returned code fences.", raw=raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return _force_hold("PARSE_FAIL", "Malformed JSON.", raw=raw)
    if not isinstance(data, dict):
        return _force_hold("SCHEMA_FAIL", "JSON root must be an object.", raw=raw)

    allowed_keys = {"action", "ticker", "shares", "reasoning"}
    # Drop unknown keys; do not execute them.
    data = {k: data[k] for k in allowed_keys if k in data}

    action = str(data.get("action", "")).lower().strip()
    if action not in ALLOWED_ACTIONS:
        return _force_hold("SCHEMA_FAIL", f"Invalid action: {action}", raw=raw)

    ticker = str(data.get("ticker", "") or "").upper().strip()
    shares_raw = data.get("shares", 0)
    reasoning = str(data.get("reasoning", "") or "")[:max_reasoning_chars]

    try:
        shares = float(shares_raw)
    except (TypeError, ValueError):
        return _force_hold("SCHEMA_FAIL", "Shares must be numeric.", raw=raw)

    if action == "hold":
        return Decision(action="hold", ticker="", shares=0.0, reasoning=reasoning or "Hold.", reason_code="OK", raw=raw)

    if not TICKER_RE.match(ticker):
        return _force_hold("SCHEMA_FAIL", f"Invalid ticker format: {ticker}", raw=raw)
    if ticker not in universe and ticker not in held:
        return _force_hold("UNKNOWN_TICKER", f"Ticker not allowed: {ticker}", raw=raw)
    if shares <= 0:
        return _force_hold("SCHEMA_FAIL", "Buy/sell requires shares > 0.", raw=raw)
    if whole_shares_only and abs(shares - round(shares)) > 1e-9:
        return _force_hold("SCHEMA_FAIL", "Fractional shares disabled.", raw=raw)
    shares = float(int(round(shares))) if whole_shares_only else shares

    return Decision(action=action, ticker=ticker, shares=shares, reasoning=reasoning, reason_code="OK", raw=raw)


def build_prompt(state: dict[str, Any], prices: dict[str, float], spx_return: float) -> str:
    # Constructed only from our structured state — never concat prior model text.
    positions = [
        {"ticker": p["ticker"], "shares": p["shares"], "avg_cost": p["avg_cost"], "price": p["price"]}
        for p in state.get("positions", [])
    ]
    return f"""You are the portfolio manager of a $100,000 paper account.
Beat the S&P 500. You may hold cash.

Current state:
- cash: {state.get("cash")}
- positions: {json.dumps(positions)}
- prices: {json.dumps(prices)}
- portfolio_value: {state.get("nav")}
- sp500_return_since_start: {spx_return}

Rules:
- Long-only. No shorts. No options. No leverage.
- Do not spend more cash than you have.
- Do not sell more shares than you hold.
- Doing nothing is a valid answer.

Return ONLY JSON. No prose before or after. No code fences.

{{
  "action": "buy" | "sell" | "hold",
  "ticker": "MU",
  "shares": 0,
  "reasoning": "one to three sentences"
}}
"""


class Agent:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.model = config.get("model", "grok-4")
        self.base_url = config.get("xai_base_url", "https://api.x.ai/v1").rstrip("/")
        self.timeout = float(config.get("xai_timeout_seconds", 45))
        self.max_reasoning_chars = int(config.get("max_reasoning_chars", 500))
        self.whole_shares_only = bool(config.get("whole_shares_only", True))
        self.universe = {t.upper() for t in config.get("universe", [])}

    def decide(self, state: dict[str, Any], prices: dict[str, float], spx_return: float, *, dry_run: bool = False) -> Decision:
        held = {p["ticker"].upper() for p in state.get("positions", [])}
        prompt = build_prompt(state, prices, spx_return)
        # Assert key never enters prompt
        key = os.getenv("XAI_API_KEY", "")
        if key and key in prompt:
            raise RuntimeError("API key leaked into prompt construction.")

        if dry_run or self.config.get("dry_run"):
            stub = json.dumps({"action": "hold", "ticker": "", "shares": 0, "reasoning": "Dry-run stub hold."})
            return parse_and_validate(
                stub,
                universe=self.universe,
                held=held,
                whole_shares_only=self.whole_shares_only,
                max_reasoning_chars=self.max_reasoning_chars,
            )

        if not key:
            return _force_hold("SCHEMA_FAIL", "XAI_API_KEY missing; forcing hold.")

        text = self._call_xai(prompt)
        decision = parse_and_validate(
            text,
            universe=self.universe,
            held=held,
            whole_shares_only=self.whole_shares_only,
            max_reasoning_chars=self.max_reasoning_chars,
        )
        if decision.reason_code in {"PARSE_FAIL", "SCHEMA_FAIL"}:
            # One retry on parse/schema failure
            text2 = self._call_xai(prompt + "\n\nYour previous reply was invalid. Return ONLY the JSON object.")
            decision = parse_and_validate(
                text2,
                universe=self.universe,
                held=held,
                whole_shares_only=self.whole_shares_only,
                max_reasoning_chars=self.max_reasoning_chars,
            )
            if decision.reason_code in {"PARSE_FAIL", "SCHEMA_FAIL"}:
                return _force_hold(decision.reason_code, decision.reasoning, raw=decision.raw)
        return decision

    def _call_xai(self, prompt: str) -> str:
        key = os.getenv("XAI_API_KEY", "")
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You output only valid JSON for paper portfolio decisions."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/chat/completions", headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
            content = data["choices"][0]["message"]["content"]
            # Do not log full request bodies.
            return str(content)
        except Exception as exc:  # timeout / network → hold at caller via schema
            return json.dumps(
                {
                    "action": "hold",
                    "ticker": "",
                    "shares": 0,
                    "reasoning": f"xAI call failed: {type(exc).__name__}. Holding.",
                }
            )
