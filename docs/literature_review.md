# Literature Review

Four papers motivate this project. Titles, authors, journals, and DOIs were
independently verified (via web search against publisher/SSRN/RePEc
records) before being cited here.

## 1. Measuring Investor Attention Using Google Search

deHaan, E., Lawrence, A., & Litjens, R. (2024/2025). *Management Science*,
71(7), 6275–6297. DOI: [10.1287/mnsc.2022.02174](https://doi.org/10.1287/mnsc.2022.02174)

Validates Google search volume as a measure of investor attention and
studies its relationship to trading activity and returns. Directly
motivates using SVI as the attention proxy in this project.

## 2. Attention-Induced Trading and Returns: Evidence from Robinhood Users

Barber, B. M., Huang, X., Odean, T., & Schwarz, C. (2022). *Journal of
Finance*, 77(6), 3141–3190. DOI: [10.1111/jofi.13183](https://doi.org/10.1111/jofi.13183)

Shows that retail attention (measured via Robinhood app data) drives
trading and is associated with return patterns that partially reverse —
raising the question of whether an attention effect is a genuine signal or
a retail-driven price-pressure artifact. This tension between "signal" and
"price pressure" is exactly what v0.2's naive CAAR could not distinguish,
motivating the momentum-control work in v0.3.

## 3. Google search trends and stock markets: Sentiment, attention or uncertainty?

Szczygielski, J. J., Charteris, A., Bwanya, P. R., & Brzeszczyński, J.
(2024). *International Review of Financial Analysis*, 91, 102549.
DOI: [10.1016/j.irfa.2023.102549](https://doi.org/10.1016/j.irfa.2023.102549)

Explicitly asks whether Google search spikes reflect attention, sentiment,
or uncertainty rather than a unified construct — the paper's title itself
is a caution against over-interpreting a single search-volume factor as
"the" attention effect. This project's finding (attention as a momentum
amplifier rather than an independent factor) is consistent with that
caution: a search-volume spike is likely picking up a mix of underlying
drivers, of which momentum-chasing appears dominant in this sample.

## 4. Investor Attention Factors and Stock Returns: Evidence from China

Dong, D., Wu, K., Fang, J., Gozgor, G., & Yan, C. (2022). *Journal of
International Financial Markets, Institutions and Money*, 77, 101499.
DOI: [10.1016/j.intfin.2021.101499](https://doi.org/10.1016/j.intfin.2021.101499)

Studies investor attention in an emerging Asian market with a high retail
share (China) rather than the US — closer in market structure to Taiwan
than the US-focused papers above. Provides a template for testing attention
effects outside developed, institutionally-dominated markets.

## How this project relates to the literature

None of the four papers test the Taiwan market, and none of them run the
specific falsification sequence used here (naive event study → momentum
control → institutional-flow control). The contribution of this project is
not a new theoretical claim, but a **reproducible, adversarially-tested
replication attempt** in a market structure (Taiwan, high retail
participation, large index concentration in a handful of semiconductor
names) that differs from the US and China settings in the literature above.
