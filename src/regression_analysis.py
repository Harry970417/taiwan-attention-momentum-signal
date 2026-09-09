"""TAS v0.4 Phase 4: does institutional flow explain away the attention_z
effect, and is the momentum/chip interaction significant?

Fama-MacBeth weekly cross-sectional regressions, Models A-E, using the
v0.4 panel (institutional-flow-augmented).
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from asof_contract import assert_no_lookahead_panel

ROOT = Path(__file__).resolve().parent.parent
PANEL_PATH = ROOT / "data" / "processed" / "attention_weekly_panel_v04_asof_safe.csv"
TABLES_DIR = ROOT / "results" / "tables"

HORIZONS = ["future_1w_excess_return", "future_2w_excess_return", "future_4w_excess_return"]
MIN_OBS_BUFFER = 5


def load_panel():
    df = pd.read_csv(PANEL_PATH, parse_dates=["week"])
    df["stock_id"] = df["stock_id"].astype(str)
    assert_no_lookahead_panel(df)
    return df


def build_design(sub: pd.DataFrame, terms: list):
    """terms: list of column names or (a, b) tuples for a*b interaction."""
    cols = {}
    names = []
    for t in terms:
        if isinstance(t, tuple):
            name = f"{t[0]}_x_{t[1]}"
            cols[name] = sub[t[0]] * sub[t[1]]
        else:
            name = t
            cols[name] = sub[t]
        names.append(name)
    X = pd.DataFrame(cols)
    return X, names


def fm_weekly(panel: pd.DataFrame, horizon: str, terms: list):
    base_cols = [t for t in terms if not isinstance(t, tuple)]
    records, skipped = [], []
    for week, grp in panel.groupby("week"):
        need = list(set(base_cols + [horizon]))
        sub = grp.dropna(subset=need)
        if sub.empty:
            skipped.append({"week": week, "reason": "no data"})
            continue
        X, names = build_design(sub, terms)
        X = X.dropna()
        sub = sub.loc[X.index]
        X.insert(0, "const", 1.0)
        y = sub[horizon].to_numpy(dtype=float)
        Xm = X.to_numpy(dtype=float)
        n, k = Xm.shape
        if n < k + MIN_OBS_BUFFER:
            skipped.append({"week": week, "reason": f"insufficient_obs n={n} k={k}"})
            continue
        if np.linalg.matrix_rank(Xm) < k:
            skipped.append({"week": week, "reason": "rank_deficient"})
            continue
        beta, *_ = np.linalg.lstsq(Xm, y, rcond=None)
        yhat = Xm @ beta
        ss_res = np.sum((y - yhat) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else None
        rec = {"week": week, "n_obs": n, "r2": r2}
        for name in names:
            idx = list(X.columns).index(name)
            rec[name] = beta[idx]
        records.append(rec)
    return pd.DataFrame(records), pd.DataFrame(skipped)


def fm_aggregate(coefs: pd.DataFrame, colname: str):
    """2026-09-09: migrated to quant_formulas' Newey-West HAC standard error
    (Desktop/quant-system-core), same fix and same reason as
    momentum_control.fm_aggregate -- see that function's docstring."""
    from quant_formulas.factor_stats import newey_west_se, t_stat_and_pvalue

    if coefs.empty or colname not in coefs.columns:
        return {"coefficient": None, "t_stat": None, "p_value": None, "n_weeks": 0, "significant": False}
    c = coefs[colname].dropna()
    n = len(c)
    if n < 2:
        return {"coefficient": None, "t_stat": None, "p_value": None, "n_weeks": n, "significant": False}
    mean = c.mean()
    se = newey_west_se(c)
    t_stat, p_value = t_stat_and_pvalue(mean, se, df=n - 1) if se > 0 else (None, None)
    return {"coefficient": mean, "t_stat": t_stat, "p_value": p_value, "n_weeks": n,
            "significant": bool(p_value is not None and p_value < 0.05)}


def main():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    panel = load_panel()

    models = {
        "A_attention_momentum": ["attention_z", "past_4w_return", "past_12w_return"],
        "B_plus_total_inst_flow": ["attention_z", "past_4w_return", "past_12w_return", "total_inst_net_buy_ratio_4w"],
        "C_plus_foreign_trust_dealer": ["attention_z", "past_4w_return", "past_12w_return",
                                         "foreign_net_buy_ratio_4w", "trust_net_buy_ratio_4w", "dealer_net_buy_ratio_4w"],
        "D_plus_volume_volatility": ["attention_z", "past_4w_return", "past_12w_return",
                                      "total_inst_net_buy_ratio_4w", "volume_ratio_4w", "volatility_12w"],
    }
    model_e_terms = ["attention_z", "past_4w_return", "past_12w_return", "total_inst_net_buy_ratio_4w",
                      ("attention_z", "past_4w_return"), ("attention_z", "total_inst_net_buy_ratio_4w")]

    summary_rows = []
    for model_name, terms in models.items():
        for horizon in HORIZONS:
            coefs, skipped = fm_weekly(panel, horizon, terms)
            agg = fm_aggregate(coefs, "attention_z")
            agg.update({"model": model_name, "horizon": horizon,
                        "avg_r2": coefs["r2"].mean() if not coefs.empty else None,
                        "n_weeks_skipped": len(skipped)})
            summary_rows.append(agg)
            print(f"{model_name} | {horizon}: attention_z coef={agg['coefficient']}, "
                  f"t={agg['t_stat']}, p={agg['p_value']}, n_weeks={agg['n_weeks']}")

    pd.DataFrame(summary_rows).to_csv(TABLES_DIR / "v04_regression_with_chips_summary_asof_safe.csv", index=False, encoding="utf-8-sig")

    # Model E: interaction terms
    interaction_rows = []
    for horizon in HORIZONS:
        coefs, skipped = fm_weekly(panel, horizon, model_e_terms)
        for var in ["attention_z", "attention_z_x_past_4w_return", "attention_z_x_total_inst_net_buy_ratio_4w",
                    "total_inst_net_buy_ratio_4w"]:
            agg = fm_aggregate(coefs, var)
            agg.update({"horizon": horizon, "term": var, "avg_r2": coefs["r2"].mean() if not coefs.empty else None,
                        "n_weeks_skipped": len(skipped)})
            interaction_rows.append(agg)
            print(f"Model E | {horizon} | {var}: coef={agg['coefficient']}, t={agg['t_stat']}, p={agg['p_value']}")

    pd.DataFrame(interaction_rows).to_csv(TABLES_DIR / "v04_interaction_model_summary_asof_safe.csv", index=False, encoding="utf-8-sig")
    print(f"\nSaved v04_regression_with_chips_summary_asof_safe.csv and v04_interaction_model_summary_asof_safe.csv")


if __name__ == "__main__":
    main()
