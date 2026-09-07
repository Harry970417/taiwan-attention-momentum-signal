# Research Findings

Status date: 2026-09-07 (previously 2026-08-02; corrected results below regenerated during
the Phase 1 A-G audit's Finding A-1 fix -- see docs/limitations.md)

## Corrected Finding

Corrected empirical results are now available (`results/tables/*_asof_safe.csv`, all
listed under "Required Evidence" below now exist and are compared in
`asof_safe_legacy_comparison.csv`). Regenerated 2026-09-07 using backward-adjusted close
prices (see `src/price_adjustment.py`) to correct a mechanical negative-return artifact
on ex-dividend dates found in the earlier raw-price version.

Summary (Fama-MacBeth, `future_4w_excess_return`): Model1 (attention only, no controls)
is significant (t=4.17, p<0.0001); adding momentum controls (Model2) removes
significance (t=1.19, p=0.24); Model5 (pooled two-way FE) is significant at the 4-week
horizon only. This is the same significance pattern the pre-fix raw-price numbers
showed -- the price-adjustment correction does not overturn the core conclusion, it only
corrects the return calculation methodology. The core conclusion remains: **the
attention effect is specification-dependent and not robust once momentum is controlled
for** -- see `docs/limitations.md` for the further caveats (survivorship bias in the
50-stock universe; Google Trends query-window normalization covering future search
volume) that this finding should be read under.

**Placebo/lead result investigated and resolved (2026-09-07): not a timing leak.**
`results/tables/robustness_placebo_lead_test.csv` (attention_z[t] vs. weekly_return at
panel row t-1) showed a significant relationship (IC_mean≈0.098, t≈7.7, p<0.001).
Checking the actual calendar dates in the panel showed why: row t-1's weekly_return
window (anchored to feature_asof_trade_date, which already includes the 14-day
conservative availability delay) ends only ~1 day before row t's SVI observation window
*starts* -- the two windows overlap by about 6 of the 7 days in real calendar time
despite the "shift(1)" row-index offset. That overlap alone could explain a significant
correlation without any leak.

To settle it, `scripts/run_corrected_placebo_test.py` reruns the same methodology
against a return window with **zero** calendar overlap -- a trailing 1-week return
ending on the last trading day strictly before observation_period_start(t) (see
`results/tables/robustness_corrected_placebo_lead_test.csv`). The result is
**nearly identical** (IC_mean≈0.099, t≈7.7, p<0.001, n=237 weeks) to the original,
overlapping-window test. Since a genuinely non-overlapping comparison shows the same
significant relationship, this is not an artifact of window overlap or a pipeline
timing defect -- it reflects a real, contemporaneous-to-recent attention/return
relationship (search interest tracking recent price performance is a well-documented
behavioral phenomenon), consistent with this project's own core finding that the
attention signal is entangled with momentum (which is exactly why Model2's momentum
control exists in the first place). This does not change the "specification-dependent,
not robust" conclusion; it's additional evidence for why momentum must be controlled
for, not a validity problem with the as-of-safe pipeline.

## Legacy Finding Status

The old v0.2-v0.4 findings, including positive CAAR, IC/ICIR, Fama-MacBeth coefficients,
sort results, matched-sample results, and institutional-flow controls, are now marked
**superseded / invalidated for predictive interpretation**.

They were generated before the Google Trends weekly availability contract was enforced.
They may be discussed only as uncorrected retrospective associations and must not be cited
as evidence of a real-time tradable predictive strategy.

## Required Evidence Before Restating a Headline Result

The following corrected artifacts must exist and be compared against legacy outputs:

- `results/tables/caar_event_summary_asof_safe.csv`
- `results/tables/v03_fama_macbeth_summary_asof_safe.csv`
- `results/tables/v03_residual_ic_summary_asof_safe.csv`
- `results/tables/v04_regression_with_chips_summary_asof_safe.csv`
- `results/tables/v04_interaction_model_summary_asof_safe.csv`
- `results/tables/asof_safe_legacy_comparison.csv` with status `compared`

All listed artifacts now exist and have been compared (`asof_safe_legacy_comparison.csv`
status: compared). Final classification: **retrospective association study** (not a
real-time tradable predictive strategy) -- not because results are unavailable, but
because of the limitations documented in `docs/limitations.md` (Google Trends query-window
normalization, survivorship bias, unresolved placebo/lead result above).
