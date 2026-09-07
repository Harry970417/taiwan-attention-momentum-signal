"""Backward (ex-dividend) price adjustment built from FinMind's free-tier
TaiwanStockDividendResult dataset.

FinMind's directly-adjusted price series (TaiwanStockPriceAdj) requires a paid tier
(verified 2026-09-07: the free tier returns HTTP 400 "Your level is free"). Its
TaiwanStockDividendResult dataset -- free-tier accessible -- reports the official
before_price/after_price reference prices TWSE itself computes for each ex-dividend
date, which already folds cash dividends, stock dividends, and rights offerings into a
single ratio. That ratio is exactly what a standard backward price adjustment needs; no
separate handling of cash vs. stock dividend components is required.

2026-09-07 Phase 1 A-G audit Finding A-1: raw close prices were being used directly for
`weekly_return`/`past_Nw_return`/`future_Nw_excess_return` (the Fama-MacBeth dependent
variable), producing a mechanical negative return on every ex-dividend date unrelated to
real economic performance.
"""
from __future__ import annotations

import pandas as pd


def build_adjusted_close(prices: pd.DataFrame, dividend_results: pd.DataFrame) -> pd.Series:
    """Return a backward-adjusted close series.

    `prices` must be indexed by date with a `close` column. `dividend_results` has
    `date` (ex-dividend trading date), `before_price`, `after_price` columns (the shape
    of FinMind's TaiwanStockDividendResult). Prices strictly before an ex-dividend date
    are scaled by after_price/before_price so the series is continuous across the event;
    prices on or after the event are left on the current (most recent) basis. Multiple
    events compound for the oldest prices, applied from most recent to oldest.
    """
    adjusted = prices["close"].astype(float).copy()
    if dividend_results.empty:
        return adjusted

    events = dividend_results.sort_values("date", ascending=False)
    for _, event in events.iterrows():
        before_price = float(event["before_price"])
        after_price = float(event["after_price"])
        if before_price <= 0 or after_price <= 0:
            continue
        factor = after_price / before_price
        ex_date = event["date"]
        mask = adjusted.index < ex_date
        adjusted.loc[mask] = adjusted.loc[mask] * factor
    return adjusted
