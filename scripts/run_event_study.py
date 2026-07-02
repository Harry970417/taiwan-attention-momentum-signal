"""Stage 2: build the attention factor panel and run the CAAR event study."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import attention_factor
import event_study
import visualization

if __name__ == "__main__":
    print("=== Step 1/3: build attention factor + control-variable panel ===")
    attention_factor.main()
    print("\n=== Step 2/3: CAAR event study ===")
    event_study.main()
    print("\n=== Step 3/3: SVI trend / price-overlay figures ===")
    visualization.main()
