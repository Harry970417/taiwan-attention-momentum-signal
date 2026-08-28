"""FinMind daily price + institutional-investor loader for the 50-stock TAS v0.2 universe.

Same REST-API-not-package approach as stock_data_loader.py (see that file's
docstring for why the FinMind pip package is avoided on this machine).
Adds TaiwanStockInstitutionalInvestorsBuySell as an optional control variable.
Supports resume: stocks with an existing raw CSV are not re-fetched.
"""
import time
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://api.finmindtrade.com/api/v4/data"
START_DATE = "2021-01-01"

ROOT = Path(__file__).resolve().parent.parent
CONFIG_CSV = ROOT / "config" / "stock_list_50.csv"
RAW_DIR = ROOT / "data" / "raw"


def fetch_dataset(dataset: str, data_id: str, start_date: str = START_DATE):
    params = {"dataset": dataset, "data_id": data_id, "start_date": start_date}
    resp = requests.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_price(stock_id: str):
    out_path = RAW_DIR / f"price_{stock_id}.csv"
    if out_path.exists():
        df = pd.read_csv(out_path)
        return True, len(df), df["date"].min(), df["date"].max(), ""
    try:
        payload = fetch_dataset("TaiwanStockPrice", stock_id)
        if payload.get("status") != 200:
            return False, 0, "", "", f"API status {payload.get('status')}: {payload.get('msg')}"
        data = payload.get("data", [])
        if not data:
            return False, 0, "", "", "Empty data array"
        df = pd.DataFrame(data)
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        return True, len(df), df["date"].min(), df["date"].max(), ""
    except Exception as e:
        return False, 0, "", "", f"{type(e).__name__}: {e}"


def fetch_institutional(stock_id: str):
    out_path = RAW_DIR / f"inst_{stock_id}.csv"
    breakdown_path = RAW_DIR / f"inst_breakdown_{stock_id}.csv"
    if out_path.exists() and breakdown_path.exists():
        return True, ""
    try:
        payload = fetch_dataset("TaiwanStockInstitutionalInvestorsBuySell", stock_id)
        if payload.get("status") != 200:
            return False, f"API status {payload.get('status')}: {payload.get('msg')}"
        data = payload.get("data", [])
        if not data:
            return False, "Empty data array"
        df = pd.DataFrame(data)
        df.to_csv(breakdown_path, index=False, encoding="utf-8-sig")
        net = (
            df.groupby("date")[["buy", "sell"]]
            .apply(lambda g: (g["buy"] - g["sell"]).sum())
            .reset_index(name="institutional_net_shares")
        )
        net.insert(1, "stock_id", stock_id)
        net.to_csv(out_path, index=False, encoding="utf-8-sig")
        return True, ""
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stocks = pd.read_csv(CONFIG_CSV)

    rows = []
    for _, r in stocks.iterrows():
        sid, sname = str(r["stock_id"]), r["stock_name"]
        p_ok, p_rows, p_start, p_end, p_err = fetch_price(sid)
        i_ok, i_err = fetch_institutional(sid)
        rows.append({
            "stock_id": sid, "stock_name": sname,
            "price_success": p_ok, "price_rows": p_rows,
            "price_start": p_start, "price_end": p_end, "price_error": p_err,
            "inst_success": i_ok, "inst_error": i_err,
        })
        print(f"{sid} {sname}: price_ok={p_ok} ({p_rows} rows) inst_ok={i_ok} {p_err}{i_err}")
        time.sleep(1.5)

    pd.DataFrame(rows).to_csv(RAW_DIR / "finmind_fetch_summary_50.csv", index=False, encoding="utf-8-sig")

    # TAIEX benchmark (fetched once, not part of the 50-stock loop)
    taiex_path = RAW_DIR / "price_TAIEX.csv"
    if not taiex_path.exists():
        payload = fetch_dataset("TaiwanStockPrice", "TAIEX")
        pd.DataFrame(payload["data"]).to_csv(taiex_path, index=False, encoding="utf-8-sig")
        print("Fetched TAIEX benchmark")
    else:
        print("TAIEX benchmark already cached")


if __name__ == "__main__":
    main()
