# Limitations

## Google Trends cross-stock scale

`pytrends` normalizes each request to a 0–100 scale within that request, so
raw SVI values from separately-queried stocks are not directly comparable.
This project batches 4 stocks + a shared anchor keyword ("台積電 股票") per
request and linearly rescales using the anchor's level relative to a
reference batch. This is an **approximation**: Google's underlying
normalization is not guaranteed to be linear near saturation, so the
rescaled cross-stock levels should be treated as directionally informative,
not exact. This limitation does **not** affect the core statistical
findings, because every hypothesis test (CAAR, IC, regressions, sorts,
matching) uses each stock's own self-normalized `attention_z` /
`attention_shock` (built from that stock's own trailing 52-week history),
never raw cross-stock SVI levels.

## Sample size and scope

- 50 large-cap TWSE stocks only (roughly 0050-index-style universe). Do
  **not** extrapolate to small-caps, mid-caps, the full TWSE/TPEx market,
  or non-Taiwan markets.
- Sample period is 2021-06 to 2026-06 (Google Trends, weekly) and 2021-01
  to 2026-07 (FinMind, daily) — a period that is momentum/bull-market-heavy
  for Taiwanese semiconductor and electronics names. Results are not tested
  across a full bear-market cycle.
- 30 industries are represented across 50 stocks, with most industries
  having only 1–2 members. This makes industry-fixed-effects regressions
  (Fama-MacBeth Model 4 in v0.3) unreliable — the reported R²≈0.89 for that
  model is an overfitting artifact, not genuine explanatory power, and its
  loss of significance at the 1-week horizon should not be read as
  evidence against the effect.

## Institutional-flow data unit

FinMind's free-tier `TaiwanStockInstitutionalInvestorsBuySell` dataset only
provides buy/sell in **shares**, not NTD monetary value. Every
`*_net_buy_value_*` column in this project is therefore a **share count**,
not a currency amount — the "value" naming is kept only for consistency
with the original variable specification and should not be read as NTD.
Ratio columns (`*_net_buy_ratio_*`) divide net shares by total shares
traded over the same window, which is unit-free and safe to compare across
stocks of different sizes.

## Linear interaction vs. non-linear conditioning

Fama-MacBeth Model E tested linear interaction terms
(`attention_z × past_4w_return`, `attention_z × total_inst_net_buy_ratio_4w`)
and found neither statistically significant (p=0.35–0.93 across horizons).
This is in tension with the double-sort and triple-sort results, which show
a clear and large conditional pattern concentrated in the "winner"
momentum tercile. The most likely explanation is that the true
attention-momentum relationship is **threshold/non-linear** (a large jump
once a stock crosses into the top momentum tercile) rather than a smooth
linear product — a specification that a simple interaction term cannot
capture. This discrepancy is reported explicitly rather than resolved by
picking whichever method gives a cleaner story; readers should weight the
non-parametric sort/matching evidence more heavily than the linear
interaction test for this particular question.

## Statistical significance under calendar clustering

Attention-shock events cluster heavily in calendar time — in some weeks,
up to 16–26 of the 50 stocks trigger an event simultaneously (see the CAAR
event summary tables). This means events are not independent draws.
Ordinary t-tests and simple bootstrap confidence intervals (used for the
CAAR and matched-sample tests) do not correct for this cross-sectional
correlation and likely overstate statistical significance to some degree.
The Fama-MacBeth / pooled two-way fixed-effects regressions with
week-clustered standard errors partially address this for the regression
results, but the event-study and matched-sample p-values should be read as
directionally informative rather than exact.

## Not investment advice, not a tradable strategy

- No transaction costs, slippage, market impact, or short-sale constraints
  are modeled anywhere in this project (Taiwan has meaningful restrictions
  on short-selling that are not simulated).
- The "strategy group comparison" in v0.4 is an explicitly research-only
  cross-sectional return comparison, not a backtested trading strategy.
- Nothing in this repository should be interpreted as a recommendation to
  buy, sell, or hold any security.
