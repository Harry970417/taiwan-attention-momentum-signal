"""Corrected placebo/lead test for the 2026-09-07 Phase 1 A-G audit's C-4 follow-up.

The original robustness_battery.placebo_lead_test() compares attention_z(t) against
weekly_return(t-1) (the panel's *previous row's* trailing 1-week return). But
weekly_return is computed relative to feature_asof_trade_date, which is anchored to the
14-day conservative availability delay -- NOT to observation_period_start directly. Row
t-1's weekly_return window ends only ~1 day before row t's SVI observation window
*starts*, so the two windows overlap by ~6 of 7 days in real calendar time. A
significant correlation there reflects contemporaneous price/attention comovement
within the same calendar week, not a forward-looking leak, because the two quantities
are not actually chronologically separated despite the "shift(1)" row-index offset.

This script builds a genuinely non-overlapping comparison: a trailing 1-week return
ending on the last trading day strictly before observation_period_start(t) (i.e. before
any day attention_z(t)'s own SVI window covers), and re-runs the same placebo
methodology against it.
"""
import sys
from pathlib import Path

import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from asof_contract import last_before, trailing_window_return  # noqa: E402
from attention_factor import RAW_DIR, load_price  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PANEL_PATH = ROOT / "data" / "processed" / "attention_weekly_panel_v03_asof_safe.csv"
OUT_PATH = ROOT / "results" / "tables" / "robustness_corrected_placebo_lead_test.csv"


def strictly_prior_return(price: pd.DataFrame, observation_period_start) -> float | None:
    """Trailing 1-week return ending on the last trading day strictly before
    observation_period_start -- guaranteed zero calendar overlap with the SVI window
    that produces attention_z for that same row."""
    cutoff = pd.Timestamp(observation_period_start) - pd.Timedelta(days=1)
    anchor = last_before(price.index, cutoff)
    if anchor is None:
        return None
    return trailing_window_return(price["close"], anchor, 1)


def main() -> None:
    panel = pd.read_csv(PANEL_PATH, parse_dates=["observation_period_start"])
    taiex = pd.read_csv(RAW_DIR / "price_TAIEX.csv", parse_dates=["date"]).sort_values("date").set_index("date")
    taiex["ret"] = taiex["close"].pct_change()

    prior_returns: dict[tuple[int, pd.Timestamp], float | None] = {}
    price_cache: dict[int, pd.DataFrame] = {}
    for stock_id in panel["stock_id"].unique():
        price = load_price(str(stock_id), taiex["ret"])
        if price is None:
            continue
        price_cache[stock_id] = price

    rows = []
    for stock_id, grp in panel.groupby("stock_id"):
        price = price_cache.get(stock_id)
        if price is None:
            continue
        for _, r in grp.iterrows():
            ret = strictly_prior_return(price, r["observation_period_start"])
            rows.append({"stock_id": stock_id, "week": r["week"], "attention_z": r["attention_z"], "strictly_prior_1w_return": ret})

    df = pd.DataFrame(rows).dropna(subset=["attention_z", "strictly_prior_1w_return"])
    ics = []
    for _, grp in df.groupby("week"):
        if len(grp) < 10:
            continue
        ic = grp["attention_z"].corr(grp["strictly_prior_1w_return"], method="spearman")
        if pd.notna(ic):
            ics.append(ic)
    s = pd.Series(ics, dtype=float)
    t_stat, p_value = stats.ttest_1samp(s, 0) if len(s) > 1 else (float("nan"), float("nan"))
    result = {
        "test": "corrected_placebo (attention_z[t] vs return strictly before observation_period_start[t])",
        "IC_mean": s.mean(), "IC_std": s.std(), "t_stat": t_stat, "p_value": p_value,
        "n_weeks": len(s),
        "interpretation": "should be ~0/non-significant; unlike the original placebo_lead_test, this comparison window has zero calendar overlap with attention_z's own SVI observation window",
    }
    pd.DataFrame([result]).to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(result)


if __name__ == "__main__":
    main()
