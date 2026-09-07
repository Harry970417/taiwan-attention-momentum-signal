import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from price_adjustment import build_adjusted_close  # noqa: E402


class PriceAdjustmentTests(unittest.TestCase):
    """2026-09-07 Phase 1 A-G audit Finding A-1: raw (unadjusted) close prices produce a
    mechanical, non-economic price drop on every ex-dividend date, polluting weekly_return,
    past_Nw_return, and future_Nw_excess_return (the Fama-MacBeth regression's own dependent
    variable). FinMind's adjusted-price dataset (TaiwanStockPriceAdj) requires a paid tier;
    TaiwanStockDividendResult (free tier) gives before_price/after_price at each ex-dividend
    date, from which a standard backward price adjustment can be built directly."""

    def test_no_dividend_events_leaves_prices_unchanged(self):
        prices = pd.DataFrame(
            {"close": [100.0, 101.0, 102.0]},
            index=pd.to_datetime(["2022-01-03", "2022-01-04", "2022-01-05"]),
        )
        dividends = pd.DataFrame(columns=["date", "before_price", "after_price"])

        adjusted = build_adjusted_close(prices, dividends)

        pd.testing.assert_series_equal(adjusted, prices["close"], check_names=False)

    def test_single_ex_dividend_event_scales_prior_prices_only(self):
        # Ex-div on 2022-07-14: before_price=23.45, after_price=22.20 (matches the real
        # 2891 event used as evidence in the audit). factor = 22.20/23.45.
        prices = pd.DataFrame(
            {"close": [23.45, 22.20, 23.00]},
            index=pd.to_datetime(["2022-07-13", "2022-07-14", "2022-07-15"]),
        )
        dividends = pd.DataFrame(
            {"date": pd.to_datetime(["2022-07-14"]), "before_price": [23.45], "after_price": [22.20]}
        )

        adjusted = build_adjusted_close(prices, dividends)

        factor = 22.20 / 23.45
        self.assertAlmostEqual(adjusted.loc["2022-07-13"], 23.45 * factor)
        # On and after the ex-dividend date, prices are already on the current basis.
        self.assertEqual(adjusted.loc["2022-07-14"], 22.20)
        self.assertEqual(adjusted.loc["2022-07-15"], 23.00)

    def test_multiple_events_compound_for_the_oldest_prices(self):
        prices = pd.DataFrame(
            {"close": [100.0, 100.0, 100.0]},
            index=pd.to_datetime(["2021-01-01", "2022-08-01", "2023-08-01"]),
        )
        dividends = pd.DataFrame(
            {
                "date": pd.to_datetime(["2022-06-01", "2023-06-01"]),
                "before_price": [110.0, 105.0],
                "after_price": [100.0, 95.0],
            }
        )

        adjusted = build_adjusted_close(prices, dividends)

        f1 = 100.0 / 110.0  # 2022-06-01 event
        f2 = 95.0 / 105.0  # 2023-06-01 event
        # 2021-01-01 predates both events -> scaled by both, compounded.
        self.assertAlmostEqual(adjusted.loc["2021-01-01"], 100.0 * f1 * f2)
        # 2022-08-01 postdates the 2022-06-01 event but predates the 2023-06-01 event.
        self.assertAlmostEqual(adjusted.loc["2022-08-01"], 100.0 * f2)
        # 2023-08-01 postdates both events -> unchanged.
        self.assertEqual(adjusted.loc["2023-08-01"], 100.0)

    def test_missing_before_price_event_is_skipped_not_fatal(self):
        prices = pd.DataFrame(
            {"close": [100.0, 100.0]}, index=pd.to_datetime(["2022-01-01", "2022-06-02"])
        )
        dividends = pd.DataFrame(
            {"date": pd.to_datetime(["2022-06-01"]), "before_price": [0.0], "after_price": [95.0]}
        )

        adjusted = build_adjusted_close(prices, dividends)

        # A zero/missing before_price can't yield a usable ratio -- must not divide by
        # zero or corrupt the series; the event is skipped and prices stay as-is.
        pd.testing.assert_series_equal(adjusted, prices["close"], check_names=False)


if __name__ == "__main__":
    unittest.main()
