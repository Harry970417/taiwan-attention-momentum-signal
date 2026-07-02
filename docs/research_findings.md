# Research Findings

## v0.2 — Initial attention effect (naive)

- 50/50 stocks successfully collected (Google Trends + FinMind), near-0%
  missing data.
- CAAR (`attention_z>2` events, n=377 after non-overlap filter): CAR@+8w =
  **+14.2%**, t=8.46, p<0.0001. Pattern is momentum, not reversal — CAAR
  was already rising for 4 weeks *before* the event.
- IC/ICIR (`attention_z`): ICIR ≈ 0.31 (1w), decaying mildly to 0.31→0.23
  across `attention_shock` at 4w. Positive-IC-week ratio ~62–64%.
- Group split by past 4-week return: past winners CAR@+8w = **+30.8%**
  (t=12.6, p≈1e-26); past non-winners CAR@+8w = **-1.1%** (t=-0.68,
  **p=0.50, not significant**). This is the first sign the effect might be
  momentum-driven.
- Backtest: excluding high-attention stocks from a 50-stock equal-weight
  portfolio *reduced* total return (140% vs 223% over 236 weeks) and
  Sharpe-like ratio (1.13 vs 1.43) — consistent with high-attention stocks
  being winners, not bubbles.

Full detail: [`../reports/TAS_v0.2_Result_Snapshot.md`](../reports/TAS_v0.2_Result_Snapshot.md)

## v0.3 — Momentum control

- Correlation: `attention_z` vs `past_8w_return` r=0.315, vs
  `past_12w_return` r=0.305 — moderate, not high collinearity.
- Fama-MacBeth: attention_z coefficient shrinks from 0.0039 (attention-only)
  to 0.0025 (+momentum controls) — **~36% shrinkage** — but remains
  significant (p<0.001) through Models 1–3 and the corrected Model 5
  (pooled two-way FE, cluster-robust by week). Model 4 (industry fixed
  effects) is unreliable: 30 industries for 50 stocks means most industries
  have 1–2 members, producing an implausible R²≈0.89 (overfitting artifact,
  not genuine explanatory power).
- Residual-factor IC (after removing momentum/volume/volatility/liquidity):
  significant at 1 week (IC=0.036, p=0.0004) and 2 weeks (IC=0.027,
  p=0.0049), but **not significant at 4 weeks** (IC=0.008, p=0.38).
- Double sort (past 4w return × attention_z): future 4w excess return in
  the winner+high-attention cell is **+3.28%**, vs -0.15% in
  winner+low-attention, and near-zero across the entire loser row. Effect
  strength is monotonically increasing in past momentum.
- Matched-sample event study (695 events matched on momentum/volume/
  volatility, 14.8% same-industry match rate): event stocks still beat
  matched controls by **+1.71% / +2.43% / +3.74%** at 1w/2w/4w (all
  p<0.0001), and the gap **grows** with horizon — in tension with the
  residual-IC result above, interpreted as evidence the true relationship
  is a non-linear momentum interaction that linear residualization
  partially removes.

Full detail: [`../reports/TAS_v0.3_Momentum_Control_Report.md`](../reports/TAS_v0.3_Momentum_Control_Report.md)

## v0.4 — Institutional flow control

- Correlation: `attention_z` vs any institutional net-buy ratio maxes out
  at **r=0.054** (foreign, 4-week), far below its correlation with momentum
  (r=0.277).
- Fama-MacBeth with institutional-flow controls: attention_z coefficient
  moves from 0.00250 (momentum-only) to 0.00247 (+total institutional flow)
  — **~1% shrinkage**, versus 36% shrinkage when momentum was added in
  v0.3. Remains significant (p<0.001) whether foreign/trust/dealer flows
  are added separately (Model C) or combined with volume/volatility
  (Model D).
- Interaction terms (Model E): `attention_z × past_4w_return` and
  `attention_z × total_inst_net_buy_ratio_4w` are **not** statistically
  significant (p=0.35–0.93) at any horizon, even though the double/triple
  sorts show a clear conditional pattern — see `limitations.md` for the
  interpretation of this discrepancy.
- Triple sort (momentum × attention × institutional flow), winner bucket,
  future 4w excess return: inst-selling **+2.99%**, inst-neutral **+4.45%**,
  inst-buying **+2.51%** — high attention works in the winner bucket
  *regardless* of institutional flow direction, directly contradicting an
  institutional-flow explanation.
- Strategy-group comparison (research comparison, not a tradable
  backtest): momentum+attention (G2) clearly outperforms both pure momentum
  (G1) and momentum+institutional-flow (G3, which barely beats G1);
  stacking institutional flow on top of momentum+attention (G4) adds no
  further benefit and increases drawdown.

Full detail: [`../reports/TAS_v0.4_Final_Research_Interpretation.md`](../reports/TAS_v0.4_Final_Research_Interpretation.md)

## Final classification

**B — Conditional Momentum Amplifier.** Not an independent alpha factor (A);
not primarily an institutional-flow proxy (C, explicitly ruled out in
v0.4); not pure noise after controls (D, ruled out — a residual effect
survives most tests). The attention signal has genuine incremental
information, but its predictive power is conditional on the stock already
exhibiting positive momentum, and this conditioning is not explained by
institutional trading flow.
