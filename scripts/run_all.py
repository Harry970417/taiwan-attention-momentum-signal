"""Run the full TAS pipeline end to end: data collection -> attention
factor + CAAR -> momentum control -> institutional flow control.

Expect 30-60+ minutes for a full run, mostly spent on Google Trends
rate-limit backoff during data collection. Safe to re-run: completed
stocks are cached and skipped.
"""
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
STAGES = [
    "run_data_collection.py",
    "run_event_study.py",
    "run_momentum_control.py",
    "run_institutional_flow_analysis.py",
]

if __name__ == "__main__":
    for stage in STAGES:
        print(f"\n{'='*60}\nRunning {stage}\n{'='*60}")
        result = subprocess.run([sys.executable, str(SCRIPTS_DIR / stage)])
        if result.returncode != 0:
            print(f"\n{stage} failed with exit code {result.returncode}; stopping.")
            sys.exit(result.returncode)
    print("\nAll stages completed.")
