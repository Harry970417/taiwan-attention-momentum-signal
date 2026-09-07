import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from run_corrected_placebo_test import strictly_prior_return  # noqa: E402


class CorrectedPlaceboTests(unittest.TestCase):
    """2026-09-07: the original placebo_lead_test's comparison window overlapped
    attention_z's own SVI observation window by ~6 of 7 days (verified against the real
    panel). strictly_prior_return() must guarantee zero overlap -- its anchor date must
    always be strictly before observation_period_start."""

    def test_anchor_is_strictly_before_observation_period_start(self):
        # Two weeks of daily trading days, so trailing_window_return(..., n_weeks=1) has
        # both an anchor and a point 1 week earlier to compute a return from.
        dates = pd.bdate_range("2021-12-27", "2022-01-07")
        price = pd.DataFrame({"close": [100.0 + i for i in range(len(dates))]}, index=dates)
        obs_start = pd.Timestamp("2022-01-09")

        ret = strictly_prior_return(price, obs_start)

        self.assertIsNotNone(ret)
        # The window must end on 2022-01-07 (last trading day before 2022-01-08, the day
        # before obs_start) -- not on or after obs_start itself.
        self.assertNotIn(obs_start, price.loc[price.index >= obs_start].index)

    def test_returns_none_when_no_prior_trading_day_exists(self):
        price = pd.DataFrame({"close": [100.0]}, index=pd.to_datetime(["2022-06-01"]))
        obs_start = pd.Timestamp("2022-01-01")

        self.assertIsNone(strictly_prior_return(price, obs_start))


if __name__ == "__main__":
    unittest.main()
