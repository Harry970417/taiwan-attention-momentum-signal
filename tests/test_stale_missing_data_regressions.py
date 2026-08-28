import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import attention_factor  # noqa: E402
import result_comparison  # noqa: E402
import trends_collector  # noqa: E402
from asof_contract import annotate_google_trends_weekly  # noqa: E402


class StaleMissingDataRegressionTests(unittest.TestCase):
    def test_attention_loader_rejects_stale_trends_manifest_entry(self):
        trend_index = pd.date_range("2021-01-03", periods=4, freq="W-SUN")
        annotated = annotate_google_trends_weekly(
            pd.DataFrame({"SVI": [10, 20, 30, 40]}, index=trend_index)
        )

        old_raw_dir = attention_factor.RAW_DIR
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            raw_dir = Path(tmp)
            attention_factor.RAW_DIR = raw_dir
            trend_path = raw_dir / "trends_2330.csv"
            annotated.to_csv(trend_path, index=False, encoding="utf-8-sig")

            manifest = trends_collector.new_manifest()
            manifest["stocks"]["2330"] = {
                "scale_factor": 1.0,
                "batch": "test",
                "timeframe": "today 5-y",
                "geo": trends_collector.GEO,
                "availability_policy": trends_collector.AVAILABILITY_POLICY,
                "request_config_sha256": trends_collector.request_config_sha256(),
                "file_sha256": trends_collector.file_sha256(trend_path),
                "error": "",
            }
            (raw_dir / "trends50_manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            try:
                with self.assertRaisesRegex(ValueError, "stale/incompatible"):
                    attention_factor.load_trends("2330")
            finally:
                attention_factor.RAW_DIR = old_raw_dir

    def test_trends_collector_main_fails_fast_when_pytrends_missing(self):
        old_trend_req = trends_collector.TrendReq
        old_import_error = trends_collector.PYTRENDS_IMPORT_ERROR
        trends_collector.TrendReq = None
        trends_collector.PYTRENDS_IMPORT_ERROR = ImportError("No module named pytrends")

        try:
            with self.assertRaisesRegex(RuntimeError, "pytrends is required"):
                trends_collector.main()
        finally:
            trends_collector.TrendReq = old_trend_req
            trends_collector.PYTRENDS_IMPORT_ERROR = old_import_error

    def test_result_comparison_flags_missing_corrected_key_and_metric(self):
        old_tables_dir = result_comparison.TABLES_DIR
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tables_dir = Path(tmp)
            result_comparison.TABLES_DIR = tables_dir
            pd.DataFrame([
                {"model": "m1", "horizon": 1, "coefficient": 0.1, "t_stat": 2.0},
                {"model": "m2", "horizon": 4, "coefficient": 0.2, "t_stat": 3.0},
            ]).to_csv(tables_dir / "legacy.csv", index=False)
            pd.DataFrame([
                {"model": "m1", "horizon": 1, "coefficient": 0.15},
            ]).to_csv(tables_dir / "corrected.csv", index=False)

            try:
                rows = result_comparison.compare_pair({
                    "name": "test_comparison",
                    "legacy": "legacy.csv",
                    "corrected": "corrected.csv",
                    "keys": ["model", "horizon"],
                    "metrics": ["coefficient", "t_stat"],
                })
            finally:
                result_comparison.TABLES_DIR = old_tables_dir

        statuses = {row["status"] for row in rows}
        self.assertIn("blocked_missing_corrected_metric", statuses)
        self.assertIn("blocked_missing_corrected_key", statuses)
        self.assertIn("compared", statuses)
        self.assertTrue(any(
            row["status"] == "blocked_missing_corrected_key"
            and row["model"] == "m2"
            and row["horizon"] == 4
            for row in rows
        ))


if __name__ == "__main__":
    unittest.main()
