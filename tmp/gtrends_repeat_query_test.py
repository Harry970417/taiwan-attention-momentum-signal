"""Phase4 robustness: does repeat-querying the same Google Trends keyword+timeframe
return the same weekly series, or does sampling/normalization introduce drift?
Small standalone script, not part of the production pipeline -- ponytail: throwaway.
"""
import time
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pytrends.request import TrendReq

OUT = Path(__file__).parent / "gtrends_repeat_results.json"

# Anchor + two representative stocks already used in the production pipeline.
QUERIES = {
    "2330": "台積電 股票",
    "2454": "聯發科 股票",
}
TIMEFRAME = "2024-01-01 2024-12-31"  # shorter window than full 5yr sample, still real weekly data
GEO = "TW"
N_REPEATS = 3

results = {}
pytrends = TrendReq(hl="zh-TW", tz=480)

for stock_id, keyword in QUERIES.items():
    series_list = []
    errors = []
    for i in range(N_REPEATS):
        try:
            pytrends.build_payload([keyword], timeframe=TIMEFRAME, geo=GEO)
            df = pytrends.interest_over_time()
            if df.empty:
                errors.append(f"repeat{i}: empty response")
                continue
            s = df[keyword].astype(float)
            series_list.append(s)
            print(f"{stock_id} repeat{i}: {len(s)} weeks, mean={s.mean():.2f}", flush=True)
        except Exception as e:
            errors.append(f"repeat{i}: {type(e).__name__}: {e}")
            print(f"{stock_id} repeat{i}: ERROR {e}", flush=True)
        time.sleep(20)  # be polite between requests to reduce 429 risk

    entry = {"errors": errors, "n_success": len(series_list)}
    if len(series_list) >= 2:
        aligned = pd.concat(series_list, axis=1, join="inner")
        aligned.columns = [f"run{i}" for i in range(len(series_list))]
        corr = aligned.corr().values
        pairwise_corr = [corr[i][j] for i in range(len(series_list)) for j in range(i+1, len(series_list))]
        mad = []
        for i in range(len(series_list)):
            for j in range(i+1, len(series_list)):
                mad.append(float(np.abs(aligned[f"run{i}"] - aligned[f"run{j}"]).mean()))
        # rank stability: Spearman correlation of within-series rank
        rank_corr = []
        for i in range(len(series_list)):
            for j in range(i+1, len(series_list)):
                rank_corr.append(float(aligned[f"run{i}"].rank().corr(aligned[f"run{j}"].rank(), method="spearman")))
        entry.update({
            "n_weeks_aligned": len(aligned),
            "pairwise_pearson_corr": pairwise_corr,
            "pairwise_mean_abs_diff": mad,
            "pairwise_rank_spearman": rank_corr,
        })
    results[stock_id] = entry

OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
print("Saved:", OUT)
