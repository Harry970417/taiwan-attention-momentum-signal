"""FDR correction across all TAS as-of-safe hypothesis tests (Benjamini-Hochberg, alpha=0.10)."""
import pandas as pd
from statsmodels.stats.multitest import multipletests

ROOT = "results/tables"

rows = []

caar = pd.read_csv(f"{ROOT}/caar_event_summary_asof_safe.csv")
for _, r in caar.iterrows():
    rows.append({"family": "event_study_caar", "test": r["event_definition"], "horizon": "final_window", "p_value": r["p_value"]})

fm = pd.read_csv(f"{ROOT}/v03_fama_macbeth_summary_asof_safe.csv")
for _, r in fm.iterrows():
    rows.append({"family": "fama_macbeth", "test": r["model"], "horizon": r["horizon"], "p_value": r["p_value"]})

inter = pd.read_csv(f"{ROOT}/v04_interaction_model_summary_asof_safe.csv")
for _, r in inter.iterrows():
    rows.append({"family": "interaction_model", "test": r["term"], "horizon": r["horizon"], "p_value": r["p_value"]})

df = pd.DataFrame(rows)
reject, p_adj, _, _ = multipletests(df["p_value"], alpha=0.10, method="fdr_bh")
df["p_value_fdr"] = p_adj
df["significant_fdr_010"] = reject

df.to_csv(f"{ROOT}/fdr_correction_all_tests_asof_safe.csv", index=False)

n_sig_raw = (df["p_value"] < 0.10).sum()
n_sig_fdr = df["significant_fdr_010"].sum()
print(f"共 {len(df)} 組檢定")
print(f"原始未校正 p<0.10 顯著數：{n_sig_raw}")
print(f"FDR(alpha=0.10)校正後顯著數：{n_sig_fdr}")
print()
print("=== FDR校正後仍顯著的組 ===")
sig = df[df["significant_fdr_010"]]
if len(sig) == 0:
    print("（無）")
else:
    print(sig.to_string(index=False))
print()
print("=== Model5 pooled 4週 這組的FDR校正結果 ===")
m5 = df[(df["family"] == "fama_macbeth") & (df["test"] == "Model5_pooled_2wayFE_cluster_by_week") & (df["horizon"] == "future_4w_excess_return")]
print(m5.to_string(index=False))
