"""FDR correction across all TAS as-of-safe hypothesis tests (Benjamini-Hochberg).

Primary/authoritative test family (see MULTIPLE_TESTING_FAMILY_CONTRACT.md for
the rationale): all 30 tests -- 3 event-study CAAR definitions + 15 regression
specifications (M1-M4 Fama-MacBeth x 3 horizons, M5 two-way FE x 3 horizons)
+ 12 interaction tests (Model E, 4 terms x 3 horizons) -- corrected together
as one family. Reported at both q=0.10 and q=0.05.

Secondary sensitivity only: the same three groups corrected separately
(event_study / regression / interaction sub-families), to show whether
family-scoping changes the conclusion. The single authoritative rule is the
pooled 30-test family above.
"""
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

for q in (0.10, 0.05):
    reject, p_adj, _, _ = multipletests(df["p_value"], alpha=q, method="fdr_bh")
    df[f"p_value_fdr_q{q:.2f}"] = p_adj
    df[f"significant_fdr_q{q:.2f}"] = reject

# Backward-compatible column names (q=0.10 was the only level before this pass)
df["p_value_fdr"] = df["p_value_fdr_q0.10"]
df["significant_fdr_010"] = df["significant_fdr_q0.10"]

df.to_csv(f"{ROOT}/fdr_correction_all_tests_asof_safe.csv", index=False)

print(f"=== Primary family: all {len(df)} tests pooled ===")
for q in (0.10, 0.05):
    n_sig = df[f"significant_fdr_q{q:.2f}"].sum()
    print(f"q={q:.2f}: {n_sig} of {len(df)} significant after BH-FDR")
    sig = df[df[f"significant_fdr_q{q:.2f}"]]
    if len(sig):
        print(sig[["family", "test", "horizon", "p_value", f"p_value_fdr_q{q:.2f}"]].to_string(index=False))
    print()

# Secondary sensitivity: correct each family separately
sensitivity_rows = []
for family, grp in df.groupby("family"):
    for q in (0.10, 0.05):
        reject, p_adj, _, _ = multipletests(grp["p_value"], alpha=q, method="fdr_bh")
        for (_, r), rej, padj in zip(grp.iterrows(), reject, p_adj):
            sensitivity_rows.append({
                "family": family, "test": r["test"], "horizon": r["horizon"], "p_value": r["p_value"],
                "q": q, "p_value_fdr_within_family": padj, "significant_within_family": rej,
            })
sens_df = pd.DataFrame(sensitivity_rows)
sens_df.to_csv(f"{ROOT}/fdr_correction_by_family_sensitivity_asof_safe.csv", index=False)

print("=== Secondary sensitivity: each family corrected separately ===")
for (family, q), grp in sens_df.groupby(["family", "q"]):
    n_sig = grp["significant_within_family"].sum()
    print(f"{family} (n={len(grp)}), q={q:.2f}: {n_sig} significant")
