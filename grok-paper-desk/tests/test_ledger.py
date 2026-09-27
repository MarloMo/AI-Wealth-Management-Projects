
from __future__ import annotations

from pathlib import Path

import pytest

from ledger import Ledger, LedgerError


@pytest.fixture()
def ledger(tmp_path: Path) -> Ledger:
    return Ledger(
        db_path=tmp_path / "t.db",
        audit_log_path=tmp_path / "a.jsonl",
        starting_cash=100_000,
    )


def test_buy_and_sell(ledger: Ledger):
    ledger.buy("MU", 10, 100.0, nav=100_000, min_cash_buffer=0.01, max_position_weight=0.6)
    st = ledger.get_state()
    assert st.positions["MU"].shares == 10
    ledger.sell("MU", 4, 110.0)
    st = ledger.get_state()
    assert st.positions["MU"].shares == 6


def test_insufficient_cash(ledger: Ledger):
    with pytest.raises(LedgerError) as ei:
        ledger.buy("MU", 2000, 100.0, nav=100_000, min_cash_buffer=0.01, max_position_weight=0.95)
    assert ei.value.code == "INSUFFICIENT_CASH"


def test_insufficient_shares(ledger: Ledger):
    ledger.buy("MU", 5, 10.0, nav=100_000, min_cash_buffer=0.0, max_position_weight=0.9)
    with pytest.raises(LedgerError) as ei:
        ledger.sell("MU", 6, 10.0)
    assert ei.value.code == "INSUFFICIENT_SHARES"


def test_weight_cap(ledger: Ledger):
    # 70k of 100k nav = 0.70 > 0.60
    with pytest.raises(LedgerError) as ei:
        ledger.buy("MU", 700, 100.0, nav=100_000, min_cash_buffer=0.0, max_position_weight=0.60)
    assert ei.value.code == "WEIGHT_CAP"


def test_negative_cash_rejected_via_buffer(ledger: Ledger):
    with pytest.raises(LedgerError):
        ledger.buy("MU", 1000, 100.0, nav=100_000, min_cash_buffer=0.05, max_position_weight=0.99)
