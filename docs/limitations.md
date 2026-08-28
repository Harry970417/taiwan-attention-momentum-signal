# Limitations

## Corrected Results Not Yet Regenerated

As of 2026-08-02, this checkout lacks real `data/raw/` and `data/processed/` inputs.
Corrected `*_asof_safe` empirical results are therefore not available. The old results are
retained only as legacy artifacts and are invalid for predictive/tradable interpretation.

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
