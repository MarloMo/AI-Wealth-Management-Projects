
from __future__ import annotations

from agent import parse_and_validate


UNI = {"MU", "SPY"}
HELD = {"CRM"}


def _v(text: str):
    return parse_and_validate(
        text,
        universe=UNI,
        held=HELD,
        whole_shares_only=True,
        max_reasoning_chars=500,
    )


def test_malformed_json():
    d = _v("not json")
    assert d.action == "hold" and d.reason_code == "PARSE_FAIL"


def test_extra_keys_dropped_but_valid():
    d = _v('{"action":"hold","ticker":"","shares":0,"reasoning":"ok","evil":true}')
    assert d.action == "hold" and d.reason_code == "OK"


def test_lowercase_ticker_normalized_on_buy():
    d = _v('{"action":"buy","ticker":"mu","shares":1,"reasoning":"test"}')
    assert d.action == "buy" and d.ticker == "MU"


def test_fractional_shares_rejected():
    d = _v('{"action":"buy","ticker":"MU","shares":1.5,"reasoning":"test"}')
    assert d.action == "hold" and d.reason_code == "SCHEMA_FAIL"


def test_unknown_ticker():
    d = _v('{"action":"buy","ticker":"ZZZZZ","shares":1,"reasoning":"test"}')
    assert d.action == "hold" and d.reason_code == "UNKNOWN_TICKER"


def test_code_fences_rejected():
    d = _v('```json\n{"action":"hold","ticker":"","shares":0,"reasoning":"x"}\n```')
    assert d.action == "hold" and d.reason_code == "SCHEMA_FAIL"
