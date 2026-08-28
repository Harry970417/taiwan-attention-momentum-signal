"""TAS v0.3 Phase 6: double sort on past_4w_return x attention_z.

3x3 sort: loser/neutral/winner (by past_4w_return, computed within each
week's cross-section) x low/mid/high attention (by attention_z, also
within each week's cross-section). Reports mean future 1w/2w/4w excess
return in each of the 9 cells.
"""
from pathlib import Path

import pandas as pd

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt

from asof_contract import assert_no_lookahead_panel

ROOT = Path(__file__).resolve().parent.parent
PANEL_PATH = ROOT / "data" / "processed" / "attention_weekly_panel_v03_asof_safe.csv"
TABLES_DIR = ROOT / "results" / "tables"
FIGURES_DIR = ROOT / "results" / "figures"

MOM_LABELS = ["loser", "neutral", "winner"]
ATT_LABELS = ["low_attention", "mid_attention", "high_attention"]


def load_panel():
    df = pd.read_csv(PANEL_PATH, parse_dates=["week"])
    df["stock_id"] = df["stock_id"].astype(str)
    assert_no_lookahead_panel(df)
    return df


def weekly_tercile(panel: pd.DataFrame, col: str, labels: list[str]):
    def _bucket(s):
        try:
            return pd.qcut(s, 3, labels=labels, duplicates="drop")
        except ValueError:
            return pd.Series([None] * len(s), index=s.index)
    return panel.groupby("week")[col].transform(_bucket)


def main():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    panel = load_panel()

    panel["mom_bucket"] = weekly_tercile(panel, "past_4w_return", MOM_LABELS)
    panel["att_bucket"] = weekly_tercile(panel, "attention_z", ATT_LABELS)

    sub = panel.dropna(subset=["mom_bucket", "att_bucket"])
    horizons = ["future_1w_excess_return", "future_2w_excess_return", "future_4w_excess_return"]
    table = sub.groupby(["mom_bucket", "att_bucket"], observed=True)[horizons].agg(["mean", "count"])
    table.to_csv(TABLES_DIR / "v03_double_sort_past4w_attention_asof_safe.csv", encoding="utf-8-sig")
    print(table.to_string())

    for horizon, fname in [("future_1w_excess_return", "v03_double_sort_heatmap_1w_asof_safe.png"),
                            ("future_4w_excess_return", "v03_double_sort_heatmap_4w_asof_safe.png")]:
        pivot = sub.groupby(["mom_bucket", "att_bucket"], observed=True)[horizon].mean().unstack()
        pivot = pivot.reindex(index=MOM_LABELS, columns=ATT_LABELS)
        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto")
        ax.set_xticks(range(len(ATT_LABELS)))
        ax.set_xticklabels(ATT_LABELS)
        ax.set_yticks(range(len(MOM_LABELS)))
        ax.set_yticklabels(MOM_LABELS)
        for i in range(len(MOM_LABELS)):
            for j in range(len(ATT_LABELS)):
                v = pivot.values[i, j]
                ax.text(j, i, f"{v*100:.2f}%", ha="center", va="center", fontsize=10)
        ax.set_title(f"Double sort: mean {horizon}")
        fig.colorbar(im, ax=ax)
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / fname, dpi=150)
        plt.close(fig)

    # Answer the four diagnostic questions
    p1w = sub.groupby(["mom_bucket", "att_bucket"], observed=True)["future_1w_excess_return"].mean().unstack()
    print("\n--- Diagnostic answers (based on future_1w_excess_return) ---")
    print(f"1) Winner row, high vs low attention: {p1w.loc['winner','high_attention']:.4f} vs {p1w.loc['winner','low_attention']:.4f}")
    print(f"2) Neutral row, high vs low attention: {p1w.loc['neutral','high_attention']:.4f} vs {p1w.loc['neutral','low_attention']:.4f}")
    print(f"3) Loser row, high vs low attention: {p1w.loc['loser','high_attention']:.4f} vs {p1w.loc['loser','low_attention']:.4f}")


if __name__ == "__main__":
    main()
