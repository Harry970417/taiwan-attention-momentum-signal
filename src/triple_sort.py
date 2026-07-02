"""TAS v0.4 Phase 5: triple sort on past_4w_return x attention_z x
total_inst_net_buy_ratio_4w (all terciles computed within each week's
cross-section).
"""
from pathlib import Path

import pandas as pd

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
PANEL_PATH = ROOT / "data" / "processed" / "attention_weekly_panel_v04.csv"
TABLES_DIR = ROOT / "results" / "tables"
FIGURES_DIR = ROOT / "results" / "figures"

MOM_LABELS = ["loser", "neutral", "winner"]
ATT_LABELS = ["low_attention", "mid_attention", "high_attention"]
CHIP_LABELS = ["inst_selling", "inst_neutral", "inst_buying"]


def load_panel():
    df = pd.read_csv(PANEL_PATH, parse_dates=["week"])
    df["stock_id"] = df["stock_id"].astype(str)
    return df


def weekly_tercile(panel, col, labels):
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
    panel["chip_bucket"] = weekly_tercile(panel, "total_inst_net_buy_ratio_4w", CHIP_LABELS)

    sub = panel.dropna(subset=["mom_bucket", "att_bucket", "chip_bucket"])
    horizons = ["future_1w_excess_return", "future_2w_excess_return", "future_4w_excess_return"]
    table = sub.groupby(["mom_bucket", "att_bucket", "chip_bucket"], observed=True)[horizons].agg(["mean", "count"])
    table.to_csv(TABLES_DIR / "v04_triple_sort_momentum_attention_chips.csv", encoding="utf-8-sig")
    print(table.to_string())

    p4w = sub.groupby(["mom_bucket", "att_bucket", "chip_bucket"], observed=True)["future_4w_excess_return"].mean()

    for mom_label, fname in [("winner", "v04_triple_sort_winner_group_heatmap.png"),
                              ("neutral", "v04_triple_sort_neutral_group_heatmap.png")]:
        pivot = p4w.loc[mom_label].unstack()
        pivot = pivot.reindex(index=ATT_LABELS, columns=CHIP_LABELS)
        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto")
        ax.set_xticks(range(len(CHIP_LABELS)))
        ax.set_xticklabels(CHIP_LABELS)
        ax.set_yticks(range(len(ATT_LABELS)))
        ax.set_yticklabels(ATT_LABELS)
        for i in range(len(ATT_LABELS)):
            for j in range(len(CHIP_LABELS)):
                v = pivot.values[i, j]
                ax.text(j, i, f"{v*100:.2f}%", ha="center", va="center", fontsize=10)
        ax.set_title(f"{mom_label} group: mean future_4w_excess_return")
        fig.colorbar(im, ax=ax)
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / fname, dpi=150)
        plt.close(fig)

    print("\n--- Diagnostic answers (future_4w_excess_return) ---")
    print(f"1) winner+high_attention+inst_buying: {p4w.get(('winner','high_attention','inst_buying'), None)}")
    print(f"   vs winner+high_attention+inst_selling: {p4w.get(('winner','high_attention','inst_selling'), None)}")
    print(f"2) winner+high_attention+inst_selling (still positive?): {p4w.get(('winner','high_attention','inst_selling'), None)}")
    print(f"3) high_attention with inst_selling across all mom buckets:")
    for m in MOM_LABELS:
        print(f"   {m}+high_attention+inst_selling: {p4w.get((m,'high_attention','inst_selling'), None)}")
    print(f"4) Compare winner+low_attention+inst_buying vs winner+high_attention+inst_selling:")
    print(f"   {p4w.get(('winner','low_attention','inst_buying'), None)} vs {p4w.get(('winner','high_attention','inst_selling'), None)}")


if __name__ == "__main__":
    main()
