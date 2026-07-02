"""Google Trends weekly search-volume collector for the 50-stock TAS v0.2 universe.

Cross-stock scale problem: pytrends normalizes each request to its own 0-100
scale, so SVI values from separate single-keyword requests are NOT
comparable across stocks. To partially correct this we batch requests as
[anchor keyword] + [4 other stocks] (Google Trends allows up to 5 terms per
request on a shared scale), always using the same anchor ("台積電 股票").
The anchor's mean level in each batch is compared to a reference batch to
derive a linear rescaling factor, which is applied to the other 4 stocks in
that batch. This is an approximation (Google's underlying index is not
perfectly linear/additive near saturation) -- see README "Google Trends
scale limitation" section. It is NOT required for the CAAR/IC analysis,
which uses each stock's own within-series z-score/ratio (self-normalized),
but it makes cross-stock SVI level comparisons and dashboard displays more
meaningful.

Resumable via data/raw/trends50_manifest.json, independent of any
trends_<id>.csv left over from the earlier 5-stock pilot (v0.1 used
un-anchored single-keyword requests, which are not on the same scale as
this batch-anchored pipeline, so v0.2 refetches all 50 including the
original 5 pilot stocks for consistency).
"""
import json
import time
from pathlib import Path

import pandas as pd
from pytrends.request import TrendReq

ROOT = Path(__file__).resolve().parent.parent
CONFIG_CSV = ROOT / "config" / "stock_list_50.csv"
RAW_DIR = ROOT / "data" / "raw"
RESULT_CSV = ROOT / "results" / "tables" / "google_trends_test_result_50.csv"
MANIFEST_PATH = RAW_DIR / "trends50_manifest.json"

ANCHOR_STOCK_ID = "2330"
ANCHOR_KEYWORD = "台積電 股票"
BATCH_SIZE = 4  # + 1 anchor = 5 keywords per pytrends request (Google's max)
TIMEFRAME = "today 5-y"
GEO = "TW"


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {}


def save_manifest(manifest: dict):
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def make_batches(stocks: pd.DataFrame):
    others = stocks[stocks["stock_id"].astype(str) != ANCHOR_STOCK_ID]
    others = others.reset_index(drop=True)
    batches = []
    for i in range(0, len(others), BATCH_SIZE):
        batches.append(others.iloc[i:i + BATCH_SIZE])
    return batches


def fetch_batch(keywords: list[str]):
    pytrends = TrendReq(hl="zh-TW", tz=480)
    pytrends.build_payload(keywords, timeframe=TIMEFRAME, geo=GEO)
    df = pytrends.interest_over_time()
    if df is not None and not df.empty:
        df = df.drop(columns=["isPartial"], errors="ignore")
    return df


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_CSV.parent.mkdir(parents=True, exist_ok=True)

    stocks = pd.read_csv(CONFIG_CSV, dtype={"stock_id": str})
    manifest = load_manifest()

    # 1) Fetch the anchor alone first (reference scale), unless already cached.
    if ANCHOR_STOCK_ID not in manifest:
        last_err = ""
        for attempt in range(4):
            try:
                df = fetch_batch([ANCHOR_KEYWORD])
                if df is None or df.empty:
                    last_err = "Empty response for anchor"
                else:
                    df.columns = ["SVI"]
                    df.to_csv(RAW_DIR / f"trends_{ANCHOR_STOCK_ID}.csv", encoding="utf-8-sig")
                    manifest[ANCHOR_STOCK_ID] = {
                        "scale_factor": 1.0, "batch": "anchor_solo",
                        "date_start": str(df.index.min().date()), "date_end": str(df.index.max().date()),
                        "n_rows": len(df), "error": "",
                    }
                    anchor_ref_mean = df["SVI"].mean()
                    save_manifest(manifest)
                    last_err = ""
                    break
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"
            wait = 45 * (attempt + 1)
            print(f"  [anchor] attempt {attempt+1} failed: {last_err}; waiting {wait}s")
            time.sleep(wait)
        if last_err:
            manifest[ANCHOR_STOCK_ID] = {"scale_factor": None, "error": last_err}
            save_manifest(manifest)
            print("FATAL: could not fetch anchor keyword; aborting (no valid reference scale).")
            return
        time.sleep(30)
    else:
        anchor_df = pd.read_csv(RAW_DIR / f"trends_{ANCHOR_STOCK_ID}.csv", index_col=0, parse_dates=True)
        anchor_ref_mean = anchor_df.iloc[:, 0].mean()
        print("Anchor already cached, reusing as reference scale.")

    batches = make_batches(stocks)
    for b_idx, batch in enumerate(batches):
        batch_ids = batch["stock_id"].tolist()
        if all(sid in manifest and manifest[sid].get("scale_factor") is not None for sid in batch_ids):
            print(f"Batch {b_idx}: all {batch_ids} cached, skipping")
            continue

        keywords = [ANCHOR_KEYWORD] + batch["keyword"].tolist()
        last_err = ""
        for attempt in range(4):
            try:
                df = fetch_batch(keywords)
                if df is None or df.empty:
                    last_err = "Empty response"
                else:
                    anchor_col = df.columns[0]
                    batch_anchor_mean = df[anchor_col].mean()
                    scale_factor = (anchor_ref_mean / batch_anchor_mean) if batch_anchor_mean > 0 else None
                    df.to_csv(RAW_DIR / f"trends_batch_raw_{b_idx}.csv", encoding="utf-8-sig")
                    for sid, kw in zip(batch_ids, batch["keyword"].tolist()):
                        raw_series = df[kw]
                        anchored = raw_series * scale_factor if scale_factor else raw_series
                        out = anchored.to_frame(name="SVI")
                        out.to_csv(RAW_DIR / f"trends_{sid}.csv", encoding="utf-8-sig")
                        manifest[sid] = {
                            "scale_factor": scale_factor, "batch": b_idx,
                            "date_start": str(out.index.min().date()), "date_end": str(out.index.max().date()),
                            "n_rows": len(out), "error": "",
                        }
                    save_manifest(manifest)
                    last_err = ""
                    break
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"
            wait = 45 * (attempt + 1)
            print(f"  [batch {b_idx} {batch_ids}] attempt {attempt+1} failed: {last_err}; waiting {wait}s")
            time.sleep(wait)
        if last_err:
            for sid in batch_ids:
                manifest[sid] = {"scale_factor": None, "batch": b_idx, "error": last_err}
            save_manifest(manifest)
            print(f"Batch {b_idx} {batch_ids} FAILED after retries: {last_err}; continuing to next batch")
        else:
            print(f"Batch {b_idx} {batch_ids}: OK, scale_factor={scale_factor:.3f}" if scale_factor else f"Batch {b_idx} OK")
        time.sleep(30)

    # Write summary CSV
    rows = []
    name_map = dict(zip(stocks["stock_id"], stocks["stock_name"]))
    kw_map = dict(zip(stocks["stock_id"], stocks["keyword"]))
    for sid in stocks["stock_id"]:
        m = manifest.get(sid, {})
        rows.append({
            "stock_id": sid, "stock_name": name_map[sid], "keyword": kw_map[sid],
            "success": m.get("scale_factor") is not None,
            "scale_factor": m.get("scale_factor"),
            "date_start": m.get("date_start", ""), "date_end": m.get("date_end", ""),
            "n_rows": m.get("n_rows", 0), "error": m.get("error", ""),
        })
    pd.DataFrame(rows).to_csv(RESULT_CSV, index=False, encoding="utf-8-sig")
    n_ok = sum(1 for r in rows if r["success"])
    print(f"\n{n_ok}/{len(rows)} stocks succeeded. Saved summary to {RESULT_CSV}")


if __name__ == "__main__":
    main()
