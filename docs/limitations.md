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

## Google Trends Scale And Sampling (Measurement Audit, 2026-09-13)

Each Google Trends request returns a 0-100 index normalized **within that single
request's query window** (its own set of up to 5 keywords, over the fixed
`RESEARCH_SAMPLE_START`-`RESEARCH_SAMPLE_END` timeframe) -- Google does not expose a
cross-request common scale. `trends_collector.py` queries batches of `[anchor keyword] +
[4 stocks]`, always including the same anchor ("台積電 股票"), and rescales the 4
non-anchor stocks in each batch so the anchor's mean level matches its solo-query
reference mean. This gives an **approximate common scale across all 50 stocks' raw SVI
levels** (used only for dashboard/plot display, e.g. `results/tables/google_trends_test_result_50.csv`
and the SVI overlay figures) -- it is not exact, since Google's underlying index is not
provably linear/additive near saturation, and it is not required for any inferential
result in this project.

**No inferential result in this project compares raw SVI levels across stocks.**
`attention_z` and `attention_shock` are each computed from a single stock's own SVI
series against its own trailing 52-week mean/std (see "attention_z Is a Within-Stock
Score" below) -- they never divide or compare one stock's raw 0-100 value against
another's. The one place a cross-stock comparison happens at all is
`attention_top_decile` (event_study.py), which ranks each week's **already-standardized**
`attention_z` values across stocks to find the 90th percentile -- comparing per-stock
z-scores (unit-free by construction) is a materially weaker claim than comparing raw
Google Trends 0-100 levels, but it is still a comparison across stocks whose underlying
52-week baselines and volatilities differ, so it is not a claim that stocks are on a
literally identical measurement scale either. Trends sampling noise and low-volume zeros
remain limitations regardless of scaling.

## `attention_z` Is a Within-Stock Score, Not a Cross-Stock Ranking

`attention_z = (SVI - SVI_MA52) / SVI_STD52` is a **within-stock, trailing-52-week
time-series z-score** -- it measures how unusual this week's search interest is relative
to *that same stock's own* recent history, not how this stock's attention compares to the
other 49 stocks in the panel this week. All Model1-5 Fama-MacBeth/panel regressions use
this within-stock score as the independent variable, not a raw SVI level or a weekly
cross-sectional rank. The weekly cross-sectional comparison in those regressions is
therefore over *each stock's own-history abnormal-attention score*, not over each stock's
absolute attention level -- consistent with the Da/Engelberg/Gao (2011)-style Abnormal
Search Volume Index convention in the literature, not a project-specific design choice.
This distinction matters for interpreting the coefficient: a positive `attention_z`
coefficient means "weeks where a stock is unusually attention-grabbing *relative to its
own history* tend to have higher forward returns," not "the most-searched stock in a
given week tends to have higher forward returns."

## Momentum Control Covers Only 1-Month and 3-Month Windows (M1-M5 Headline Models)

The momentum control variables used in Model2-5 are `past_4w_return` (~1 month) and
`past_12w_return` (~3 months) only -- both simple close-to-close returns with **no skip
period**, ending at `feature_asof_trade_date`. This project does **not** control for
Jegadeesh-Titman canonical 12-1 momentum (12-month return skipping the most recent month)
or market-adjusted momentum (the momentum controls are individual-stock raw returns, not
returns net of the market) within M1-M5 itself. Any portfolio text describing this as
"controlling for momentum" must say "controlling for this project's specific 1-month and
3-month trailing-return proxies," not "controlling for momentum" unqualified -- the latter
implies canonical momentum has been ruled out, which it has not been within M1-M5.

**Canonical momentum robustness check (added 2026-09-13).** `momentum_control.py`'s
`canonical_momentum_robustness()` re-runs the univariate attention_z Fama-MacBeth
regression controlling, one at a time, for five pre-registered proxies: `past_4w_return`
(1-month), `past_12w_return` (3-month), `past_26w_return` (6-month), a new
`past_52w_skip4w_return` (12-1 month momentum, skipping the most recent ~4 weeks), and
`past_1w_return` (short-term reversal). All five are reported regardless of outcome (see
`results/tables/canonical_momentum_robustness_asof_safe.csv`) -- this is not a search over
specifications until one leaves attention significant.

## Data Scope

The intended universe is 50 Taiwan large-cap stocks. Results should not be extrapolated to
small caps, TPEx, non-Taiwan markets, or future periods without separate validation.

## Event-Study Inference: Calendar Clustering Corrected (2026-09-13)

Attention-shock events cluster heavily in calendar time (many stocks spike in the same
week on common market-wide news), so a plain per-event t-test on final-window CAR
overstates significance -- same-week events are not independent draws, and forward-return
windows overlap across nearby signal weeks. `event_study.py` now reports two statistics
for each of the 3 CAAR definitions: `t_stat_naive` (kept for transparency, likely
overstated) and `t_stat_date_clustered_hac` (authoritative), which collapses same-week
events into one weekly-portfolio CAR observation and runs a Newey-West HAC t-test across
that weekly series -- the same estimator used for every Fama-MacBeth model (M1-M5). Only
`t_stat_date_clustered_hac` / `p_value_date_clustered_hac` feed the FDR correction and any
significance claim in the portfolio write-up.

## Institutional Flow Scaling

FinMind's free institutional-investor data reports shares, not NTD value. Columns with
`value` in their historical names (pre-2026-09-13) are share counts, not monetary value.
As of 2026-09-13, `institutional_flow.py` also computes `*_net_buy_ntd_value_4w`
(net shares x that week's close price, an approximate monetary-flow proxy) and
`regression_analysis.py` reports the attention_z coefficient under three institutional-
flow control specifications side by side (`results/tables/v04_institutional_flow_scaling_sensitivity_asof_safe.csv`):
raw share counts, the NTD-value approximation, and the volume-scaled ratio (net shares /
trading volume, the pre-existing and primary specification). Market-cap-scaled flow
(net_buy_value / market_cap) is **not implemented**: no reliable market-cap or
shares-outstanding series is available from the FinMind free tier this project uses, and
approximating market cap from price alone (without a real share count) would silently
misstate float rather than genuinely control for firm size. This is a disclosed
measurement limitation, not a completed feature.

## Rolling-Window Stability Chart Specification

The 52-week rolling stability chart (`results/figures/robustness_rolling_window_4w.png`,
`tas_rolling_window_stability.png`) plots the **Model1 (attention-only, no momentum
control)** univariate Fama-MacBeth `attention_z` coefficient at the **4-week
(`future_4w_excess_return`) horizon**, with a **Newey-West HAC** standard error on each
52-week rolling window (migrated 2026-09-13 off the previous naive std/sqrt(n) formula,
for consistency with the M1-M5 headline estimator). Because this is Model1, it shows the
*uncontrolled* attention-return relationship's stability over time, not the
momentum-controlled one -- the chart title and a subtitle state the model, attention
measure, horizon, and covariance estimator explicitly so this cannot be conflated with a
momentum-controlled result.

## Multiple Testing

See `MULTIPLE_TESTING_FAMILY_CONTRACT.md` at the repo root for the authoritative
definition of the 30-test family corrected together (3 event-study + 15 regression + 12
interaction), reported at both BH-FDR q=0.10 and q=0.05, plus a secondary
per-family sensitivity check.

## M1-M5 Estimator Naming

M1-M4 are Fama-MacBeth (per-week cross-sectional OLS, coefficients aggregated across
weeks) with a Newey-West HAC standard error on that time series. M5 is a pooled two-way
(stock + week) fixed-effects panel regression with standard errors **clustered by week**
-- this is a distinct estimator from M1-M4 and must never be called "Newey-West HAC" or
folded into "the Fama-MacBeth models" in prose; write "M1-M4 Fama-MacBeth + NW-HAC" and
"M5 two-way FE, cluster-by-week SE" as two separate items, e.g. when describing the
30-test family as "15 regression specifications (M1-M4 Fama-MacBeth + M5 two-way FE)."

## Not Investment Advice

Nothing in this repository is a recommendation to buy, sell, or hold securities. No
transaction costs, slippage, market impact, short-sale constraints, or live execution
constraints are modeled.
