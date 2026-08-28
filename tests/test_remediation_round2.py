import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import attention_factor  # noqa: E402
import event_study  # noqa: E402
import result_comparison  # noqa: E402
import trends_collector  # noqa: E402


class RemediationRound2Tests(unittest.TestCase):
    def test_event_window_offset_plus_one_starts_at_first_tradeable(self):
        dates = pd.bdate_range("2021-12-01", "2022-03-15")
        stock_close = pd.Series(range(100, 100 + len(dates)), index=dates, dtype=float)
        market_close = pd.Series(range(200, 200 + len(dates)), index=dates, dtype=float)
        events = pd.DataFrame([{
            "stock_id": "2330",
            "stock_name": "TSMC",
            "week": pd.Timestamp("2022-01-09"),
            "return_start": pd.Timestamp("2022-01-10"),
            "first_tradeable_at": pd.Timestamp("2022-01-10"),
        }])
        stale_panel = pd.DataFrame([{
            "stock_id": "2330",
            "week": pd.Timestamp("2022-01-16"),
            "weekly_excess_return": 999.0,
        }])

        out = event_study.compute_event_window(
            stale_panel,
            events,
            {"2330": stock_close},
            market_close,
        )
        plus_one = out.loc[out["offset"] == 1].iloc[0]

        self.assertGreaterEqual(pd.Timestamp(plus_one["return_start"]), pd.Timestamp("2022-01-10"))
        self.assertEqual(pd.Timestamp(plus_one["return_start"]).date().isoformat(), "2022-01-10")
        self.assertEqual(pd.Timestamp(plus_one["return_end"]).date().isoformat(), "2022-01-17")
        expected_ar = (
            stock_close.loc["2022-01-17"] / stock_close.loc["2022-01-10"] - 1
            - (market_close.loc["2022-01-17"] / market_close.loc["2022-01-10"] - 1)
        )
        self.assertAlmostEqual(plus_one["AR"], expected_ar)
        self.assertNotEqual(plus_one["AR"], 999.0)

    def test_partial_universe_coverage_gate_refuses_survivor_subset(self):
        rows = [
            {"stock_id": "2330", "status": "accepted"},
            {"stock_id": "2454", "status": "blocked_missing_raw_input"},
        ]
        with self.assertRaisesRegex(RuntimeError, "partial survivor universe"):
            attention_factor.assert_complete_universe_coverage(rows, expected_n=2)

    def test_trends_timeframe_is_fixed_and_cache_requires_matching_policy_and_checksum(self):
        self.assertNotIn("today", trends_collector.TIMEFRAME)
        self.assertRegex(trends_collector.TIMEFRAME, r"^\d{4}-\d{2}-\d{2} \d{4}-\d{2}-\d{2}$")

        stale = trends_collector.new_manifest()
        stale["request_config"] = {**trends_collector.request_config(), "timeframe": "today 5-y"}
        stale["request_config_sha256"] = "stale"
        self.assertFalse(trends_collector.manifest_matches_request(stale))

        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            path = Path(tmp) / "trends_2330.csv"
            path.write_text("date,SVI\n2022-01-02,10\n", encoding="utf-8")
            manifest = trends_collector.new_manifest()
            manifest["stocks"]["2330"] = {
                "scale_factor": 1.0,
                "timeframe": trends_collector.TIMEFRAME,
                "availability_policy": trends_collector.AVAILABILITY_POLICY,
                "request_config_sha256": trends_collector.request_config_sha256(),
                "file_sha256": trends_collector.file_sha256(path),
            }
            self.assertTrue(trends_collector.cache_entry_is_valid(manifest, "2330", path))
            path.write_text("date,SVI\n2022-01-02,11\n", encoding="utf-8")
            self.assertFalse(trends_collector.cache_entry_is_valid(manifest, "2330", path))

    def test_legacy_inventory_covers_present_tables_and_figures(self):
        present = result_comparison.discover_present_legacy_artifacts()
        inventoried = {spec["legacy"] for spec in result_comparison.LEGACY_EVIDENCE}

        self.assertFalse(present - inventoried)
        self.assertIn("results/tables/ic_summary.csv", inventoried)
        self.assertIn("results/tables/v03_matched_event_summary.csv", inventoried)
        self.assertIn("results/tables/v04_strategy_group_comparison.csv", inventoried)

        rows = result_comparison.legacy_provenance_rows()
        by_artifact = {row["legacy_artifact"]: row for row in rows}
        self.assertEqual(by_artifact["results/tables/ic_summary.csv"]["corrected_status"], "not_regenerated")
        self.assertEqual(by_artifact["results/tables/v03_matched_event_summary.csv"]["corrected_status"], "not_regenerated")
        self.assertTrue(by_artifact["results/tables/ic_summary.csv"]["legacy_sha256"])


if __name__ == "__main__":
    unittest.main()
