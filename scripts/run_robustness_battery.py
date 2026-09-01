"""Robustness battery for the as-of-safe TAS analysis: winsorize sensitivity,
subperiod stability, rolling-window coefficient path, and a placebo/lead
timing-integrity check. Reuses momentum_control's per-week FM machinery so
the estimator itself is identical to the audited main analysis."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from momentum_control import load_panel, fm_weekly_coefs, fm_aggregate, pooled_two_way_fe, HORIZONS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "results" / "tables"
FIGS = ROOT / "results" / "figures"
CTRL_M2 = ["past_4w_return", "past_12w_return"]

plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]
plt.rcParams["axes.unicode_minus"] = False


def winsorize_sensitivity(panel):
    rows = []
    for pct in [None, 0.01, 0.05]:
        p = panel.copy()
        if pct is not None:
            lo, hi = p["attention_z"].quantile(pct), p["attention_z"].quantile(1 - pct)
            p["attention_z"] = p["attention_z"].clip(lo, hi)
        for horizon in HORIZONS:
            coefs, _ = fm_weekly_coefs(p, horizon, [], use_industry_fe=False)
            agg = fm_aggregate(coefs, "Model1_attention_only", horizon)
            agg["winsorize_pct"] = "none" if pct is None else f"{pct:.0%}"
            rows.append(agg)
        m5 = pooled_two_way_fe(p, "future_4w_excess_return", CTRL_M2 + ["volume_ratio_4w", "volatility_12w", "liquidity_rank"])
        m5["winsorize_pct"] = "none" if pct is None else f"{pct:.0%}"
        rows.append(m5)
    return pd.DataFrame(rows)


def subperiod_stability(panel):
    weeks = sorted(panel["week"].unique())
    mid = weeks[len(weeks) // 2]
    rows = []
    for label, sub in [("first_half", panel[panel["week"] < mid]), ("second_half", panel[panel["week"] >= mid])]:
        for horizon in HORIZONS:
            coefs, _ = fm_weekly_coefs(sub, horizon, [], use_industry_fe=False)
            agg = fm_aggregate(coefs, "Model1_attention_only", horizon)
            agg["subperiod"] = label
            agg["week_start"] = str(sub["week"].min())
            agg["week_end"] = str(sub["week"].max())
            rows.append(agg)
    return pd.DataFrame(rows)


def rolling_window(panel, horizon="future_4w_excess_return", window_weeks=52):
    coefs, _ = fm_weekly_coefs(panel, horizon, [], use_industry_fe=False)
    coefs = coefs.sort_values("week").reset_index(drop=True)
    rows = []
    for i in range(window_weeks, len(coefs) + 1):
        win = coefs.iloc[i - window_weeks:i]
        c = win["coef"].dropna()
        if len(c) < 10:
            continue
        mean, std, n = c.mean(), c.std(), len(c)
        t = mean / (std / np.sqrt(n)) if std else np.nan
        rows.append({"window_end_week": win["week"].iloc[-1], "coef": mean, "t_stat": t})
    return pd.DataFrame(rows)


def placebo_lead_test(panel):
    """Attention at week t should NOT predict return realized before t.
    Test: attention_z(t) vs weekly_return(t-1) [already-realized return one week earlier].
    A significant relation here would indicate a timing leak."""
    p = panel.sort_values(["stock_id", "week"]).copy()
    p["past_1w_return_placebo_target"] = p.groupby("stock_id")["weekly_return"].shift(1)
    rows = []
    for _, grp in p.groupby("week"):
        sub = grp[["attention_z", "past_1w_return_placebo_target"]].dropna()
        if len(sub) < 10:
            continue
        ic = sub["attention_z"].corr(sub["past_1w_return_placebo_target"], method="spearman")
        if pd.notna(ic):
            rows.append(ic)
    s = pd.Series(rows, dtype=float)
    from scipy import stats
    t_stat, p_value = stats.ttest_1samp(s, 0) if len(s) > 1 else (np.nan, np.nan)
    return {
        "test": "placebo_lead (attention_z[t] vs already-realized return[t-1])",
        "IC_mean": s.mean(), "IC_std": s.std(), "t_stat": t_stat, "p_value": p_value,
        "n_weeks": len(s),
        "interpretation": "should be ~0/non-significant; significant result would indicate a timing leak in the as-of-safe pipeline",
    }


def main():
    panel = load_panel()

    print("=== 1. Winsorize sensitivity ===")
    wdf = winsorize_sensitivity(panel)
    wdf.to_csv(TABLES / "robustness_winsorize_sensitivity.csv", index=False, encoding="utf-8-sig")
    print(wdf[["model", "horizon", "winsorize_pct", "coefficient", "t_stat", "p_value"]].to_string())

    print("\n=== 2. Subperiod stability ===")
    sdf = subperiod_stability(panel)
    sdf.to_csv(TABLES / "robustness_subperiod_stability.csv", index=False, encoding="utf-8-sig")
    print(sdf[["model", "horizon", "subperiod", "coefficient", "t_stat", "p_value", "n_weeks"]].to_string())

    print("\n=== 3. Rolling 52-week window (4w horizon) ===")
    rdf = rolling_window(panel)
    rdf.to_csv(TABLES / "robustness_rolling_window_4w.csv", index=False, encoding="utf-8-sig")
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(pd.to_datetime(rdf["window_end_week"]), rdf["coef"], color="#2166ac", linewidth=1.5)
    ax.axhline(0, color="gray", linestyle="--", linewidth=1)
    ax2 = ax.twinx()
    ax2.plot(pd.to_datetime(rdf["window_end_week"]), rdf["t_stat"], color="#d73027", linewidth=1, alpha=0.6)
    ax2.axhline(1.96, color="#d73027", linestyle=":", linewidth=1)
    ax2.axhline(-1.96, color="#d73027", linestyle=":", linewidth=1)
    ax.set_xlabel("滾動窗口結束週")
    ax.set_ylabel("Attention係數（52週滾動）", color="#2166ac")
    ax2.set_ylabel("t統計量", color="#d73027")
    ax.set_title("TAS: Attention係數52週滾動穩定性（4週預測期間）")
    fig.tight_layout()
    fig.savefig(FIGS / "robustness_rolling_window_4w.png", dpi=300)
    fig.savefig(Path(r"C:\Users\user\Desktop\推甄資料最新版\06_圖表與視覺素材") / "tas_rolling_window_stability.png", dpi=300)
    plt.close(fig)
    print(f"n_windows={len(rdf)}, coef range=[{rdf['coef'].min():.5f}, {rdf['coef'].max():.5f}], "
          f"pct windows |t|>1.96: {(rdf['t_stat'].abs() > 1.96).mean():.1%}")

    print("\n=== 4. Placebo/lead timing-integrity test ===")
    placebo = placebo_lead_test(panel)
    pd.DataFrame([placebo]).to_csv(TABLES / "robustness_placebo_lead_test.csv", index=False, encoding="utf-8-sig")
    print(placebo)


if __name__ == "__main__":
    main()
