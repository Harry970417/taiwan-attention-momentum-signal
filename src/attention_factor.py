"""TAS v0.3 Phase 2: extend the weekly attention panel with momentum,
liquidity, volatility, and industry control variables.

Recomputes from raw data (rather than merging onto attention_weekly_panel_50.csv)
so all fields use a single consistent nearest-trading-day alignment.
Output: data/processed/attention_weekly_panel_v03.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CONFIG_CSV = ROOT / "config" / "stock_list_50.csv"
RAW_DIR = ROOT / "data" / "raw"
OUT_PATH = ROOT / "data" / "processed" / "attention_weekly_panel_v03.csv"

Z_THRESHOLD = 2.0
SHOCK_THRESHOLD = 1.0
PAST_WINDOWS = [1, 4, 8, 12, 26]
FORWARD_WINDOWS = [1, 2, 4]


def load_trends(stock_id: str):
    path = RAW_DIR / f"trends_{stock_id}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.columns = ["SVI"]
    df.index.name = "week"
    return df


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


def build_for_stock(stock_id, stock_name, industry, price, taiex, svi):
    svi = svi.copy()
    svi["SVI_MA52"] = svi["SVI"].rolling(52, min_periods=26).mean()
    svi["SVI_STD52"] = svi["SVI"].rolling(52, min_periods=26).std()
    svi["attention_shock"] = svi["SVI"] / svi["SVI_MA52"] - 1
    svi["attention_z"] = (svi["SVI"] - svi["SVI_MA52"]) / svi["SVI_STD52"]

    rows = []
    for date, r in svi.dropna(subset=["SVI_MA52"]).iterrows():
        rec = {
            "stock_id": stock_id, "stock_name": stock_name, "industry": industry, "week": date.date(),
            "SVI": r["SVI"], "SVI_MA52": _r(r["SVI_MA52"], 3), "SVI_STD52": _r(r["SVI_STD52"], 3),
            "attention_shock": _r(r["attention_shock"]), "attention_z": _r(r["attention_z"]),
        }
        rec["is_attention_event_z2"] = bool(pd.notna(r["attention_z"]) and r["attention_z"] > Z_THRESHOLD)
        rec["is_attention_event_ratio"] = bool(pd.notna(r["attention_shock"]) and r["attention_shock"] > SHOCK_THRESHOLD)

        rec["weekly_return"] = _r(window_return(price["close"], date, 1, "backward"))
        rec["market_weekly_return"] = _r(window_return(taiex["close"], date, 1, "backward"))
        if rec["weekly_return"] is not None and rec["market_weekly_return"] is not None:
            rec["weekly_excess_return"] = round(rec["weekly_return"] - rec["market_weekly_return"], 4)
        else:
            rec["weekly_excess_return"] = None

        for n in PAST_WINDOWS:
            rec[f"past_{n}w_return"] = _r(window_return(price["close"], date, n, "backward"))

        for n in FORWARD_WINDOWS:
            s_fwd = window_return(price["close"], date, n, "forward")
            m_fwd = window_return(taiex["close"], date, n, "forward")
            rec[f"future_{n}w_return"] = _r(s_fwd)
            rec[f"future_{n}w_excess_return"] = _r(s_fwd - m_fwd) if (s_fwd is not None and m_fwd is not None) else None

        d = nearest_at_or_before(price.index, date)
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
    taiex = pd.read_csv(RAW_DIR / "price_TAIEX.csv", parse_dates=["date"]).sort_values("date").set_index("date")
    taiex["ret"] = taiex["close"].pct_change()

    panels, skipped = [], []
    for _, r in stocks.iterrows():
        sid, sname, industry = r["stock_id"], r["stock_name"], r["industry"]
        svi = load_trends(sid)
        price = load_price(sid, taiex["ret"])
        if svi is None or price is None:
            skipped.append(sid)
            continue
        df = build_for_stock(sid, sname, industry, price, taiex, svi)
        panels.append(df)
        print(f"{sid}: {len(df)} weeks")

    panel = pd.concat(panels, ignore_index=True)

    # Cross-sectional liquidity_rank each week (1 = most liquid, by turnover_proxy)
    panel["liquidity_rank"] = panel.groupby("week")["turnover_proxy"].rank(ascending=False, method="average")

    panel.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\nSaved {len(panel)} rows ({panel['stock_id'].nunique()} stocks) to {OUT_PATH}")
    if skipped:
        print(f"Skipped: {skipped}")


if __name__ == "__main__":
    main()
