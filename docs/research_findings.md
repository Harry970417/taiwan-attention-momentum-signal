# Research Findings

Status date: 2026-09-09 (previously 2026-08-02, then 2026-09-07; corrected results below
regenerated twice during the Phase 1 A-G audit -- Finding A-1's price adjustment, then
the Newey-West HAC migration below -- see docs/limitations.md)

## Corrected Finding

Corrected empirical results are now available (`results/tables/*_asof_safe.csv`, all
listed under "Required Evidence" below now exist and are compared in
`asof_safe_legacy_comparison.csv`). Regenerated 2026-09-07 using backward-adjusted close
prices (see `src/price_adjustment.py`) to correct a mechanical negative-return artifact
on ex-dividend dates found in the earlier raw-price version, then regenerated again
2026-09-09 after migrating `momentum_control.fm_aggregate`, `regression_analysis.
fm_aggregate`, and `momentum_control.factor_ic_summary` off their naive (non-HAC)
significance tests onto `quant_formulas` (`Desktop/quant-system-core`'s canonical
Newey-West HAC implementation) -- closing this repo's own Finding C-2/P1-19 (zero
Newey-West/HAC implementation anywhere, despite the 1/2/4-week overlapping forward-return
windows this project's own design uses inducing serial correlation).

Summary (Fama-MacBeth, `future_4w_excess_return`, HAC-corrected): Model1 (attention only,
no controls) has an individual-test HAC p-value of 0.016 (t=2.43), visibly weaker than
the pre-HAC t=4.17; Model1 at the 1-week horizon is **not significant at conventional
levels** post-HAC (t=1.91, p=0.057); adding momentum controls (Model2) removes
significance entirely (t=0.79, p=0.43); Model5 (pooled two-way FE, cluster-by-week SE)
has an individual-test p-value of 0.006 (t=2.73) at the 4-week horizon only. **Model1-4's
t-statistics come from the Fama-MacBeth time-series test (HAC-corrected); Model5's
t-statistic comes from a week-clustered robust standard error in a single pooled panel
regression -- these are two different covariance estimators and are not directly
comparable in significance strength against each other, despite appearing in the same
summary table.**

**After the 2026-09-13 event-study date-clustering fix (see below), re-running BH-FDR
across the pooled 30-test family materially changes which of these individual-test
results survive multiple-testing correction.** Feeding FDR the naive (uncorrected)
event-study p-values had previously let 5-6 of 30 tests survive, including Model1 at the
4-week horizon; those naive p-values were themselves too small (overstating
significance from same-week event clustering), which distorted the whole family's
BH ranking. With the corrected, date-clustered event-study p-values now feeding the same
family: **only 2 of 30 tests survive BH-FDR at q=0.10** -- the `attention_ratio`
event-study CAAR (p_fdr=0.030) and Model5 at the 4-week horizon (p_fdr=0.094, i.e. only
barely under 0.10) -- and **only 1 of 30 survives at q=0.05** (the event-study result;
Model5 does not). **Model1 is no longer FDR-significant at any horizon, at either q
level, once the event-study family is corrected for calendar clustering.** See
`results/tables/fdr_correction_all_tests_asof_safe.csv` and
`MULTIPLE_TESTING_FAMILY_CONTRACT.md`.

This correction makes the already-cautious "specification-dependent, not robust"
conclusion **more conservative across the board, never less** -- it does not overturn
anything, it removes findings that were only ever marginally significant under
under-corrected tests. The core conclusion is now stronger, not weaker: **after
correcting data timing, calendar-clustering in the event study, and testing attention_z
against every canonical momentum window (see below), the predictive evidence for
attention is highly dependent on specification, horizon, and sample period; it is not
sufficient to establish a robust, independent attention premium** -- see
`docs/limitations.md` for the further caveats (survivorship bias in the 50-stock
universe; Google Trends query-window normalization covering future search volume) that
this finding should be read under.

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

## Event-Study Inference: Calendar-Clustering Correction (2026-09-13)

The three CAAR event-study tests (`attention_z2`, `attention_ratio`, `attention_top_decile`)
previously reported only a naive per-event t-test, which treats every event as an
independent draw despite heavy calendar clustering (many stocks spike attention the same
week on common market-wide news) and overlapping forward-return windows across nearby
signal weeks. `event_study.py` now also reports a date-clustered, Newey-West HAC t-test:
same-week events are first collapsed into one weekly-portfolio CAR observation, then
NW-HAC is run on that weekly series (the same estimator as M1-M5). Regenerated
2026-09-13 (`results/tables/caar_event_summary_asof_safe.csv`):

| Event definition | n events (after filter) | n calendar weeks | naive t | naive p | **date-clustered HAC t** | **date-clustered HAC p** |
|---|---:|---:|---:|---:|---:|---:|
| attention_z2 | 388 | 148 | 4.076 | <0.001 | **2.284** | **0.024** |
| attention_ratio | 498 | 184 | 5.607 | <0.001 | **3.346** | **0.001** |
| attention_top_decile | 664 | 225 | 3.838 | <0.001 | **2.347** | **0.020** |

All three remain significant at conventional levels (p<0.05) individually, even after
collapsing same-week correlation, though the effective t-statistics roughly halve
relative to the naive test -- confirming the naive test was overstating significance, as
flagged, without fully explaining away the underlying CAAR pattern. After pooling into
the 30-test FDR family (see Multiple Testing below), only `attention_ratio` survives at
both q=0.10 and q=0.05; `attention_z2` and `attention_top_decile` do not survive FDR
correction once pooled with the other 27 tests, despite being individually significant.

## Canonical Momentum Robustness (2026-09-13)

M1-M5 only ever control for `past_4w_return` (1-month) and `past_12w_return` (3-month).
`momentum_control.canonical_momentum_robustness()` checks the univariate attention_z
coefficient (Fama-MacBeth + NW-HAC, same estimator as M1) against five pre-registered
momentum/reversal proxies one at a time -- 1-month, 3-month, 6-month (`past_26w_return`),
12-1 month (`past_52w_skip4w_return`, skipping the most recent ~4 weeks), and short-term
(1-week) reversal (`past_1w_return`) -- all reported regardless of outcome, not searched
until one leaves attention significant. Full table:
`results/tables/canonical_momentum_robustness_asof_safe.csv`.

At the 4-week horizon (baseline, no momentum control: t=2.434, p=0.016): controlling for
1-month return drops it to t=1.62 (p=0.11); 3-month to t=1.28 (p=0.20); 6-month to t=1.74
(p=0.08); 12-1 month to t=1.90 (p=0.06) -- **attention_z loses significance at
conventional levels under every one of the four momentum definitions tested**, not just
the two (1-month, 3-month) already used in M1-M5. It survives only the short-term
(1-week) reversal control (t=2.28, p=0.023) -- reversal and momentum are conceptually
different controls, so this is not evidence against the "momentum explains it away"
finding. This strengthens rather than narrows the existing conclusion: the earlier
limitation ("only tested against 1-month/3-month windows") no longer applies, and the
fragility to momentum controls generalizes across window definitions.

## Institutional Flow Scaling Sensitivity (2026-09-13)

The institutional-flow control was previously only available as raw net share counts
(mislabeled `*_value_*`) or a volume-scaled ratio. `regression_analysis.py` now reports
the attention_z coefficient side by side under three flow specifications -- raw shares,
an approximate NTD-value flow (net shares x that week's close price), and the existing
volume-scaled ratio -- in
`results/tables/v04_institutional_flow_scaling_sensitivity_asof_safe.csv`. At the 4-week
horizon: raw shares t=0.92 (p=0.36), NTD-value approx t=0.67 (p=0.50), volume-scaled
ratio t=0.86 (p=0.39) -- attention_z is non-significant under all three, and the choice
of flow scaling changes the conclusion for none of them. This is a clean robustness
result: the earlier "measured in shares, not value" limitation is resolved by showing it
doesn't matter to the conclusion, not by asserting it doesn't matter. Market-cap-scaled
flow is not implemented (no reliable market cap data from the FinMind free tier; see
`docs/limitations.md`).

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
