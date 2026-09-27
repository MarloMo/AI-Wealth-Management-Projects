from __future__ import annotations

from desk import compute_performance


def test_compute_performance_flat_vs_spy():
    perf = compute_performance(nav=100_000.0, starting_nav=100_000.0, spy_return_since_start=0.02)
    assert perf["desk_return_since_start"] == 0.0
    assert perf["spx_return_since_start"] == 0.02
    assert abs(perf["excess_return"] - (-0.02)) < 1e-12


def test_compute_performance_desk_beats_spy():
    # NAV 110k on 100k start = +10%; SPY +4% -> excess +6%
    perf = compute_performance(nav=110_000.0, starting_nav=100_000.0, spy_return_since_start=0.04)
    assert abs(perf["desk_return_since_start"] - 0.10) < 1e-12
    assert abs(perf["excess_return"] - 0.06) < 1e-12


def test_compute_performance_desk_lags_spy():
    perf = compute_performance(nav=98_000.0, starting_nav=100_000.0, spy_return_since_start=-0.01)
    assert abs(perf["desk_return_since_start"] - (-0.02)) < 1e-12
    assert abs(perf["excess_return"] - (-0.01)) < 1e-12


def test_compute_performance_zero_starting_nav():
    perf = compute_performance(nav=100_000.0, starting_nav=0.0, spy_return_since_start=0.05)
    assert perf["desk_return_since_start"] == 0.0
    assert perf["excess_return"] == -0.05
