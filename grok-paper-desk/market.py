
"""Market data via yfinance. No broker. Tick-scoped quote cache."""

from __future__ import annotations

from typing import Iterable

import yfinance as yf


class Market:
    def __init__(self, benchmark: str = "SPY"):
        self.benchmark = benchmark.upper()
        self._tick_cache: dict[str, float] = {}

    def clear_cache(self) -> None:
        self._tick_cache.clear()

    def get_price(self, ticker: str) -> float:
        t = ticker.upper()
        if t in self._tick_cache:
            return self._tick_cache[t]
        px = self._fetch_price(t)
        if px is None or px <= 0:
            raise RuntimeError(f"No price available for {t}")
        self._tick_cache[t] = px
        return px

    def _fetch_price(self, t: str) -> float | None:
        # Try ticker.history first, then download() as a fallback.
        try:
            hist = yf.Ticker(t).history(period="5d")
            if hist is not None and not hist.empty:
                return float(hist["Close"].iloc[-1])
        except Exception:
            pass
        try:
            df = yf.download(t, period="5d", progress=False, auto_adjust=True)
            if df is not None and not df.empty:
                col = "Close" if "Close" in df.columns else df.columns[0]
                series = df[col]
                if hasattr(series, "iloc"):
                    val = series.iloc[-1]
                    # download may return MultiIndex columns
                    try:
                        return float(val)
                    except TypeError:
                        return float(val.squeeze())
        except Exception:
            pass
        return None

    def get_prices(self, tickers: Iterable[str]) -> dict[str, float]:
        out: dict[str, float] = {}
        errors: list[str] = []
        for t in tickers:
            try:
                out[t.upper()] = self.get_price(t)
            except Exception as exc:
                errors.append(f"{t.upper()}: {exc}")
        if not out:
            raise RuntimeError("No prices available: " + "; ".join(errors))
        # Keep going if some optional names fail; caller uses what is present.
        if errors:
            print("Price warnings: " + "; ".join(errors))
        return out

    def get_benchmark_return(self, start_date: str) -> float:
        """Approximate total return of benchmark since start_date (ISO or YYYY-MM-DD)."""
        start = start_date[:10]
        try:
            hist = yf.Ticker(self.benchmark).history(start=start)
        except Exception:
            return 0.0
        if hist is None or hist.empty or len(hist) < 2:
            return 0.0
        first = float(hist["Close"].iloc[0])
        last = float(hist["Close"].iloc[-1])
        if first <= 0:
            return 0.0
        return (last / first) - 1.0
