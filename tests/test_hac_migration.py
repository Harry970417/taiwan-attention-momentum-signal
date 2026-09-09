"""2026-09-09: migrate momentum_control.fm_aggregate, regression_analysis.fm_aggregate,
and momentum_control.factor_ic_summary off their naive (non-HAC) significance tests
onto quant_formulas (Desktop/quant-system-core), per the Phase 1 A-G audit's C-2/P1-19
finding that this repo had zero Newey-West/HAC implementation anywhere despite
1/2/4-week overlapping forward-return windows inducing serial correlation."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from momentum_control import fm_aggregate as momentum_control_fm_aggregate  # noqa: E402
from momentum_control import factor_ic_summary  # noqa: E402
from regression_analysis import fm_aggregate as regression_analysis_fm_aggregate  # noqa: E402
from quant_formulas.factor_stats import newey_west_se, t_stat_and_pvalue  # noqa: E402


def _autocorrelated_coef_series(n=60, seed=0):
    # AR(1)-style series: positive serial correlation, exactly the pattern
    # overlapping forward-return windows induce. Naive std/sqrt(n) understates
    # the true standard error of the mean for a series like this.
    rng = np.random.RandomState(seed)
    values = [0.0]
    for _ in range(n - 1):
        values.append(0.7 * values[-1] + rng.normal(0, 0.01))
    return pd.Series(values) + 0.01  # nonzero mean


class MomentumControlFmAggregateHacTests(unittest.TestCase):
    def test_matches_quant_formulas_newey_west_exactly(self):
        coef_values = _autocorrelated_coef_series()
        coefs = pd.DataFrame({"week": range(len(coef_values)), "coef": coef_values, "n_obs": 50, "r2": 0.1})

        result = momentum_control_fm_aggregate(coefs, "TestModel", "future_1w_excess_return")

        expected_se = newey_west_se(coef_values)
        expected_t, expected_p = t_stat_and_pvalue(coef_values.mean(), expected_se, df=len(coef_values) - 1)
        self.assertAlmostEqual(result["t_stat"], expected_t, places=8)
        self.assertAlmostEqual(result["p_value"], expected_p, places=8)

    def test_no_longer_matches_the_deprecated_naive_formula(self):
        coef_values = _autocorrelated_coef_series()
        coefs = pd.DataFrame({"week": range(len(coef_values)), "coef": coef_values, "n_obs": 50, "r2": 0.1})

        result = momentum_control_fm_aggregate(coefs, "TestModel", "future_1w_excess_return")

        naive_t = coef_values.mean() / (coef_values.std() / np.sqrt(len(coef_values)))
        self.assertNotAlmostEqual(result["t_stat"], naive_t, places=4)
        # Positive serial correlation -> HAC SE > naive SE -> |HAC t| < |naive t|.
        self.assertLess(abs(result["t_stat"]), abs(naive_t))

    def test_empty_coefs_still_handled_safely(self):
        result = momentum_control_fm_aggregate(pd.DataFrame(), "TestModel", "future_1w_excess_return")
        self.assertIsNone(result["t_stat"])
        self.assertEqual(result["n_weeks"], 0)


class RegressionAnalysisFmAggregateHacTests(unittest.TestCase):
    def test_matches_quant_formulas_newey_west_exactly(self):
        coef_values = _autocorrelated_coef_series(seed=1)
        coefs = pd.DataFrame({"attention_z": coef_values})

        result = regression_analysis_fm_aggregate(coefs, "attention_z")

        expected_se = newey_west_se(coef_values)
        expected_t, expected_p = t_stat_and_pvalue(coef_values.mean(), expected_se, df=len(coef_values) - 1)
        self.assertAlmostEqual(result["t_stat"], expected_t, places=8)
        self.assertAlmostEqual(result["p_value"], expected_p, places=8)


class FactorIcSummaryHacTests(unittest.TestCase):
    def test_ic_significance_no_longer_uses_plain_ttest_1samp(self):
        rng = np.random.RandomState(2)
        weeks = pd.date_range("2022-01-02", periods=40, freq="W")
        rows = []
        # Construct an autocorrelated attention_z / forward-return relationship
        # across weeks so the per-week IC series itself is serially correlated.
        drift = 0.0
        for week in weeks:
            drift = 0.6 * drift + rng.normal(0, 0.3)
            for stock in range(15):
                az = rng.normal(0, 1) + drift
                fwd = 0.01 * az + rng.normal(0, 0.02)
                rows.append({
                    "week": week,
                    "residual_attention_z": az,
                    "future_1w_excess_return": fwd,
                    "future_2w_excess_return": fwd,
                    "future_4w_excess_return": fwd,
                })
        panel = pd.DataFrame(rows)

        result = factor_ic_summary(panel, "residual_attention_z")
        row = result[result["horizon"] == "future_1w_excess_return"].iloc[0]

        from scipy import stats as scipy_stats

        ics = []
        for _, grp in panel.groupby("week"):
            ic = grp["residual_attention_z"].corr(grp["future_1w_excess_return"], method="spearman")
            if pd.notna(ic):
                ics.append(ic)
        ic_series = pd.Series(ics, dtype=float)
        naive_t, _ = scipy_stats.ttest_1samp(ic_series, 0)

        self.assertNotAlmostEqual(row["t_stat"], naive_t, places=4)
        # Column contract preserved for the existing CSV consumer.
        self.assertIn("ICIR", result.columns)
        self.assertIn("positive_IC_ratio", result.columns)


if __name__ == "__main__":
    unittest.main()
