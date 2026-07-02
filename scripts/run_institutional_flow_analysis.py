"""Stage 4: integrate institutional flow data and test whether it explains
the attention-momentum effect (regression with chip controls + triple sort).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import institutional_flow
import regression_analysis
import triple_sort

if __name__ == "__main__":
    print("=== Step 1/3: build institutional-flow-augmented panel ===")
    institutional_flow.main()
    print("\n=== Step 2/3: regression with institutional flow controls + interactions ===")
    regression_analysis.main()
    print("\n=== Step 3/3: triple sort (momentum x attention x institutional flow) ===")
    triple_sort.main()
