"""Event study (CAAR) for attention-shock events, 50-stock TAS v0.2 panel.

Event definitions:
  z2          : attention_z > 2 (own-history z-score shock)
  ratio       : attention_shock > 1 (search volume >100% above own 52w MA)
  top_decile  : attention_z above the 90th percentile of the whole panel

For each definition: drop overlapping events for the same stock within a
4-week window (keep the first), flag calendar clustering (how many other
stocks also have an event that same week), then compute per-event AR/CAR
over the [-4, +8] week window using AR = weekly_return - market_weekly_return
(both already in the weekly panel), and average across events to get CAAR.

Significance: ordinary one-sample t-test on the final-window CAR across
events, plus a bootstrap (2000 resamples, resampling events with
replacement) 95% CI on mean CAR. Note: because events cluster in calendar
time (many stocks can spike in the same week), events are not independent
draws -- the ordinary t-test likely overstates significance. This is
flagged explicitly rather than silently trusting the t-test; a
clustering-robust or calendar-time-portfolio approach would be the correct
next step if these results are to be used for anything beyond screening.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
PANEL_PATH = ROOT / "data" / "processed" / "attention_weekly_panel_50.csv"
TABLES_DIR = ROOT / "results" / "tables"
FIGURES_DIR = ROOT / "results" / "figures"

NON_OVERLAP_WEEKS = 4
WINDOW_PRE, WINDOW_POST = 4, 8
N_BOOTSTRAP = 2000
RNG_SEED = 42


def load_panel():
    df = pd.read_csv(PANEL_PATH, parse_dates=["week"])
    df["stock_id"] = df["stock_id"].astype(str)
    return df


def get_event_flags(panel: pd.DataFrame):
    top_decile_threshold = panel["attention_z"].quantile(0.90)
    return {
        "attention_z2": panel["is_attention_event_z2"].fillna(False),
        "attention_ratio": panel["is_attention_event_ratio"].fillna(False),
        "attention_top_decile": panel["attention_z"] > top_decile_threshold,
    }, top_decile_threshold


def non_overlap_filter(events: pd.DataFrame) -> pd.DataFrame:
    """Keep only the first event per stock within any NON_OVERLAP_WEEKS window."""
    kept = []
    for sid, grp in events.groupby("stock_id"):
        grp = grp.sort_values("week")
        last_kept_week = None
        for _, row in grp.iterrows():
            if last_kept_week is None or (row["week"] - last_kept_week).days >= NON_OVERLAP_WEEKS * 7:
                kept.append(row)
                last_kept_week = row["week"]
    return pd.DataFrame(kept) if kept else events.iloc[0:0]


def flag_calendar_clustering(events: pd.DataFrame) -> pd.DataFrame:
    counts = events.groupby("week")["stock_id"].transform("count")
    events = events.copy()
    events["n_events_same_week"] = counts
    return events


def compute_event_window(panel: pd.DataFrame, events: pd.DataFrame):
    """Return long-format DataFrame: event_id, stock_id, event_week, offset, AR."""
    lookup = panel.set_index(["stock_id", "week"])[["weekly_return", "market_weekly_return"]]
    rows = []
    for eid, ev in enumerate(events.itertuples()):
        for offset in range(-WINDOW_PRE, WINDOW_POST + 1):
            target_week = ev.week + pd.Timedelta(weeks=offset)
            key = (ev.stock_id, target_week)
            if key in lookup.index:
                r = lookup.loc[key]
                wr, mr = r["weekly_return"], r["market_weekly_return"]
                if pd.notna(wr) and pd.notna(mr):
                    rows.append({"event_id": eid, "stock_id": ev.stock_id, "event_week": ev.week,
                                 "offset": offset, "AR": wr - mr})
    return pd.DataFrame(rows)


def summarize_caar(event_window: pd.DataFrame):
    """Per-offset AAR/CAAR across events, plus per-event final CAR for significance tests."""
    if event_window.empty:
        return pd.DataFrame(), pd.DataFrame()

    offsets = sorted(event_window["offset"].unique())
    per_event = event_window.pivot_table(index="event_id", columns="offset", values="AR")
    per_event = per_event.reindex(columns=offsets)
    car = per_event.cumsum(axis=1)

    rows = []
    for o in offsets:
        ar_vals = per_event[o].dropna()
        car_vals = car[o].dropna()
        t_ar = stats.ttest_1samp(ar_vals, 0) if len(ar_vals) > 1 else (np.nan, np.nan)
        rows.append({
            "offset": o, "AAR": ar_vals.mean() if len(ar_vals) else None,
            "CAAR": car_vals.mean() if len(car_vals) else None,
            "n_events": len(car_vals),
            "AAR_t_stat": t_ar[0], "AAR_p_value": t_ar[1],
        })
    by_window = pd.DataFrame(rows)

    final_car = car[offsets[-1]].dropna()
    return by_window, final_car


def bootstrap_ci(values: pd.Series, n_boot=N_BOOTSTRAP, seed=RNG_SEED):
    if len(values) < 2:
        return None, None
    rng = np.random.default_rng(seed)
    arr = values.to_numpy()
    boots = rng.choice(arr, size=(n_boot, len(arr)), replace=True).mean(axis=1)
    return np.percentile(boots, 2.5), np.percentile(boots, 97.5)


def plot_caar(by_window: pd.DataFrame, title: str, out_path: Path):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(by_window["offset"], by_window["CAAR"], marker="o", color="tab:blue")
    ax.axhline(0, color="grey", linewidth=0.8)
    ax.axvline(0, color="red", linestyle="--", linewidth=0.8, label="Event week (0)")
    ax.set_xlabel("Weeks relative to event")
    ax.set_ylabel("CAAR (cumulative average abnormal return)")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    panel = load_panel()
    flags, top_decile_threshold = get_event_flags(panel)
    print(f"Top-decile attention_z threshold (panel-wide 90th pct): {top_decile_threshold:.3f}")

    summary_rows = []
    fig_map = {
        "attention_z2": "caar_attention_z2.png",
        "attention_ratio": "caar_attention_ratio.png",
        "attention_top_decile": "caar_attention_top_decile.png",
    }
    all_by_window = []

    for name, flag in flags.items():
        raw_events = panel.loc[flag, ["stock_id", "stock_name", "week"]].copy()
        n_raw = len(raw_events)
        filtered = non_overlap_filter(raw_events)
        filtered = flag_calendar_clustering(filtered)
        n_events = len(filtered)
        n_stocks = filtered["stock_id"].nunique()
        max_cluster = filtered["n_events_same_week"].max() if n_events else 0

        event_window = compute_event_window(panel, filtered)
        by_window, final_car = summarize_caar(event_window)
        by_window.insert(0, "event_definition", name)
        all_by_window.append(by_window)

        if len(final_car) > 1:
            t_stat, p_value = stats.ttest_1samp(final_car, 0)
            ci_low, ci_high = bootstrap_ci(final_car)
        else:
            t_stat = p_value = ci_low = ci_high = None

        summary_rows.append({
            "event_definition": name,
            "n_events_raw": n_raw,
            "n_events_after_nonoverlap_filter": n_events,
            "n_unique_stocks": n_stocks,
            "max_events_same_calendar_week": max_cluster,
            "final_window_offset": WINDOW_POST,
            "CAR_mean_at_final_window": final_car.mean() if len(final_car) else None,
            "CAR_std": final_car.std() if len(final_car) else None,
            "t_stat": t_stat, "p_value": p_value,
            "bootstrap_ci_low": ci_low, "bootstrap_ci_high": ci_high,
            "n_events_used_in_test": len(final_car),
        })

        if not by_window.empty and name in fig_map:
            direction = "動能(momentum)" if (final_car.mean() or 0) > 0 else "反轉(reversal)" if (final_car.mean() or 0) < 0 else "無明顯方向"
            plot_caar(by_window, f"CAAR - {name} (n={n_events} events, {direction})", FIGURES_DIR / fig_map[name])
            print(f"{name}: {n_raw} raw -> {n_events} after filter, {n_stocks} stocks, "
                  f"CAR@+{WINDOW_POST}w mean={final_car.mean():.4f} t={t_stat:.3f} p={p_value:.4f}" if len(final_car) > 1 else f"{name}: insufficient events for test")

    pd.DataFrame(summary_rows).to_csv(TABLES_DIR / "caar_event_summary.csv", index=False, encoding="utf-8-sig")
    if all_by_window:
        pd.concat(all_by_window, ignore_index=True).to_csv(TABLES_DIR / "caar_by_event_window.csv", index=False, encoding="utf-8-sig")
    print(f"\nSaved caar_event_summary.csv and caar_by_event_window.csv to {TABLES_DIR}")


if __name__ == "__main__":
    main()
