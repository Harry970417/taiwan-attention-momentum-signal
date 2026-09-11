"""Generate the remaining TAS chart set for the admissions portfolio, from real as-of-safe results."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np

plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]
plt.rcParams["axes.unicode_minus"] = False

OUT = r"C:\Users\user\Desktop\推甄資料最新版\06_圖表與視覺素材"
ROOT = "results/tables"

# 1. Effect size comparison (legacy vs corrected CAR mean)
cmp = pd.read_csv(f"{ROOT}/asof_safe_legacy_comparison.csv")
car = cmp[(cmp["comparison"] == "event_study_caar") & (cmp["metric"] == "CAR_mean_at_final_window")]
labels = car["event_definition"].tolist()
legacy = car["legacy_value"].astype(float) * 100
corrected = car["corrected_value"].astype(float) * 100
x = np.arange(len(labels)); w = 0.35
fig, ax = plt.subplots(figsize=(8, 5.5))
ax.bar(x - w/2, legacy, w, label="修正前 (Legacy)", color="#c0392b")
ax.bar(x + w/2, corrected, w, label="修正後 (Corrected)", color="#2980b9")
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_ylabel("CAR 均值 (%)")
ax.set_title("TAS：Look-ahead Bias 修正前後累積異常報酬(CAR)對照")
ax.legend()
fig.tight_layout(); fig.savefig(f"{OUT}/tas_legacy_vs_corrected_effect_size.png", dpi=300); plt.close(fig)

# 2. Interaction coefficient + CI (attention_z_x_past_4w_return across horizons)
inter = pd.read_csv(f"{ROOT}/v04_interaction_model_summary_asof_safe.csv")
it = inter[inter["term"] == "attention_z_x_past_4w_return"].copy()
horizon_labels = {"future_1w_excess_return": "1週", "future_2w_excess_return": "2週", "future_4w_excess_return": "4週"}
it["h"] = it["horizon"].map(horizon_labels)
# approximate 95% CI from coefficient and t_stat -> se = coef/t
it["se"] = it["coefficient"].abs() / it["t_stat"].abs()
it["ci"] = 1.96 * it["se"]
fig, ax = plt.subplots(figsize=(7, 5))
ax.errorbar(it["h"], it["coefficient"], yerr=it["ci"], fmt="o", capsize=6, color="#8e44ad", markersize=9)
ax.axhline(0, color="gray", linestyle="--", linewidth=1)
ax.set_ylabel("交互作用係數 (attention_z × 過去4週報酬)")
ax.set_title("TAS：注意力×動能交互作用係數與95%信賴區間\n(正式檢定不支持「放大器」機制——區間皆涵蓋0)")
fig.tight_layout(); fig.savefig(f"{OUT}/tas_interaction_coefficient_ci.png", dpi=300); plt.close(fig)

# 3. Model1-5 coefficient plot with FDR significance markers.
# ponytail: single vertical forest-plot (15 rows: 5 models x 3 horizons) with
# 95% CI error bars, not 3 side-by-side subplots -- the 3-subplot layout
# forced 8pt tick labels and made it hard to see at a glance that M2-M4
# mostly lose significance once momentum is controlled for. This must stay
# a single authoritative plot so "which rows are still significant after
# FDR" reads in one glance, not spread across 3 small panels.
fdr = pd.read_csv(f"{ROOT}/fdr_correction_all_tests_asof_safe.csv")
fm = pd.read_csv(f"{ROOT}/v03_fama_macbeth_summary_asof_safe.csv")
fm_fdr = fdr[fdr["family"] == "fama_macbeth"]
fm = fm.merge(fm_fdr[["test", "horizon", "significant_fdr_010", "p_value_fdr"]], left_on=["model", "horizon"], right_on=["test", "horizon"])
model_order = ["Model1_attention_only", "Model2_plus_momentum", "Model3_plus_volume_vol", "Model4_plus_liquidity_industry_FE", "Model5_pooled_2wayFE_cluster_by_week"]
model_short = {"Model1_attention_only": "M1 純注意力", "Model2_plus_momentum": "M2 +動能", "Model3_plus_volume_vol": "M3 +量能波動", "Model4_plus_liquidity_industry_FE": "M4 +流動性/產業FE", "Model5_pooled_2wayFE_cluster_by_week": "M5 二維FE"}
horizon_order = ["future_1w_excess_return", "future_2w_excess_return", "future_4w_excess_return"]
horizon_label = {"future_1w_excess_return": "1週", "future_2w_excess_return": "2週", "future_4w_excess_return": "4週"}
fm["se"] = fm["coefficient"].abs() / fm["t_stat"].abs()
fm["ci95"] = 1.96 * fm["se"]
rows = [(m, h) for m in model_order for h in horizon_order]
fm_idx = fm.set_index(["model", "horizon"])
labels = [f"{model_short[m]} | {horizon_label[h]}" for m, h in rows]
coefs = [fm_idx.loc[(m, h), "coefficient"] for m, h in rows]
cis = [fm_idx.loc[(m, h), "ci95"] for m, h in rows]
sig = [bool(fm_idx.loc[(m, h), "significant_fdr_010"]) for m, h in rows]
colors = ["#2e7d32" if s else "#9e9e9e" for s in sig]
y = np.arange(len(rows))[::-1]  # top row = first entry
fig, ax = plt.subplots(figsize=(13, 9))
for i, (yi, col) in enumerate(zip(y, colors)):
    ax.errorbar([coefs[i]], [yi], xerr=[cis[i]], fmt="o", capsize=5, markersize=9,
                elinewidth=2, ecolor=col, mfc=col, mec=col)
ax.axvline(0, color="black", linewidth=1)
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=11)
ax.set_xlabel("迴歸係數（95% 信賴區間）", fontsize=12)
ax.tick_params(axis="x", labelsize=11)
ax.set_title("TAS：M1–M4 Fama-MacBeth／M5 Two-way FE 全部15組係數與95% CI\n（綠色＝FDR校正後仍顯著，灰色＝不顯著；M1-4與M5非同一covariance estimator，見文字說明）", fontsize=14)
fig.tight_layout(); fig.savefig(f"{OUT}/tas_model1to5_coefficients_fdr.png", dpi=300); plt.close(fig)

# 3b. Legacy vs corrected t-statistic comparison (event study, 3 attention
# definitions) -- previously generated ad hoc, never saved to a tracked
# script (Codex/visual-QA gap). Recreate from the same comparison table used
# by chart 1 above so it has an authoritative, reproducible source.
tstat = cmp[(cmp["comparison"] == "event_study_caar") & (cmp["metric"] == "t_stat")]
t_labels = tstat["event_definition"].tolist()
t_legacy = tstat["legacy_value"].astype(float)
t_corrected = tstat["corrected_value"].astype(float)
xt = np.arange(len(t_labels)); wt = 0.35
fig, ax = plt.subplots(figsize=(9, 6.5))
ax.bar(xt - wt/2, t_legacy, wt, label="修正前 (Legacy)", color="#c0392b")
ax.bar(xt + wt/2, t_corrected, wt, label="修正後 (Corrected)", color="#2980b9")
ax.axhline(1.96, color="gray", linestyle="--", linewidth=1.3, label="5% 顯著門檻 (t=1.96)")
ax.set_xticks(xt); ax.set_xticklabels(t_labels, fontsize=11)
ax.set_ylabel("t 統計量", fontsize=12)
ax.tick_params(axis="y", labelsize=11)
ax.set_title("TAS：Look-ahead Bias 修正前後事件研究 t 統計量對照", fontsize=15)
ax.legend(fontsize=10.5)
fig.tight_layout(); fig.savefig(f"{OUT}/tas_legacy_vs_corrected_tstat.png", dpi=300); plt.close(fig)

# 4. Double-sort heatmap (4w)
# ponytail: source CSV has a 3-row multi-index header (metric name row,
# mean/count row, mom_bucket/att_bucket label row) that pd.read_csv's default
# single-header read mangles into "Unnamed: 0"-style columns, so mom_bucket/
# att_bucket never matched and this chart silently never wrote its PNG.
ds = pd.read_csv(f"{ROOT}/v03_double_sort_past4w_attention_asof_safe.csv", header=None, skiprows=3)
ds.columns = ["mom_bucket", "att_bucket", "f1w_mean", "f1w_count", "f2w_mean", "f2w_count",
              "future_4w_excess_return_mean", "f4w_count"]
pivot = ds.pivot(index="mom_bucket", columns="att_bucket", values="future_4w_excess_return_mean")
if pivot is not None:
    order_mom = [m for m in ["loser", "neutral", "winner"] if m in pivot.index]
    order_att = [a for a in ["low_attention", "mid_attention", "high_attention"] if a in pivot.columns]
    pivot = pivot.reindex(index=order_mom, columns=order_att)
    fig, ax = plt.subplots(figsize=(6.5, 5))
    im = ax.imshow(pivot.values * 100, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(range(len(order_att))); ax.set_xticklabels(["低注意力", "中注意力", "高注意力"])
    ax.set_yticks(range(len(order_mom))); ax.set_yticklabels(["輸家", "中性", "贏家"])
    for i in range(len(order_mom)):
        for j in range(len(order_att)):
            ax.text(j, i, f"{pivot.values[i,j]*100:.2f}%", ha="center", va="center", fontsize=10)
    fig.colorbar(im, label="未來4週超額報酬 (%)")
    ax.set_title("TAS：動能×注意力 Double Sort（描述性，非正式檢定結論）")
    fig.tight_layout(); fig.savefig(f"{OUT}/tas_double_sort_heatmap.png", dpi=300); plt.close(fig)

# 5. Event study CAAR bar
caar = pd.read_csv(f"{ROOT}/caar_event_summary_asof_safe.csv")
fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(caar["event_definition"], caar["CAR_mean_at_final_window"] * 100, color="#2980b9")
for b, p in zip(bars, caar["p_value"]):
    ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.1, f"p={p:.4f}", ha="center", fontsize=9)
ax.set_ylabel("CAR 均值 @+8週 (%)")
ax.set_title("TAS：事件研究法累積異常報酬（修正後，皆FDR顯著）")
fig.tight_layout(); fig.savefig(f"{OUT}/tas_event_study_caar.png", dpi=300); plt.close(fig)

# 6. Research timeline
fig, ax = plt.subplots(figsize=(11, 3.2))
stages = ["原始模型\n顯著支持\n「放大器」假說", "稽核發現\nGoogle Trends\nlook-ahead bias", "主動撤回\n原結論", "建立as-of-safe\n資料管線", "50檔237週\n完整重新驗證", "FDR校正：\n事件研究+M1顯著\n交互作用不顯著"]
xs = np.arange(len(stages))
ax.plot(xs, [0]*len(stages), color="#34495e", linewidth=2, zorder=1)
ax.scatter(xs, [0]*len(stages), s=140, color="#2980b9", zorder=2)
for i, s in enumerate(stages):
    ax.text(i, 0.15 if i % 2 == 0 else -0.15, s, ha="center", va="bottom" if i % 2 == 0 else "top", fontsize=9)
ax.set_ylim(-0.6, 0.6); ax.axis("off")
ax.set_title("TAS 研究時間軸：從錯誤結論到誠實重新驗證")
fig.tight_layout(); fig.savefig(f"{OUT}/tas_research_timeline.png", dpi=300); plt.close(fig)

print("done")
