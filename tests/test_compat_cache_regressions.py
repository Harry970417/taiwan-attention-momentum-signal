import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import stock_data_loader  # noqa: E402
import trends_collector  # noqa: E402


class CompatibilityCacheRegressionTests(unittest.TestCase):
    def test_institutional_fetch_writes_net_file_after_groupby_aggregation(self):
        payload = {
            "status": 200,
            "data": [
                {"date": "2022-01-03", "buy": 100, "sell": 40},
                {"date": "2022-01-03", "buy": 15, "sell": 30},
                {"date": "2022-01-04", "buy": 8, "sell": 3},
            ],
        }
        old_raw_dir = stock_data_loader.RAW_DIR
        old_fetch_dataset = stock_data_loader.fetch_dataset

        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            stock_data_loader.RAW_DIR = Path(tmp)
            stock_data_loader.fetch_dataset = lambda dataset, stock_id: payload
            try:
                ok, err = stock_data_loader.fetch_institutional("2330")
            finally:
                stock_data_loader.RAW_DIR = old_raw_dir
                stock_data_loader.fetch_dataset = old_fetch_dataset

            self.assertTrue(ok, err)
            self.assertEqual(err, "")
            self.assertTrue((Path(tmp) / "inst_breakdown_2330.csv").exists())

            net = pd.read_csv(Path(tmp) / "inst_2330.csv")

        self.assertEqual(net.columns.tolist(), ["date", "stock_id", "institutional_net_shares"])
        self.assertEqual(net["stock_id"].astype(str).unique().tolist(), ["2330"])
        by_date = dict(zip(net["date"], net["institutional_net_shares"]))
        self.assertEqual(by_date["2022-01-03"], 45)
        self.assertEqual(by_date["2022-01-04"], 5)

    def test_legacy_date_svi_trend_cache_is_reused_with_date_index(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            path = Path(tmp) / "trends_2330.csv"
            path.write_text("date,SVI\n2022-01-02,10\n2022-01-09,20\n", encoding="utf-8")

            cached = trends_collector.read_cached_trend(path)

        self.assertEqual(cached.index.tolist(), [pd.Timestamp("2022-01-02"), pd.Timestamp("2022-01-09")])
        self.assertEqual(cached["SVI"].tolist(), [10, 20])
        self.assertEqual(cached.iloc[0]["observation_period_start"].date().isoformat(), "2022-01-02")
        self.assertEqual(cached.iloc[0]["available_at"].date().isoformat(), "2022-01-16")


if __name__ == "__main__":
    unittest.main()
