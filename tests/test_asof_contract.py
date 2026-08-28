import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from asof_contract import (  # noqa: E402
    add_trailing_attention_features,
    annotate_google_trends_weekly,
    assert_google_trends_weekly_index,
    assert_no_lookahead_panel,
    first_at_or_after,
    forward_window,
)


class AsOfContractTests(unittest.TestCase):
    def test_weekly_contract_cross_year(self):
        raw = pd.DataFrame({"SVI": [10, 20]}, index=pd.to_datetime(["2021-12-26", "2022-01-02"]))
        out = annotate_google_trends_weekly(raw)

        self.assertEqual(out.iloc[0]["observation_period_start"].date().isoformat(), "2021-12-26")
        self.assertEqual(out.iloc[0]["observation_period_end"].date().isoformat(), "2022-01-01")
        self.assertEqual(out.iloc[0]["available_at"].date().isoformat(), "2022-01-09")
        self.assertEqual(out.iloc[1]["observation_period_end"].date().isoformat(), "2022-01-08")
        self.assertEqual(out.iloc[1]["signal_date"].date().isoformat(), "2022-01-16")

    def test_annotating_already_annotated_trends_is_idempotent(self):
        raw = pd.DataFrame({"SVI": [10, 20]}, index=pd.to_datetime(["2021-12-26", "2022-01-02"]))
        once = annotate_google_trends_weekly(raw)
        twice = annotate_google_trends_weekly(once)

        pd.testing.assert_frame_equal(twice, once)

    def test_google_trends_week_boundary_must_be_sunday(self):
        with self.assertRaises(AssertionError):
            assert_google_trends_weekly_index(pd.to_datetime(["2022-01-03"]))

    def test_holiday_first_tradeable_after_signal(self):
        trading_days = pd.to_datetime(["2022-01-07", "2022-01-11", "2022-01-12"])
        self.assertEqual(first_at_or_after(trading_days, "2022-01-09").date().isoformat(), "2022-01-11")

    def test_forward_window_missing_horizon_data_returns_none(self):
        price = pd.Series([100, 101], index=pd.to_datetime(["2022-01-11", "2022-01-12"]))
        end, ret = forward_window(price, "2022-01-11", 1)
        self.assertIsNone(end)
        self.assertIsNone(ret)

    def test_no_lookahead_assertion_catches_same_week_trade(self):
        bad = pd.DataFrame([{
            "stock_id": "2330",
            "week": "2022-01-09",
            "observation_period_start": "2022-01-02",
            "observation_period_end": "2022-01-08",
            "available_at": "2022-01-16",
            "signal_date": "2022-01-16",
            "first_tradeable_at": "2022-01-10",
            "feature_asof_trade_date": "2022-01-07",
            "return_start": "2022-01-10",
            "z_window_end": "2022-01-08",
            "return_end_1w": "2022-01-17",
        }])
        with self.assertRaises(AssertionError):
            assert_no_lookahead_panel(bad)

    def test_no_lookahead_assertion_accepts_cross_month_and_year_panel(self):
        good = pd.DataFrame([{
            "stock_id": "2330",
            "week": "2022-01-16",
            "observation_period_start": "2022-01-02",
            "observation_period_end": "2022-01-08",
            "available_at": "2022-01-16",
            "signal_date": "2022-01-16",
            "first_tradeable_at": "2022-01-17",
            "feature_asof_trade_date": "2022-01-14",
            "return_start": "2022-01-17",
            "z_window_end": "2022-01-08",
            "return_end_1w": "2022-01-24",
        }, {
            "stock_id": "2330",
            "week": "2023-01-08",
            "observation_period_start": "2022-12-25",
            "observation_period_end": "2022-12-31",
            "available_at": "2023-01-08",
            "signal_date": "2023-01-08",
            "first_tradeable_at": "2023-01-09",
            "feature_asof_trade_date": "2023-01-06",
            "return_start": "2023-01-09",
            "z_window_end": "2022-12-31",
            "return_end_1w": "2023-01-16",
        }])
        assert_no_lookahead_panel(good)

    def test_trailing_zscore_is_unchanged_by_future_values(self):
        idx = pd.date_range("2021-01-03", periods=70, freq="W-SUN")
        base = pd.DataFrame({"SVI": range(70)}, index=idx)
        changed = base.copy()
        changed.iloc[60:, 0] = 1000

        z_base = add_trailing_attention_features(base).loc[idx[40], "attention_z"]
        z_changed = add_trailing_attention_features(changed).loc[idx[40], "attention_z"]
        self.assertAlmostEqual(z_base, z_changed)


if __name__ == "__main__":
    unittest.main()
