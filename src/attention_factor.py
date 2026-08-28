"""TAS v0.3 Phase 2: extend the weekly attention panel with momentum,
liquidity, volatility, and industry control variables.

Recomputes from raw data and applies the as-of-safe Google Trends weekly
availability contract before aligning prices and forward returns.
Output: data/processed/attention_weekly_panel_v03_asof_safe.csv
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from asof_contract import (
    AVAILABILITY_POLICY,
    add_trailing_attention_features,
    assert_no_lookahead_panel,
    first_at_or_after,
    forward_window,
    last_at_or_before,
    last_before,
    normalize_date,
    trailing_window_return,
)
from trends_collector import (
    GEO as TRENDS_GEO,
    MANIFEST_VERSION as TRENDS_MANIFEST_VERSION,
    TIMEFRAME as TRENDS_TIMEFRAME,
    file_sha256 as trends_file_sha256,
    manifest_matches_request as trends_manifest_matches_request,
    request_config_sha256 as trends_request_config_sha256,
)

ROOT = Path(__file__).resolve().parent.parent
CONFIG_CSV = ROOT / "config" / "stock_list_50.csv"
RAW_DIR = ROOT / "data" / "raw"
OUT_PATH = ROOT / "data" / "processed" / "attention_weekly_panel_v03_asof_safe.csv"
TABLES_DIR = ROOT / "results" / "tables"
COVERAGE_MANIFEST_PATH = TABLES_DIR / "panel_coverage_manifest_asof_safe.csv"

Z_THRESHOLD = 2.0
SHOCK_THRESHOLD = 1.0
PAST_WINDOWS = [1, 4, 8, 12, 26]
FORWARD_WINDOWS = [1, 2, 4]
MIN_USABLE_PANEL_ROWS = 26
MIN_USABLE_FORWARD_ROWS = 26


def trends_manifest_path() -> Path:
    return RAW_DIR / "trends50_manifest.json"


def assert_trends_file_matches_manifest(stock_id: str, path: Path) -> None:
    manifest_path = trends_manifest_path()
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Missing Google Trends manifest: {manifest_path}. "
            f"Refusing to use cached {path.name} without provenance."
        )

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid Google Trends manifest JSON: {manifest_path}") from e

    if not trends_manifest_matches_request(manifest):
        raise ValueError(
            "Google Trends manifest does not match the current pinned request config "
            f"(manifest_version={TRENDS_MANIFEST_VERSION}, timeframe={TRENDS_TIMEFRAME}, "
            f"geo={TRENDS_GEO}, availability_policy={AVAILABILITY_POLICY}). "
            f"Refusing to use cached {path.name}."
        )

    entry = manifest.get("stocks", {}).get(str(stock_id))
    if not entry:
        raise ValueError(f"Google Trends manifest has no entry for stock_id={stock_id}; refusing {path.name}.")
    if entry.get("scale_factor") is None:
        error = entry.get("error") or "no successful collection recorded"
        raise ValueError(f"Google Trends manifest marks stock_id={stock_id} as failed: {error}")

    required = {
        "timeframe": TRENDS_TIMEFRAME,
        "geo": TRENDS_GEO,
        "availability_policy": AVAILABILITY_POLICY,
        "request_config_sha256": trends_request_config_sha256(),
    }
    mismatches = [
        f"{field}={entry.get(field)!r} (expected {expected!r})"
        for field, expected in required.items()
        if entry.get(field) != expected
    ]
    if mismatches:
        raise ValueError(
            f"Google Trends manifest entry for stock_id={stock_id} is stale/incompatible: "
            + "; ".join(mismatches)
        )

    expected_hash = entry.get("file_sha256")
    actual_hash = trends_file_sha256(path)
    if not expected_hash or actual_hash != expected_hash:
        raise ValueError(
            f"Google Trends file hash mismatch for stock_id={stock_id}: "
            f"manifest={expected_hash!r}, actual={actual_hash!r}. Refusing {path.name}."
        )


def load_trends(stock_id: str):
    path = RAW_DIR / f"trends_{stock_id}.csv"
    if not path.exists():
        return None
    assert_trends_file_matches_manifest(stock_id, path)
    raw = pd.read_csv(path)
    if "observation_period_start" in raw.columns:
        return raw.reset_index(drop=True)
    if "SVI" in raw.columns and raw.columns[0] != "SVI":
        legacy = raw.set_index(pd.to_datetime(raw[raw.columns[0]]))[["SVI"]]
        return legacy
    legacy = pd.read_csv(path, index_col=0, parse_dates=True)
    if "SVI" not in legacy.columns:
        legacy.columns = ["SVI"]
    return legacy


def load_price(stock_id: str, taiex_ret: pd.Series):
    path = RAW_DIR / f"price_{stock_id}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["date"]).sort_values("date").set_index("date")
    df["ret"] = df["close"].pct_change()

    df["vol_ma20"] = df["Trading_Volume"].rolling(20, min_periods=10).mean()
    df["vol_ma60"] = df["Trading_Volume"].rolling(60, min_periods=30).mean()
    df["turnover_ma20"] = df["Trading_money"].rolling(20, min_periods=10).mean()
    df["volatility_20"] = df["ret"].rolling(20, min_periods=10).std()
    df["volatility_60"] = df["ret"].rolling(60, min_periods=30).std()

    roll_max_60 = df["close"].rolling(60, min_periods=30).max()
    df["drawdown"] = df["close"] / roll_max_60 - 1
    df["max_drawdown_12w"] = df["drawdown"].rolling(60, min_periods=30).min()

    mkt = taiex_ret.reindex(df.index)
    cov = df["ret"].rolling(130, min_periods=65).cov(mkt)
    var = mkt.rolling(130, min_periods=65).var()
    df["beta_26w"] = cov / var
    return df


def nearest_at_or_after(index: pd.DatetimeIndex, target: pd.Timestamp):
    cand = index[index >= target]
    return cand[0] if len(cand) else None


def nearest_at_or_before(index: pd.DatetimeIndex, target: pd.Timestamp):
    cand = index[index <= target]
    return cand[-1] if len(cand) else None


def window_return(price: pd.Series, date: pd.Timestamp, n_weeks: int, direction: str):
    idx = price.index
    if direction == "forward":
        d0 = nearest_at_or_after(idx, date)
        d1 = nearest_at_or_after(idx, date + pd.Timedelta(weeks=n_weeks))
    else:
        d1 = nearest_at_or_before(idx, date)
        d0 = nearest_at_or_before(idx, date - pd.Timedelta(weeks=n_weeks))
    if d0 is None or d1 is None:
        return None
    p0, p1 = price.loc[d0], price.loc[d1]
    if pd.isna(p0) or pd.isna(p1) or p0 == 0:
        return None
    return p1 / p0 - 1


def _r(x, n=4):
    return round(x, n) if x is not None and pd.notna(x) else None


def write_coverage_manifest(rows: list[dict]) -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(COVERAGE_MANIFEST_PATH, index=False, encoding="utf-8-sig")


def coverage_failures(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r.get("status") != "accepted"]


def assert_complete_universe_coverage(rows: list[dict], expected_n: int) -> None:
    failures = coverage_failures(rows)
    if len(rows) != expected_n or failures:
        raise RuntimeError(
            "Corrected panel coverage gate failed: "
            f"{len(failures)} of {expected_n} configured stocks are missing required raw inputs "
            "or minimum usable history; refusing to write a partial survivor universe. "
            f"See {COVERAGE_MANIFEST_PATH.relative_to(ROOT)}."
        )


def build_for_stock(stock_id, stock_name, industry, price, taiex, svi):
    svi = add_trailing_attention_features(svi)

    rows = []
    for date, r in svi.dropna(subset=["SVI_MA52"]).iterrows():
        signal_date = normalize_date(r["signal_date"])
        first_tradeable = first_at_or_after(price.index, signal_date)
        if first_tradeable is None:
            continue
        feature_asof = last_before(price.index, first_tradeable)
        if feature_asof is None:
            continue

        rec = {
            "stock_id": stock_id, "stock_name": stock_name, "industry": industry,
            "week": signal_date.date(),
            "google_trends_week": normalize_date(r["observation_period_start"]).date(),
            "observation_period_start": normalize_date(r["observation_period_start"]).date(),
            "observation_period_end": normalize_date(r["observation_period_end"]).date(),
            "available_at": normalize_date(r["available_at"]).date(),
            "signal_date": signal_date.date(),
            "first_tradeable_at": first_tradeable.date(),
            "feature_asof_trade_date": feature_asof.date(),
            "return_start": first_tradeable.date(),
            "availability_policy": r["availability_policy"],
            "availability_lag_days": int((normalize_date(r["available_at"]) - normalize_date(r["observation_period_start"])).days),
            "z_window_end": normalize_date(r["z_window_end"]).date(),
            "SVI_window_n": int(r["SVI_window_n"]) if pd.notna(r["SVI_window_n"]) else None,
            "SVI": r["SVI"], "SVI_MA52": _r(r["SVI_MA52"], 3), "SVI_STD52": _r(r["SVI_STD52"], 3),
            "attention_shock": _r(r["attention_shock"]), "attention_z": _r(r["attention_z"]),
        }
        rec["is_attention_event_z2"] = bool(pd.notna(r["attention_z"]) and r["attention_z"] > Z_THRESHOLD)
        rec["is_attention_event_ratio"] = bool(pd.notna(r["attention_shock"]) and r["attention_shock"] > SHOCK_THRESHOLD)

        rec["weekly_return"] = _r(trailing_window_return(price["close"], feature_asof, 1))
        rec["market_weekly_return"] = _r(trailing_window_return(taiex["close"], feature_asof, 1))
        if rec["weekly_return"] is not None and rec["market_weekly_return"] is not None:
            rec["weekly_excess_return"] = round(rec["weekly_return"] - rec["market_weekly_return"], 4)
        else:
            rec["weekly_excess_return"] = None

        for n in PAST_WINDOWS:
            rec[f"past_{n}w_return"] = _r(trailing_window_return(price["close"], feature_asof, n))

        for n in FORWARD_WINDOWS:
            s_end, s_fwd = forward_window(price["close"], first_tradeable, n)
            _, m_fwd = forward_window(taiex["close"], first_tradeable, n)
            rec[f"return_end_{n}w"] = s_end.date() if s_end is not None else None
            rec[f"future_{n}w_return"] = _r(s_fwd)
            rec[f"future_{n}w_excess_return"] = _r(s_fwd - m_fwd) if (s_fwd is not None and m_fwd is not None) else None

        d = feature_asof
        if d is not None:
            row = price.loc[d]
            rec["volume_ratio_4w"] = _r(row["Trading_Volume"] / row["vol_ma20"]) if row["vol_ma20"] and row["vol_ma20"] > 0 else None
            rec["volume_ratio_12w"] = _r(row["Trading_Volume"] / row["vol_ma60"]) if row["vol_ma60"] and row["vol_ma60"] > 0 else None
            rec["turnover_proxy"] = _r(row["turnover_ma20"], 0)
            rec["trading_value_proxy"] = _r(row["Trading_money"], 0)
            rec["volatility_4w"] = _r(row["volatility_20"])
            rec["volatility_12w"] = _r(row["volatility_60"])
            rec["beta_26w"] = _r(row["beta_26w"])
            rec["max_drawdown_12w"] = _r(row["max_drawdown_12w"])
        else:
            for c in ["volume_ratio_4w", "volume_ratio_12w", "turnover_proxy", "trading_value_proxy",
                      "volatility_4w", "volatility_12w", "beta_26w", "max_drawdown_12w"]:
                rec[c] = None

        rows.append(rec)
    return pd.DataFrame(rows)


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    stocks = pd.read_csv(CONFIG_CSV, dtype={"stock_id": str})
    taiex_path = RAW_DIR / "price_TAIEX.csv"
    if not taiex_path.exists():
        write_coverage_manifest([{
            "stock_id": r["stock_id"],
            "stock_name": r["stock_name"],
            "industry": r["industry"],
            "status": "blocked_missing_benchmark",
            "trends_present": (RAW_DIR / f"trends_{r['stock_id']}.csv").exists(),
            "price_present": (RAW_DIR / f"price_{r['stock_id']}.csv").exists(),
            "benchmark_present": False,
            "panel_rows": 0,
            "future_4w_excess_rows": 0,
            "minimum_panel_rows": MIN_USABLE_PANEL_ROWS,
            "minimum_future_4w_excess_rows": MIN_USABLE_FORWARD_ROWS,
            "reason": f"Missing real raw benchmark data: {taiex_path}",
        } for _, r in stocks.iterrows()])
        raise FileNotFoundError(
            f"Missing real raw benchmark data: {taiex_path}. "
            "Run scripts/run_data_collection.py with real API access; do not use data/sample as research evidence."
        )
    taiex = pd.read_csv(taiex_path, parse_dates=["date"]).sort_values("date").set_index("date")
    taiex["ret"] = taiex["close"].pct_change()

    panels, coverage_rows = [], []
    for _, r in stocks.iterrows():
        sid, sname, industry = r["stock_id"], r["stock_name"], r["industry"]
        trends_path = RAW_DIR / f"trends_{sid}.csv"
        price_path = RAW_DIR / f"price_{sid}.csv"
        coverage = {
            "stock_id": sid,
            "stock_name": sname,
            "industry": industry,
            "status": "accepted",
            "trends_present": trends_path.exists(),
            "price_present": price_path.exists(),
            "benchmark_present": True,
            "panel_rows": 0,
            "future_4w_excess_rows": 0,
            "minimum_panel_rows": MIN_USABLE_PANEL_ROWS,
            "minimum_future_4w_excess_rows": MIN_USABLE_FORWARD_ROWS,
            "reason": "",
        }
        try:
            svi = load_trends(sid)
        except Exception as e:
            coverage["status"] = "blocked_invalid_trends_input"
            coverage["reason"] = f"{type(e).__name__}: {e}"
            coverage_rows.append(coverage)
            continue
        try:
            price = load_price(sid, taiex["ret"])
        except Exception as e:
            coverage["status"] = "blocked_invalid_price_input"
            coverage["reason"] = f"{type(e).__name__}: {e}"
            coverage_rows.append(coverage)
            continue
        if svi is None or price is None:
            missing = []
            if svi is None:
                missing.append("trends")
            if price is None:
                missing.append("price")
            coverage["status"] = "blocked_missing_raw_input"
            coverage["reason"] = "Missing required raw input(s): " + ", ".join(missing)
            coverage_rows.append(coverage)
            continue
        try:
            df = build_for_stock(sid, sname, industry, price, taiex, svi)
        except Exception as e:
            coverage["status"] = "blocked_panel_build_error"
            coverage["reason"] = f"{type(e).__name__}: {e}"
            coverage_rows.append(coverage)
            continue
        coverage["panel_rows"] = len(df)
        coverage["future_4w_excess_rows"] = int(df["future_4w_excess_return"].notna().sum()) if "future_4w_excess_return" in df.columns else 0
        if len(df) < MIN_USABLE_PANEL_ROWS:
            coverage["status"] = "blocked_insufficient_history"
            coverage["reason"] = f"Only {len(df)} usable panel rows after as-of feature construction."
        elif coverage["future_4w_excess_rows"] < MIN_USABLE_FORWARD_ROWS:
            coverage["status"] = "blocked_insufficient_forward_history"
            coverage["reason"] = (
                f"Only {coverage['future_4w_excess_rows']} usable 4w forward-excess rows after alignment."
            )
        else:
            panels.append(df)
        coverage_rows.append(coverage)
        print(f"{sid}: {len(df)} weeks")

    write_coverage_manifest(coverage_rows)
    assert_complete_universe_coverage(coverage_rows, len(stocks))

    panel = pd.concat(panels, ignore_index=True)

    # Cross-sectional liquidity_rank each week (1 = most liquid, by turnover_proxy)
    panel["liquidity_rank"] = panel.groupby("week")["turnover_proxy"].rank(ascending=False, method="average")
    assert_no_lookahead_panel(panel)

    panel.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\nSaved {len(panel)} rows ({panel['stock_id'].nunique()} stocks) to {OUT_PATH}")


if __name__ == "__main__":
    main()
