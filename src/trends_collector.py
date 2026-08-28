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
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
try:
    from pytrends.request import TrendReq
    PYTRENDS_IMPORT_ERROR = None
except ImportError as exc:
    TrendReq = None
    PYTRENDS_IMPORT_ERROR = exc

from asof_contract import AVAILABILITY_POLICY, annotate_google_trends_weekly

ROOT = Path(__file__).resolve().parent.parent
CONFIG_CSV = ROOT / "config" / "stock_list_50.csv"
RAW_DIR = ROOT / "data" / "raw"
RESULT_CSV = ROOT / "results" / "tables" / "google_trends_test_result_50.csv"
MANIFEST_PATH = RAW_DIR / "trends50_manifest.json"

ANCHOR_STOCK_ID = "2330"
ANCHOR_KEYWORD = "台積電 股票"
BATCH_SIZE = 4  # + 1 anchor = 5 keywords per pytrends request (Google's max)
RESEARCH_SAMPLE_START = "2021-07-04"
RESEARCH_SAMPLE_END = "2026-07-05"
TIMEFRAME = f"{RESEARCH_SAMPLE_START} {RESEARCH_SAMPLE_END}"
GEO = "TW"
MANIFEST_VERSION = 2
PYTRENDS_REQUIRED_MESSAGE = "pytrends is required for Google Trends collection; install requirements.txt first."


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def request_config() -> dict:
    return {
        "timeframe": TIMEFRAME,
        "geo": GEO,
        "availability_policy": AVAILABILITY_POLICY,
        "anchor_stock_id": ANCHOR_STOCK_ID,
        "anchor_keyword": ANCHOR_KEYWORD,
        "batch_size": BATCH_SIZE,
    }


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def request_config_sha256() -> str:
    return sha256_text(json.dumps(request_config(), ensure_ascii=False, sort_keys=True))


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_pytrends_available() -> None:
    if TrendReq is not None:
        return
    if PYTRENDS_IMPORT_ERROR is not None:
        raise RuntimeError(PYTRENDS_REQUIRED_MESSAGE) from PYTRENDS_IMPORT_ERROR
    raise RuntimeError(PYTRENDS_REQUIRED_MESSAGE)


def new_manifest(invalidated_from: dict | None = None, reason: str = "") -> dict:
    now = utc_now_iso()
    return {
        "manifest_version": MANIFEST_VERSION,
        "request_config": request_config(),
        "request_config_sha256": request_config_sha256(),
        "created_at_utc": now,
        "updated_at_utc": now,
        "invalidated_previous_manifest": invalidated_from is not None,
        "invalidation_reason": reason,
        "stocks": {},
    }


def manifest_matches_request(manifest: dict) -> bool:
    return (
        manifest.get("manifest_version") == MANIFEST_VERSION
        and manifest.get("request_config") == request_config()
        and manifest.get("request_config_sha256") == request_config_sha256()
    )


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        loaded = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if manifest_matches_request(loaded):
            return loaded
        return new_manifest(loaded, "requested timeframe or availability policy changed")
    return new_manifest()


def save_manifest(manifest: dict):
    manifest["request_config"] = request_config()
    manifest["request_config_sha256"] = request_config_sha256()
    manifest["updated_at_utc"] = utc_now_iso()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def cache_entry_is_valid(manifest: dict, stock_id: str, path: Path) -> bool:
    entry = manifest.get("stocks", {}).get(stock_id)
    if not entry or entry.get("scale_factor") is None:
        return False
    if entry.get("timeframe") != TIMEFRAME:
        return False
    if entry.get("availability_policy") != AVAILABILITY_POLICY:
        return False
    if entry.get("request_config_sha256") != request_config_sha256():
        return False
    if not path.exists():
        return False
    return entry.get("file_sha256") == file_sha256(path)


def success_entry(scale_factor, batch, out: pd.DataFrame, trend_path: Path, raw_batch_path: Path | None = None) -> dict:
    return {
        "scale_factor": scale_factor,
        "batch": batch,
        "timeframe": TIMEFRAME,
        "geo": GEO,
        "request_config_sha256": request_config_sha256(),
        "date_start": str(out["observation_period_start"].min().date()),
        "date_end": str(out["observation_period_end"].max().date()),
        "available_at_end": str(out["available_at"].max().date()),
        "availability_policy": AVAILABILITY_POLICY,
        "n_rows": len(out),
        "file_sha256": file_sha256(trend_path),
        "raw_batch_file_sha256": file_sha256(raw_batch_path) if raw_batch_path else None,
        "collected_at_utc": utc_now_iso(),
        "error": "",
    }


def error_entry(batch, error: str) -> dict:
    return {
        "scale_factor": None,
        "batch": batch,
        "timeframe": TIMEFRAME,
        "geo": GEO,
        "request_config_sha256": request_config_sha256(),
        "availability_policy": AVAILABILITY_POLICY,
        "n_rows": 0,
        "file_sha256": None,
        "raw_batch_file_sha256": None,
        "collected_at_utc": utc_now_iso(),
        "error": error,
    }


def make_batches(stocks: pd.DataFrame):
    others = stocks[stocks["stock_id"].astype(str) != ANCHOR_STOCK_ID]
    others = others.reset_index(drop=True)
    batches = []
    for i in range(0, len(others), BATCH_SIZE):
        batches.append(others.iloc[i:i + BATCH_SIZE])
    return batches


def fetch_batch(keywords: list[str]):
    ensure_pytrends_available()
    pytrends = TrendReq(hl="zh-TW", tz=480)
    pytrends.build_payload(keywords, timeframe=TIMEFRAME, geo=GEO)
    df = pytrends.interest_over_time()
    if df is not None and not df.empty:
        if "isPartial" in df.columns:
            df = df.loc[~df["isPartial"].fillna(False).astype(bool)].copy()
        df = df.drop(columns=["isPartial"], errors="ignore")
    return df


def write_trend_series(series: pd.Series, out_path: Path) -> pd.DataFrame:
    out = annotate_google_trends_weekly(series.to_frame(name="SVI"))
    cols = [
        "observation_period_start",
        "observation_period_end",
        "available_at",
        "signal_date",
        "availability_policy",
        "SVI",
    ]
    out[cols].to_csv(out_path, index=False, encoding="utf-8-sig")
    return out


def read_cached_trend(path: Path) -> pd.DataFrame:
    cached = pd.read_csv(path)
    if "SVI" in cached.columns:
        if "observation_period_start" not in cached.columns and "date" in cached.columns:
            cached = cached.copy()
            cached["date"] = pd.to_datetime(cached["date"])
            cached = cached.set_index("date")
        return annotate_google_trends_weekly(cached)
    cached = pd.read_csv(path, index_col=0, parse_dates=True)
    return annotate_google_trends_weekly(cached)


def main():
    ensure_pytrends_available()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_CSV.parent.mkdir(parents=True, exist_ok=True)

    stocks = pd.read_csv(CONFIG_CSV, dtype={"stock_id": str})
    manifest = load_manifest()
    stock_manifest = manifest.setdefault("stocks", {})
    if manifest.get("invalidated_previous_manifest"):
        print(f"Invalidated Trends cache: {manifest.get('invalidation_reason')}")

    # 1) Fetch the anchor alone first (reference scale), unless already cached.
    anchor_path = RAW_DIR / f"trends_{ANCHOR_STOCK_ID}.csv"
    if not cache_entry_is_valid(manifest, ANCHOR_STOCK_ID, anchor_path):
        last_err = ""
        for attempt in range(4):
            try:
                df = fetch_batch([ANCHOR_KEYWORD])
                if df is None or df.empty:
                    last_err = "Empty response for anchor"
                else:
                    df.columns = ["SVI"]
                    out = write_trend_series(df["SVI"], anchor_path)
                    stock_manifest[ANCHOR_STOCK_ID] = success_entry(1.0, "anchor_solo", out, anchor_path)
                    anchor_ref_mean = out["SVI"].mean()
                    save_manifest(manifest)
                    last_err = ""
                    break
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"
            wait = 45 * (attempt + 1)
            print(f"  [anchor] attempt {attempt+1} failed: {last_err}; waiting {wait}s")
            time.sleep(wait)
        if last_err:
            stock_manifest[ANCHOR_STOCK_ID] = error_entry("anchor_solo", last_err)
            save_manifest(manifest)
            print("FATAL: could not fetch anchor keyword; aborting (no valid reference scale).")
            return
        time.sleep(30)
    else:
        anchor_df = read_cached_trend(anchor_path)
        anchor_ref_mean = anchor_df["SVI"].mean()
        print("Anchor already cached, reusing as reference scale.")

    batches = make_batches(stocks)
    for b_idx, batch in enumerate(batches):
        batch_ids = batch["stock_id"].tolist()
        if all(cache_entry_is_valid(manifest, sid, RAW_DIR / f"trends_{sid}.csv") for sid in batch_ids):
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
                    raw_batch_path = RAW_DIR / f"trends_batch_raw_{b_idx}.csv"
                    df.to_csv(raw_batch_path, encoding="utf-8-sig")
                    for sid, kw in zip(batch_ids, batch["keyword"].tolist()):
                        raw_series = df[kw]
                        anchored = raw_series * scale_factor if scale_factor else raw_series
                        trend_path = RAW_DIR / f"trends_{sid}.csv"
                        out = write_trend_series(anchored, trend_path)
                        stock_manifest[sid] = success_entry(scale_factor, b_idx, out, trend_path, raw_batch_path)
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
                stock_manifest[sid] = error_entry(b_idx, last_err)
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
        m = stock_manifest.get(sid, {})
        rows.append({
            "stock_id": sid, "stock_name": name_map[sid], "keyword": kw_map[sid],
            "success": m.get("scale_factor") is not None,
            "scale_factor": m.get("scale_factor"),
            "timeframe": m.get("timeframe", ""),
            "request_config_sha256": m.get("request_config_sha256", ""),
            "date_start": m.get("date_start", ""), "date_end": m.get("date_end", ""),
            "available_at_end": m.get("available_at_end", ""),
            "availability_policy": m.get("availability_policy", ""),
            "file_sha256": m.get("file_sha256", ""),
            "collected_at_utc": m.get("collected_at_utc", ""),
            "n_rows": m.get("n_rows", 0), "error": m.get("error", ""),
        })
    pd.DataFrame(rows).to_csv(RESULT_CSV, index=False, encoding="utf-8-sig")
    n_ok = sum(1 for r in rows if r["success"])
    print(f"\n{n_ok}/{len(rows)} stocks succeeded. Saved summary to {RESULT_CSV}")


if __name__ == "__main__":
    main()
