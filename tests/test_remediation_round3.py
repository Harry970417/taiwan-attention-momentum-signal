import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import attention_factor  # noqa: E402
import event_study  # noqa: E402
import result_comparison  # noqa: E402
import trends_collector  # noqa: E402
from asof_contract import annotate_google_trends_weekly  # noqa: E402


def _daily_price_frame() -> pd.DataFrame:
    dates = pd.bdate_range("2020-12-01", "2021-12-31")
    close = np.linspace(100.0, 180.0, len(dates))
    out = pd.DataFrame({
        "close": close,
        "Trading_Volume": 1_000_000.0,
        "Trading_money": close * 1_000_000.0,
    }, index=dates)
    out["ret"] = out["close"].pct_change()
    out["vol_ma20"] = 1_000_000.0
    out["vol_ma60"] = 1_000_000.0
    out["turnover_ma20"] = out["Trading_money"].rolling(20, min_periods=1).mean()
    out["volatility_20"] = 0.01
    out["volatility_60"] = 0.01
    out["beta_26w"] = 1.0
    out["max_drawdown_12w"] = 0.0
    return out


def _write_valid_trends_manifest(raw_dir: Path, stock_id: str, trend_path: Path) -> None:
    manifest = trends_collector.new_manifest()
    manifest["stocks"][stock_id] = {
        "scale_factor": 1.0,
        "batch": "test",
        "timeframe": trends_collector.TIMEFRAME,
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


class RemediationRound3Tests(unittest.TestCase):
    def test_annotated_trends_file_builds_panel_without_double_annotation_collision(self):
        trend_index = pd.date_range("2021-01-03", periods=40, freq="W-SUN")
        annotated = annotate_google_trends_weekly(
            pd.DataFrame({"SVI": np.arange(10, 50, dtype=float)}, index=trend_index)
        )
        price = _daily_price_frame()
        taiex = _daily_price_frame()

        old_raw_dir = attention_factor.RAW_DIR
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            attention_factor.RAW_DIR = Path(tmp)
            trend_path = Path(tmp) / "trends_2330.csv"
            annotated.to_csv(trend_path, index=False, encoding="utf-8-sig")
            _write_valid_trends_manifest(Path(tmp), "2330", trend_path)
            try:
                loaded = attention_factor.load_trends("2330")
                self.assertNotEqual(loaded.index.name, "observation_period_start")
                panel = attention_factor.build_for_stock("2330", "TSMC", "Semiconductor", price, taiex, loaded)
            finally:
                attention_factor.RAW_DIR = old_raw_dir

        self.assertFalse(panel.empty)
        self.assertIn("attention_z", panel.columns)

    def test_collection_status_table_is_not_legacy_evidence(self):
        status_path = ROOT / "results" / "tables" / "google_trends_test_result_50.csv"

        self.assertIn("results/tables/google_trends_test_result_50.csv", result_comparison.NON_EVIDENCE_ARTIFACTS)
        self.assertFalse(result_comparison.is_legacy_evidence_candidate(status_path))

    def test_pre_event_windows_are_contiguous_and_non_overlapping(self):
        trading_days = pd.bdate_range("2021-11-01", "2022-02-15")
        bounds = {
            offset: event_study.event_window_bounds(trading_days, "2022-01-10", offset)
            for offset in range(-event_study.WINDOW_PRE, 1)
        }

        for offset in range(-event_study.WINDOW_PRE, 0):
            self.assertEqual(bounds[offset][1], bounds[offset + 1][0])
            self.assertLessEqual(bounds[offset][1], bounds[offset + 1][0])


if __name__ == "__main__":
    unittest.main()
