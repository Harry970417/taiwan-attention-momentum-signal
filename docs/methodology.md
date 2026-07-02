# Methodology

## 1. Google Trends SVI and the cross-stock scale problem

`pytrends` normalizes every request's keyword(s) to a shared 0–100 scale
*within that request*. Querying 50 stocks one at a time therefore produces
50 series that are not on a common scale. This project batches requests as
[anchor keyword ("台積電 股票")] + [4 other stocks] (Google Trends allows up
to 5 terms per request), then rescales each batch linearly so the anchor's
level matches a reference batch. This is an approximation, not an exact
calibration — see `docs/limitations.md`. Critically, it does **not** affect
the statistical results below, because every test uses a stock's own
self-normalized attention measure (next section), not raw cross-stock SVI
levels.

## 2. Attention factor construction

- `SVI_MA52`, `SVI_STD52`: trailing 52-week mean/std of SVI, per stock.
- `attention_shock = SVI / SVI_MA52 - 1`
- `attention_z = (SVI - SVI_MA52) / SVI_STD52`
- Event flags: `attention_z > 2`, `attention_shock > 1`, or top decile of
  `attention_z` pooled across the whole panel.

## 3. CAAR event study

Event window [-4, +8] weeks. `AR = stock weekly return - TAIEX weekly
return`. A 4-week non-overlap filter keeps only the first event per stock
within any 4-week span. Calendar clustering (how many stocks have an event
in the same week) is explicitly counted and reported, because heavy
clustering means events are not independent draws and ordinary t-tests /
bootstrap CIs likely overstate significance.

## 4. Cross-sectional IC / ICIR

Each week, Spearman-correlate the attention factor across all available
stocks against forward 1/2/4-week excess returns. `ICIR = mean(IC) /
std(IC)`; significance via a one-sample t-test on the weekly IC series.
Weeks with fewer than 10 valid stock observations are skipped and logged.

## 5. Fama-MacBeth regressions

Weekly cross-sectional OLS: `future_excess_return ~ attention_z + controls`,
run independently each week, then the attention_z coefficient's time
series is aggregated (mean, std, Fama-MacBeth t-stat = mean / (std /
sqrt(T))). Controls added progressively: momentum (past 4w/12w return) →
volume/volatility → liquidity + industry fixed effects → institutional
flow. Where a literal per-week fixed-effects specification is not
well-posed (e.g., "week fixed effects" inside a single week's
cross-section, which has no time variation to identify), the model is
instead estimated as a pooled two-way (stock + week) fixed-effects panel
regression with standard errors clustered by week — this also directly
addresses the calendar-clustering concern above.

## 6. Residual attention factor

Each week, regress `attention_z` on
`[past_4w_return, past_12w_return, volume_ratio_4w, volatility_12w,
liquidity_rank]` cross-sectionally; keep the residual as
`residual_attention_z`. Re-run IC/ICIR and CAAR on this residual to see
what, if anything, survives after linearly stripping out the observable
confounders.

## 7. Double / triple sort

Independent terciles within each week's cross-section:
- Double sort: `past_4w_return` (loser/neutral/winner) × `attention_z`
  (low/mid/high).
- Triple sort: adds `total_inst_net_buy_ratio_4w` (institutional
  selling/neutral/buying) as a third dimension.

This non-parametric approach can reveal threshold/non-linear conditional
effects that a linear interaction term in a regression would miss (and, in
this project, did miss — see `docs/limitations.md`).

## 8. Matched-sample event study

For each `attention_z > 2` event, find the nearest non-event stock in the
same week (standardized distance on past 4w/12w return, volume ratio, and
volatility; same industry preferred when at least 3 same-industry
candidates exist). Compare the event stock's forward excess return to its
matched control's. This isolates the attention effect from observable
momentum/volume/volatility confounders without assuming a linear
functional form.

## 9. Institutional flow control

FinMind's free institutional-investor dataset reports daily buy/sell in
**shares** (not NTD value) for five categories: Foreign_Investor,
Investment_Trust, Dealer_self, Dealer_Hedging, Foreign_Dealer_Self. These
are aggregated into foreign / trust / dealer / total net-share-bought
series, rolled up to 1-week and 4-week trailing sums, and converted to
volume-normalized ratios (net shares bought ÷ total shares traded over the
same window) for cross-stock comparability. These ratios are added as
regression controls (Fama-MacBeth Models B–E) and as a third sorting
dimension (triple sort).
