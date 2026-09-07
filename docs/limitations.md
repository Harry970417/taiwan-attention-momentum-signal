# Limitations

## Corrected Results Regenerated (updated 2026-09-07)

As of 2026-08-31, `data/raw/` and `data/processed/` contain real inputs and the corrected
`results/tables/*_asof_safe.csv` outputs have been regenerated from them (this note
previously said, as of 2026-08-02, that they were not yet available -- that was accurate
at the time but is now stale; corrected here during the 2026-09-07 Phase 1 audit).

## Google Trends Query Window Normalization Covers Future Search Volume

`trends_collector.py` fetches each 5-year sample window (`RESEARCH_SAMPLE_START` to
`RESEARCH_SAMPLE_END`) in a single `pytrends` query per batch. Google Trends internally
normalizes and rounds its 0-100 index against the peak search volume found *anywhere in
the queried window* -- so a 2022 weekly value's rounding/normalization basis can be set by
search activity that happened years later, in 2025-2026. Because the index is an integer
(not a continuous value), this is not fully cancelled out by this project's own
within-stock `attention_z` standardization, which is a linear rescaling and therefore
invariant to a *continuous* rescaling of the underlying series but not to Google's integer
rounding, whose breakpoints depend on where the window's peak falls. This means the
question "what would this signal have looked like if queried live in 2022" cannot be
answered from this data; results should be read strictly as a retrospective association
study using data collected in 2026, not as a reconstruction of what a real-time investor
would have observed at the time. The existing repeat-query stability check
(`tmp/gtrends_repeat_query_test.py`) only verifies short-term, same-session sampling
stability for a 1-year window and does not test or rule out this window-normalization
effect, nor cross-batch drift across queries run hours/days apart.

## 50-Stock Universe Selected From Currently-Alive Constituents (Survivorship Bias)

The 50-stock universe (`config/stock_list_50.csv`) was selected using large-cap/index
membership information available near data-collection time (2026), and the pipeline
(`assert_complete_universe_coverage`) requires every stock to have a complete 2022-2026
history or the run fails outright. This means any company that was delisted, was
acquired, or fell out of large-cap status during the 2022-2026 sample period is excluded
from the study -- a standard survivorship-bias mechanism that can systematically
understate how poorly underperforming names actually did, and could bias the estimated
attention x momentum interaction. (Note: `assert_complete_universe_coverage`'s "refusing
to write a partial survivor universe" error message guards against a different problem --
quietly dropping stocks *after* seeing results look worse with them included -- not
against this selection-stage bias. Both matter, but they are separate issues.) Results
should not be read as describing a portfolio that could have been assembled and held from
2022 using only information available at that time.

## Google Trends Historical Publication Time Unknown

This project cannot prove the historical publication timestamp of each Google Trends
weekly bucket. The corrected pipeline therefore applies a conservative full-week delay.
Until this assumption is validated with a stronger data source, the project should be
described as a retrospective association study, not a real-time tradable predictive
strategy.

## Google Trends Scale And Sampling

Google Trends SVI is normalized, sampled, and indexed. Cross-request values are not exact
common-scale volumes. The project uses self-normalized `attention_z` and
`attention_shock`, but Trends sampling noise and low-volume zeros remain limitations.

## Data Scope

The intended universe is 50 Taiwan large-cap stocks. Results should not be extrapolated to
small caps, TPEx, non-Taiwan markets, or future periods without separate validation.

## Institutional Data Unit

FinMind's free institutional-investor data reports shares, not NTD value. Columns with
`value` in their historical names are share counts unless renamed in a future schema.

## Not Investment Advice

Nothing in this repository is a recommendation to buy, sell, or hold securities. No
transaction costs, slippage, market impact, short-sale constraints, or live execution
constraints are modeled.
