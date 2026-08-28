"""Stage 3: as-of-safe momentum-controlled Fama-MacBeth regression and double sort.

Requires attention_weekly_panel_v03_asof_safe.csv from run_event_study.py (the panel
build step also constructs the momentum/volume/volatility control
variables used here).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import momentum_control
import double_sort

if __name__ == "__main__":
    print("=== Step 1/2: Fama-MacBeth regressions with momentum controls ===")
    momentum_control.main()
    print("\n=== Step 2/2: double sort (past return x attention_z) ===")
    double_sort.main()
