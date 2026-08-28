"""As-of-safe event study (CAAR) for attention-shock events.

Event definitions:
  z2          : attention_z > 2 (own-history z-score shock)
  ratio       : attention_shock > 1 (search volume >100% above own 52w MA)
  top_decile  : attention_z above that signal week's cross-sectional 90th percentile

For each definition: drop overlapping events for the same stock within a
4-week window (keep the first), flag calendar clustering (how many other
stocks also have an event that same week), then compute per-event AR/CAR
over the [-4, +8] week window from raw daily close prices with explicit
return_start and return_end dates per offset. Post-signal CAR starts from
offset +1 so the delayed pre-signal week is not treated as forward evidence.

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

from asof_contract import (
    assert_no_lookahead_panel,
    first_at_or_after,
    last_at_or_before,
    last_before,
    normalize_date,
    window_return,
)

ROOT = Path(__file__).resolve().parent.parent
PANEL_PATH = ROOT / "data" / "processed" / "attention_weekly_panel_v03_asof_safe.csv"
RAW_DIR = ROOT / "data" / "raw"
TABLES_DIR = ROOT / "results" / "tables"
FIGURES_DIR = ROOT / "results" / "figures"

NON_OVERLAP_WEEKS = 4
WINDOW_PRE, WINDOW_POST = 4, 8
N_BOOTSTRAP = 2000
RNG_SEED = 42


def load_panel():
    df = pd.read_csv(PANEL_PATH)
    df["stock_id"] = df["stock_id"].astype(str)
    for col in ["week", "signal_date", "return_start", "first_tradeable_at", "feature_asof_trade_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    assert_no_lookahead_panel(df)
    return df


def get_event_flags(panel: pd.DataFrame):
    top_decile_threshold = panel.groupby("week")["attention_z"].transform(lambda s: s.quantile(0.90))
    return {
        "attention_z2": panel["is_attention_event_z2"].fillna(False),
        "attention_ratio": panel["is_attention_event_ratio"].fillna(False),
        "attention_top_decile": panel["attention_z"] > top_decile_threshold,
    }, "weekly cross-sectional 90th percentile"


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


def load_price_series(path: Path, label: str) -> pd.Series:
    """Load an exact daily close series for executable event-window returns."""
    if not path.exists():
        raise FileNotFoundError(
            f"Missing real raw daily price data for {label}: {path}. "
            "Event-study ARs require executable close-to-close returns; do not reuse panel trailing returns."
        )
    raw = pd.read_csv(path, parse_dates=["date"])
    missing = {"date", "close"} - set(raw.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
    if raw.empty:
        raise ValueError(f"{path} contains no daily price rows.")

    series = raw.sort_values("date").set_index("date")["close"].astype(float)
    series.index = pd.DatetimeIndex(pd.to_datetime(series.index)).tz_localize(None).normalize()
    return series[~series.index.duplicated(keep="last")]


def load_event_price_data(stock_ids) -> tuple[dict[str, pd.Series], pd.Series]:
    market_price = load_price_series(RAW_DIR / "price_TAIEX.csv", "TAIEX benchmark")
    stock_prices = {}
    for sid in sorted({str(s) for s in stock_ids}):
        stock_prices[sid] = load_price_series(RAW_DIR / f"price_{sid}.csv", f"stock {sid}")
    return stock_prices, market_price


def _common_trading_days(stock_price: pd.Series, market_price: pd.Series) -> pd.DatetimeIndex:
    common = pd.DatetimeIndex(stock_price.index).intersection(pd.DatetimeIndex(market_price.index))
    return common.sort_values()


def event_window_bounds(trading_days: pd.DatetimeIndex, return_start, offset: int):
    """Map an event offset to executable close-to-close start/end dates."""
    anchor = normalize_date(return_start)
    if offset >= 1:
        start = first_at_or_after(trading_days, anchor + pd.Timedelta(weeks=offset - 1))
        end = first_at_or_after(trading_days, anchor + pd.Timedelta(weeks=offset))
    else:
        end = last_before(trading_days, anchor)
        for _ in range(abs(offset)):
            if end is None:
                break
            end = last_at_or_before(trading_days, end - pd.Timedelta(weeks=1))
        start = last_at_or_before(trading_days, end - pd.Timedelta(weeks=1)) if end is not None else None

    if start is None or end is None or end <= start:
        return None, None
    if offset >= 1 and start < anchor:
        raise AssertionError(
            f"Post-signal offset {offset} starts before first tradeable date: "
            f"{start.date()} < {anchor.date()}"
        )
    return start, end


def compute_event_window(
    panel: pd.DataFrame,
    events: pd.DataFrame,
    stock_prices: dict[str, pd.Series] | None = None,
    market_price: pd.Series | None = None,
):
    """Return long-format event-window ARs computed from raw daily prices."""
    del panel  # The panel supplies signal rows only; ARs must come from raw daily prices.
    if events.empty:
        return pd.DataFrame(columns=[
            "event_id", "stock_id", "event_week", "offset", "return_start", "return_end",
            "first_tradeable_at", "stock_return", "market_return", "AR",
        ])

    required = {"stock_id", "week", "return_start", "first_tradeable_at"}
    missing = required - set(events.columns)
    if missing:
        raise ValueError(f"Events are missing required as-of columns: {sorted(missing)}")

    events = events.copy()
    events["stock_id"] = events["stock_id"].astype(str)
    if stock_prices is None or market_price is None:
        stock_prices, market_price = load_event_price_data(events["stock_id"].unique())

    rows = []
    for eid, ev in enumerate(events.itertuples()):
        stock_price = stock_prices.get(ev.stock_id)
        if stock_price is None:
            raise FileNotFoundError(f"Missing loaded price series for event stock {ev.stock_id}")
        trading_days = _common_trading_days(stock_price, market_price)
        for offset in range(-WINDOW_PRE, WINDOW_POST + 1):
            start, end = event_window_bounds(trading_days, ev.return_start, offset)
            if start is None or end is None:
                continue
            stock_ret = window_return(stock_price, start, end)
            market_ret = window_return(market_price, start, end)
            if stock_ret is None or market_ret is None:
                continue
            rows.append({
                "event_id": eid,
                "stock_id": ev.stock_id,
                "event_week": ev.week,
                "offset": offset,
                "return_start": start.date(),
                "return_end": end.date(),
                "first_tradeable_at": normalize_date(ev.first_tradeable_at).date(),
                "stock_return": stock_ret,
                "market_return": market_ret,
                "AR": stock_ret - market_ret,
            })
    return pd.DataFrame(rows)


def summarize_caar(event_window: pd.DataFrame):
    """Per-offset AAR/CAAR across events, plus per-event final CAR for significance tests."""
    if event_window.empty:
        return pd.DataFrame(), pd.DataFrame()

    offsets = sorted(event_window["offset"].unique())
    per_event = event_window.pivot_table(index="event_id", columns="offset", values="AR")
    per_event = per_event.reindex(columns=offsets)
    car = per_event.cumsum(axis=1)
    post_offsets = [o for o in offsets if o >= 1]
    post_car = per_event[post_offsets].cumsum(axis=1) if post_offsets else pd.DataFrame(index=per_event.index)

    rows = []
    for o in offsets:
        ar_vals = per_event[o].dropna()
        car_vals = car[o].dropna()
        t_ar = stats.ttest_1samp(ar_vals, 0) if len(ar_vals) > 1 else (np.nan, np.nan)
        rows.append({
            "offset": o, "AAR": ar_vals.mean() if len(ar_vals) else None,
            "CAAR": car_vals.mean() if len(car_vals) else None,
            "CAAR_from_signal": post_car[o].dropna().mean() if o in post_car.columns else None,
            "n_events": len(car_vals),
            "AAR_t_stat": t_ar[0], "AAR_p_value": t_ar[1],
        })
    by_window = pd.DataFrame(rows)

    final_car = post_car[post_offsets[-1]].dropna() if post_offsets else pd.Series(dtype=float)
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
    y_col = "CAAR_from_signal" if by_window["CAAR_from_signal"].notna().any() else "CAAR"
    ax.plot(by_window["offset"], by_window[y_col], marker="o", color="tab:blue")
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
    stock_prices, market_price = load_event_price_data(panel["stock_id"].unique())
    flags, top_decile_threshold = get_event_flags(panel)
    print(f"Top-decile attention_z threshold: {top_decile_threshold}")

    summary_rows = []
    fig_map = {
        "attention_z2": "caar_attention_z2_asof_safe.png",
        "attention_ratio": "caar_attention_ratio_asof_safe.png",
        "attention_top_decile": "caar_attention_top_decile_asof_safe.png",
    }
    all_by_window = []

    for name, flag in flags.items():
        raw_events = panel.loc[flag, ["stock_id", "stock_name", "week", "return_start", "first_tradeable_at"]].copy()
        n_raw = len(raw_events)
        filtered = non_overlap_filter(raw_events)
        filtered = flag_calendar_clustering(filtered)
        n_events = len(filtered)
        n_stocks = filtered["stock_id"].nunique()
        max_cluster = filtered["n_events_same_week"].max() if n_events else 0

        event_window = compute_event_window(panel, filtered, stock_prices, market_price)
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
            "CAR_definition": "sum of weekly excess returns from offset +1 through final_window_offset",
            "CAR_mean_at_final_window": final_car.mean() if len(final_car) else None,
            "CAR_std": final_car.std() if len(final_car) else None,
            "t_stat": t_stat, "p_value": p_value,
            "bootstrap_ci_low": ci_low, "bootstrap_ci_high": ci_high,
            "n_events_used_in_test": len(final_car),
        })

        if not by_window.empty and name in fig_map:
            mean_final = final_car.mean() if len(final_car) else 0
            direction = "momentum" if mean_final > 0 else "reversal" if mean_final < 0 else "flat"
            plot_caar(by_window, f"CAAR - {name} (n={n_events} events, {direction})", FIGURES_DIR / fig_map[name])
            print(f"{name}: {n_raw} raw -> {n_events} after filter, {n_stocks} stocks, "
                  f"CAR@+{WINDOW_POST}w mean={final_car.mean():.4f} t={t_stat:.3f} p={p_value:.4f}" if len(final_car) > 1 else f"{name}: insufficient events for test")

    pd.DataFrame(summary_rows).to_csv(TABLES_DIR / "caar_event_summary_asof_safe.csv", index=False, encoding="utf-8-sig")
    if all_by_window:
        pd.concat(all_by_window, ignore_index=True).to_csv(TABLES_DIR / "caar_by_event_window_asof_safe.csv", index=False, encoding="utf-8-sig")
    print(f"\nSaved caar_event_summary_asof_safe.csv and caar_by_event_window_asof_safe.csv to {TABLES_DIR}")


if __name__ == "__main__":
    main()
