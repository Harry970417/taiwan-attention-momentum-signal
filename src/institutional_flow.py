"""TAS v0.4 Phase 2b: build the institutional-flow-augmented weekly panel.

IMPORTANT UNIT NOTE: FinMind's free institutional-investor dataset only
provides buy/sell in SHARES, not NTD value. All "*_net_buy_value_*" columns
below are therefore net SHARES bought (buy - sell), not monetary value --
kept the "_value_" name for spec compatibility but documented here and in
the README. Ratio columns divide net shares by total traded shares over the
same window, giving a unit-free "% of volume" flow measure.

dealer = Dealer_self + Dealer_Hedging + Foreign_Dealer_Self (the last is
consistently ~0 in the data but included for completeness).
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CONFIG_CSV = ROOT / "config" / "stock_list_50.csv"
RAW_DIR = ROOT / "data" / "raw"
V03_PANEL = ROOT / "data" / "processed" / "attention_weekly_panel_v03_residual.csv"
OUT_PANEL = ROOT / "data" / "processed" / "attention_weekly_panel_v04.csv"
COVERAGE_OUT = ROOT / "results" / "tables" / "v04_chip_data_coverage.csv"

DEALER_NAMES = ["Dealer_self", "Dealer_Hedging", "Foreign_Dealer_Self"]


def load_daily_flows(stock_id: str):
    path = RAW_DIR / f"inst_breakdown_{stock_id}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["date"])
    df["net"] = df["buy"] - df["sell"]
    wide = df.pivot_table(index="date", columns="name", values="net", aggfunc="sum").fillna(0)
    out = pd.DataFrame(index=wide.index)
    out["foreign_net"] = wide.get("Foreign_Investor", 0)
    out["trust_net"] = wide.get("Investment_Trust", 0)
    out["dealer_net"] = sum(wide.get(n, 0) for n in DEALER_NAMES)
    out["total_net"] = out["foreign_net"] + out["trust_net"] + out["dealer_net"]
    return out.sort_index()


def nearest_at_or_before(index: pd.DatetimeIndex, target: pd.Timestamp):
    cand = index[index <= target]
    return cand[-1] if len(cand) else None


def rolling_flow_features(flows: pd.DataFrame, volume: pd.Series):
    df = flows.copy()
    vol = volume.reindex(df.index)
    for col in ["foreign_net", "trust_net", "dealer_net", "total_net"]:
        df[f"{col}_1w"] = df[col].rolling(5, min_periods=3).sum()
        df[f"{col}_4w"] = df[col].rolling(20, min_periods=10).sum()
    df["volume_1w"] = vol.rolling(5, min_periods=3).sum()
    df["volume_4w"] = vol.rolling(20, min_periods=10).sum()
    return df


def main():
    COVERAGE_OUT.parent.mkdir(parents=True, exist_ok=True)
    stocks = pd.read_csv(CONFIG_CSV, dtype={"stock_id": str})
    panel = pd.read_csv(V03_PANEL, parse_dates=["week"])
    panel["stock_id"] = panel["stock_id"].astype(str)

    chip_rows = []
    coverage_rows = []
    for _, r in stocks.iterrows():
        sid = r["stock_id"]
        flows = load_daily_flows(sid)
        price_path = RAW_DIR / f"price_{sid}.csv"
        if flows is None or not price_path.exists():
            coverage_rows.append({"stock_id": sid, "stock_name": r["stock_name"], "success": False,
                                   "date_start": "", "date_end": "", "n_days": 0, "missing_rate": None,
                                   "usable_weeks": 0, "available_fields": "", "unavailable_fields": "all"})
            continue
        price = pd.read_csv(price_path, parse_dates=["date"]).set_index("date")
        feats = rolling_flow_features(flows, price["Trading_Volume"])

        sub_weeks = panel[panel["stock_id"] == sid]["week"]
        n_usable = 0
        for wk in sub_weeks:
            d = nearest_at_or_before(feats.index, wk)
            if d is None:
                continue
            row = feats.loc[d]
            vol1w, vol4w = row["volume_1w"], row["volume_4w"]
            rec = {"stock_id": sid, "week": wk,
                   "foreign_net_buy_value_1w": row["foreign_net_1w"],
                   "foreign_net_buy_value_4w": row["foreign_net_4w"],
                   "foreign_net_buy_ratio_1w": row["foreign_net_1w"] / vol1w if vol1w else None,
                   "foreign_net_buy_ratio_4w": row["foreign_net_4w"] / vol4w if vol4w else None,
                   "trust_net_buy_value_1w": row["trust_net_1w"],
                   "trust_net_buy_value_4w": row["trust_net_4w"],
                   "trust_net_buy_ratio_1w": row["trust_net_1w"] / vol1w if vol1w else None,
                   "trust_net_buy_ratio_4w": row["trust_net_4w"] / vol4w if vol4w else None,
                   "dealer_net_buy_value_1w": row["dealer_net_1w"],
                   "dealer_net_buy_value_4w": row["dealer_net_4w"],
                   "dealer_net_buy_ratio_1w": row["dealer_net_1w"] / vol1w if vol1w else None,
                   "dealer_net_buy_ratio_4w": row["dealer_net_4w"] / vol4w if vol4w else None,
                   "total_inst_net_buy_value_1w": row["total_net_1w"],
                   "total_inst_net_buy_value_4w": row["total_net_4w"],
                   "total_inst_net_buy_ratio_1w": row["total_net_1w"] / vol1w if vol1w else None,
                   "total_inst_net_buy_ratio_4w": row["total_net_4w"] / vol4w if vol4w else None}
            chip_rows.append(rec)
            if pd.notna(rec["total_inst_net_buy_ratio_4w"]):
                n_usable += 1

        missing_rate = 1 - (n_usable / len(sub_weeks)) if len(sub_weeks) else None
        coverage_rows.append({
            "stock_id": sid, "stock_name": r["stock_name"], "success": True,
            "date_start": str(flows.index.min().date()), "date_end": str(flows.index.max().date()),
            "n_days": len(flows), "missing_rate": round(missing_rate, 4) if missing_rate is not None else None,
            "usable_weeks": n_usable,
            "available_fields": "foreign/trust/dealer/total net buy value+ratio (1w,4w)",
            "unavailable_fields": "monetary value (only share counts available from FinMind free tier)",
        })
        print(f"{sid}: {n_usable}/{len(sub_weeks)} usable weeks")

    chip_df = pd.DataFrame(chip_rows)
    merged = panel.merge(chip_df, on=["stock_id", "week"], how="left")

    keep_cols = [
        "stock_id", "stock_name", "industry", "week",
        "attention_z", "attention_shock", "residual_attention_z", "is_attention_event_z2",
        "past_1w_return", "past_4w_return", "past_8w_return", "past_12w_return", "past_26w_return",
        "future_1w_excess_return", "future_2w_excess_return", "future_4w_excess_return",
        "volume_ratio_4w", "volatility_12w", "liquidity_rank",
        "foreign_net_buy_value_1w", "foreign_net_buy_value_4w",
        "foreign_net_buy_ratio_1w", "foreign_net_buy_ratio_4w",
        "trust_net_buy_value_1w", "trust_net_buy_value_4w",
        "trust_net_buy_ratio_1w", "trust_net_buy_ratio_4w",
        "dealer_net_buy_value_1w", "dealer_net_buy_value_4w",
        "dealer_net_buy_ratio_1w", "dealer_net_buy_ratio_4w",
        "total_inst_net_buy_value_1w", "total_inst_net_buy_value_4w",
        "total_inst_net_buy_ratio_1w", "total_inst_net_buy_ratio_4w",
    ]
    merged = merged[keep_cols]
    merged.to_csv(OUT_PANEL, index=False, encoding="utf-8-sig")
    pd.DataFrame(coverage_rows).to_csv(COVERAGE_OUT, index=False, encoding="utf-8-sig")

    print(f"\nSaved {len(merged)} rows to {OUT_PANEL}")
    print(f"Saved coverage table to {COVERAGE_OUT}")
    print(f"total_inst_net_buy_ratio_4w non-null: {merged['total_inst_net_buy_ratio_4w'].notna().sum()}/{len(merged)}")


if __name__ == "__main__":
    main()
