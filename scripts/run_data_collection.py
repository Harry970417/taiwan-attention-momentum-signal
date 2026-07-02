"""Stage 1: collect Google Trends + FinMind data for the 50-stock universe.

Google Trends rate-limits aggressively; this script retries with backoff
and caches completed stocks, so it is safe to re-run if it stops partway.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import trends_collector
import stock_data_loader

if __name__ == "__main__":
    print("=== Step 1/2: Google Trends (weekly SVI, anchor-batched) ===")
    trends_collector.main()
    print("\n=== Step 2/2: FinMind prices + institutional flow ===")
    stock_data_loader.main()
