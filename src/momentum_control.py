"""TAS v0.3 Phase 4: Fama-MacBeth weekly cross-sectional regressions.

Models 1-4 are literal per-week cross-sectional OLS regressions (the
Fama-MacBeth procedure): fit week-by-week, then aggregate the
attention_z coefficient's time series (mean, std, t-stat = mean/(std/sqrt(T))).

Model 5 as literally specified ("week fixed effects" inside a per-week
cross-sectional regression) is not well-posed: a single week's slice has
no time variation, so a week dummy is undefined, and a full set of
50 stock dummies against ~50 observations leaves ~0 residual degrees of
freedom. Per the instructions to "honestly record and switch to a feasible
model" when this happens, Model 5 is instead estimated as a POOLED
two-way (stock + week) fixed-effects panel regression with standard errors
clustered by week -- which also directly addresses the calendar-clustering
concern raised in the v0.2 report (events cluster heavily in certain weeks).
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parent.parent
PANEL_PATH = ROOT / "data" / "processed" / "attention_weekly_panel_v03.csv"
TABLES_DIR = ROOT / "results" / "tables"

HORIZONS = ["future_1w_excess_return", "future_2w_excess_return", "future_4w_excess_return"]
MIN_OBS_BUFFER = 5


def load_panel():
    df = pd.read_csv(PANEL_PATH, parse_dates=["week"])
    df["stock_id"] = df["stock_id"].astype(str)
    return df


def fm_weekly_coefs(panel: pd.DataFrame, horizon: str, continuous: list[str], use_industry_fe: bool):
    records, skipped = [], []
    for week, grp in panel.groupby("week"):
        cols = ["attention_z"] + continuous
        need = cols + [horizon] + (["industry"] if use_industry_fe else [])
        sub = grp[["stock_id"] + need].dropna(subset=cols + [horizon])
        if use_industry_fe:
            dummies = pd.get_dummies(sub["industry"], drop_first=True, dtype=float)
            X = pd.concat([sub[cols].reset_index(drop=True), dummies.reset_index(drop=True)], axis=1)
        else:
            X = sub[cols].reset_index(drop=True)
        X.insert(0, "const", 1.0)
        y = sub[horizon].reset_index(drop=True).to_numpy(dtype=float)
        Xm = X.to_numpy(dtype=float)
        n, k = Xm.shape
        if n < k + MIN_OBS_BUFFER:
            skipped.append({"week": week, "reason": f"insufficient_obs n={n} k={k}"})
            continue
        rank = np.linalg.matrix_rank(Xm)
        if rank < k:
            skipped.append({"week": week, "reason": f"rank_deficient rank={rank} k={k}"})
            continue
        beta, residuals, _, _ = np.linalg.lstsq(Xm, y, rcond=None)
        yhat = Xm @ beta
        ss_res = np.sum((y - yhat) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else None
        attn_idx = list(X.columns).index("attention_z")
        records.append({"week": week, "coef": beta[attn_idx], "n_obs": n, "r2": r2})
    return pd.DataFrame(records), pd.DataFrame(skipped)


def fm_aggregate(coefs: pd.DataFrame, model_name: str, horizon: str):
    if coefs.empty:
        return {"model": model_name, "horizon": horizon, "coefficient": None, "t_stat": None,
                "p_value": None, "n_weeks": 0, "avg_r2": None, "significant": False}
    c = coefs["coef"].dropna()
    n = len(c)
    mean, std = c.mean(), c.std()
    t_stat = mean / (std / np.sqrt(n)) if std and n > 1 else None
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=n - 1)) if t_stat is not None else None
    return {
        "model": model_name, "horizon": horizon, "coefficient": mean, "std_dev": std,
        "t_stat": t_stat, "p_value": p_value, "n_weeks": n,
        "avg_r2": coefs["r2"].mean(), "significant": bool(p_value is not None and p_value < 0.05),
    }


def pooled_two_way_fe(panel: pd.DataFrame, horizon: str, continuous: list[str]):
    """Model 5 fallback: pooled OLS with stock + week fixed effects, SE clustered by week."""
    cols = ["attention_z"] + continuous
    sub = panel[["stock_id", "week"] + cols + [horizon]].dropna(subset=cols + [horizon]).copy()
    sub["stock_id"] = sub["stock_id"].astype(str)
    sub["week_str"] = sub["week"].astype(str)

    formula = f"{horizon} ~ " + " + ".join(cols) + " + C(stock_id) + C(week_str)"
    try:
        model = smf.ols(formula, data=sub)
        result = model.fit(cov_type="cluster", cov_kwds={"groups": sub["week_str"]})
        coef = result.params.get("attention_z")
        t_stat = result.tvalues.get("attention_z")
        p_value = result.pvalues.get("attention_z")
        return {
            "model": "Model5_pooled_2wayFE_cluster_by_week", "horizon": horizon,
            "coefficient": coef, "t_stat": t_stat, "p_value": p_value,
            "n_weeks": sub["week"].nunique(), "n_obs": len(sub), "avg_r2": result.rsquared,
            "significant": bool(p_value is not None and p_value < 0.05),
            "note": "Deviates from per-week Fama-MacBeth: week FE is undefined within a single "
                    "week's cross-section, and per-week stock FE (50 dummies for ~50 obs) leaves "
                    "no residual d.o.f. Estimated instead as a pooled two-way (stock+week) FE panel "
                    "regression with SEs clustered by week (also addresses calendar-clustering).",
        }
    except Exception as e:
        return {"model": "Model5_pooled_2wayFE_cluster_by_week", "horizon": horizon,
                "coefficient": None, "t_stat": None, "p_value": None, "n_weeks": 0,
                "note": f"FAILED: {type(e).__name__}: {e}"}


def main():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    panel = load_panel()

    model_specs = {
        "Model1_attention_only": [],
        "Model2_plus_momentum": ["past_4w_return", "past_12w_return"],
        "Model3_plus_volume_vol": ["past_4w_return", "past_12w_return", "volume_ratio_4w", "volatility_12w"],
        "Model4_plus_liquidity_industry_FE": ["past_4w_return", "past_12w_return", "volume_ratio_4w", "volatility_12w", "liquidity_rank"],
    }

    summary_rows = []
    by_horizon_rows = []

    for model_name, controls in model_specs.items():
        use_fe = model_name.startswith("Model4")
        for horizon in HORIZONS:
            coefs, skipped = fm_weekly_coefs(panel, horizon, controls, use_industry_fe=use_fe)
            agg = fm_aggregate(coefs, model_name, horizon)
            summary_rows.append(agg)
            coefs["model"] = model_name
            coefs["horizon"] = horizon
            by_horizon_rows.append(coefs)
            print(f"{model_name} | {horizon}: coef={agg['coefficient']}, t={agg['t_stat']}, "
                  f"p={agg['p_value']}, n_weeks={agg['n_weeks']}, skipped={len(skipped)}")

    # Model 5: pooled two-way FE fallback
    for horizon in HORIZONS:
        m5 = pooled_two_way_fe(panel, horizon, ["past_4w_return", "past_12w_return", "volume_ratio_4w", "volatility_12w", "liquidity_rank"])
        summary_rows.append(m5)
        print(f"Model5 (pooled 2-way FE) | {horizon}: coef={m5.get('coefficient')}, "
              f"t={m5.get('t_stat')}, p={m5.get('p_value')}")

    pd.DataFrame(summary_rows).to_csv(TABLES_DIR / "v03_fama_macbeth_summary.csv", index=False, encoding="utf-8-sig")
    pd.concat(by_horizon_rows, ignore_index=True).to_csv(TABLES_DIR / "v03_regression_by_horizon.csv", index=False, encoding="utf-8-sig")
    print(f"\nSaved v03_fama_macbeth_summary.csv and v03_regression_by_horizon.csv to {TABLES_DIR}")


if __name__ == "__main__":
    main()
