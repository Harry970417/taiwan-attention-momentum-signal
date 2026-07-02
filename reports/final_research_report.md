# Attention Meets Momentum: Final Research Report

## 1. Abstract

We test whether Google search-volume spikes ("attention shocks") predict
short-term (1–4 week) excess returns for 50 large-cap Taiwan-listed stocks,
and whether any such predictive power is independent of price momentum and
institutional trading flow. An initial event study and cross-sectional IC
analysis find statistically significant positive effects (CAAR@+8w=+14.2%,
ICIR≈0.31). Controlling for momentum shrinks the effect by roughly a third
but does not eliminate it; a battery of non-parametric tests (double sort,
matched-sample event study) finds a persistent, momentum-concentrated
residual effect. Controlling for institutional (foreign/trust/dealer)
trading flow leaves the effect almost entirely unchanged, ruling out
institutional flow as the driving mechanism. We conclude that attention
functions as a **conditional momentum amplifier** in this sample, not an
independent alpha signal.

## 2. Introduction

Investor attention, proxied by internet search volume, has been linked to
trading activity and return patterns in developed markets (US) and in
China. Taiwan — a market with a high retail-investor participation rate and
fast capital rotation across narrative-driven sectors (semiconductors, AI
supply chain, shipping) — is a plausible setting for a similar effect, but
public, reproducible tests are scarce. This project builds a full pipeline
from data collection through a sequence of increasingly strict statistical
controls, explicitly designed to test whether an initial positive finding
survives scrutiny.

## 3. Literature Background

See [`docs/literature_review.md`](../docs/literature_review.md) for full
detail. Four papers motivate the design: deHaan, Lawrence & Litjens
(2024/2025, *Management Science*) on measuring attention via Google search;
Barber, Huang, Odean & Schwarz (2022, *Journal of Finance*) on
attention-induced retail trading; Szczygielski, Charteris, Bwanya &
Brzeszczyński (2024, *International Review of Financial Analysis*) on
whether search trends reflect sentiment, attention, or uncertainty; and
Dong, Wu, Fang, Gozgor & Yan (2022, *Journal of International Financial
Markets, Institutions and Money*) on attention factors in China, a market
structurally closer to Taiwan than the US.

## 4. Data

- **Universe**: 50 large-cap TWSE stocks (`config/stock_list_50.csv`),
  built around a 0050-index-style large-cap set.
- **Google Trends**: weekly SVI, 2021-06 to 2026-06, collected via
  `pytrends` with an anchor-keyword batching scheme to partially correct
  for cross-request scale incomparability.
- **FinMind REST API**: daily close price, volume, trading value, and
  TAIEX benchmark (2021-01 to 2026-07); daily institutional
  (foreign/trust/dealer) buy-sell in shares.

## 5. Methodology

Full detail in [`docs/methodology.md`](../docs/methodology.md). Summary:
self-normalized attention factors (`attention_z`, `attention_shock`) →
CAAR event study → weekly cross-sectional IC/ICIR → Fama-MacBeth
regressions with progressively richer controls → residual-factor
re-testing → double/triple sort → matched-sample event study.

## 6. Empirical Results

### 6.1 Initial CAAR and IC evidence

`attention_z>2` events (n=377 after a 4-week non-overlap filter) show
CAR@+8w=+14.2% (t=8.46). Weekly cross-sectional IC of `attention_z` against
forward excess returns has ICIR≈0.31 (t≈4.8). The CAAR pattern shows
significant positive drift *before* the event week, an early warning sign
of momentum contamination.

### 6.2 Momentum contamination

Splitting `attention_z>2` events by prior 4-week return: past winners show
CAR@+8w=+30.8% (t=12.6); past non-winners show CAR@+8w=-1.1% (p=0.50, not
significant). Fama-MacBeth regressions confirm this: adding momentum
controls shrinks the attention coefficient by ~36% (still significant,
p<0.001).

### 6.3 Residual attention factor

Orthogonalizing `attention_z` against momentum, volume, volatility, and
liquidity each week and re-testing IC: significant at 1–2 weeks
(IC=0.036/0.027, p<0.005) but not at 4 weeks (IC=0.008, p=0.38).

### 6.4 Matched sample evidence

Nearest-neighbor matching each event to a similar-momentum/volume/
volatility non-event stock in the same week: event stocks still outperform
matched controls by +1.7% to +3.7% (1w–4w, all p<0.0001), with the gap
*growing* over the 4-week window — evidence of a persistent effect that
survives momentum-matching, in tension with the linear residual-factor
result above (interpreted as a non-linear/threshold interaction that
linear residualization partially removes; see
[`docs/limitations.md`](../docs/limitations.md)).

### 6.5 Institutional flow control

`attention_z` correlates weakly with all institutional net-buy ratios
(max r=0.054, vs r=0.277 for momentum). Adding institutional-flow controls
to the Fama-MacBeth regression shrinks the attention coefficient by only
~1% (0.00250→0.00247), versus 36% for momentum controls. A triple sort
(momentum × attention × institutional flow) shows high attention working
equally well in the winner bucket whether institutions are buying, neutral,
or selling (+2.51%, +4.45%, +2.99% at 4w respectively) — direct evidence
against an institutional-flow explanation.

## 7. Final Interpretation

The weight of evidence across five independent methods (correlation,
Fama-MacBeth regression, residual-factor IC, double/triple sort,
matched-sample event study) supports a single consistent story: attention
shocks carry a small amount of genuine incremental information about
short-term returns, but this information is **conditional on the stock
already exhibiting positive price momentum**, and this conditioning is
**not** explained by institutional trading flow. This project should be
interpreted as evidence that Google Trends attention can amplify
short-term momentum in Taiwan large-cap stocks, rather than evidence of a
standalone attention alpha.

## 8. Practical Implications

- Attention should be used as a *conditioning/ranking signal within an
  existing momentum universe*, not as a standalone stock-selection
  criterion.
- Institutional-flow filters add no measurable benefit on top of a
  momentum + attention combination in this sample and increase drawdown
  when stacked on — they are not a useful additional screen here.
- None of the above constitutes a costed, tradable strategy (see
  Limitations).

## 9. Limitations

See [`docs/limitations.md`](../docs/limitations.md) for full detail:
Google Trends cross-stock scale approximation; 50-stock, large-cap-only,
bull-market-heavy sample; industry-fixed-effects overfitting in one
regression specification; institutional data available only as share
counts, not NTD value; a documented discrepancy between linear-interaction
and non-parametric-sort evidence; no correction for calendar-clustering in
event-study/matched-sample significance tests; no transaction costs or
short-sale constraints modeled anywhere.

## 10. Conclusion

Across three rounds of increasingly adversarial testing (naive event
study → momentum control → institutional-flow control), the Google Trends
attention signal in this 50-stock Taiwan large-cap sample survives as a
real but conditional effect: a **momentum amplifier**, not an independent
alpha factor. The research process — actively trying to explain the
finding away rather than stopping at the first significant result — is, in
our view, as much the point of this project as the specific numeric
result.

## 11. References

1. deHaan, E., Lawrence, A., & Litjens, R. (2024/2025). *Measuring Investor
   Attention Using Google Search*. Management Science, 71(7), 6275–6297.
   https://doi.org/10.1287/mnsc.2022.02174
2. Barber, B. M., Huang, X., Odean, T., & Schwarz, C. (2022).
   *Attention-Induced Trading and Returns: Evidence from Robinhood Users*.
   Journal of Finance, 77(6), 3141–3190. https://doi.org/10.1111/jofi.13183
3. Szczygielski, J. J., Charteris, A., Bwanya, P. R., & Brzeszczyński, J.
   (2024). *Google search trends and stock markets: Sentiment, attention or
   uncertainty?* International Review of Financial Analysis, 91, 102549.
   https://doi.org/10.1016/j.irfa.2023.102549
4. Dong, D., Wu, K., Fang, J., Gozgor, G., & Yan, C. (2022). *Investor
   Attention Factors and Stock Returns: Evidence from China*. Journal of
   International Financial Markets, Institutions and Money, 77, 101499.
   https://doi.org/10.1016/j.intfin.2021.101499
