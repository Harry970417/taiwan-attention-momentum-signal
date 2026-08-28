"""Stage 4: integrate as-of-safe institutional flow controls and triple sort.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import institutional_flow
import regression_analysis
import result_comparison
import triple_sort

if __name__ == "__main__":
    print("=== Step 1/4: build institutional-flow-augmented panel ===")
    institutional_flow.main()
    print("\n=== Step 2/4: regression with institutional flow controls + interactions ===")
    regression_analysis.main()
    print("\n=== Step 3/4: triple sort (momentum x attention x institutional flow) ===")
    triple_sort.main()
    print("\n=== Step 4/4: legacy vs as-of-safe result comparison ===")
    result_comparison.main()
