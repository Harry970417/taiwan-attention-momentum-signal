# Methodology

## 1. Google Trends Weekly Availability Contract

Weekly Google Trends rows are treated as observation-period data, not as immediately
tradeable signals. The corrected pipeline records:

- `observation_period_start`: Google Trends weekly bucket label.
- `observation_period_end`: six calendar days after the bucket start.
- `available_at`: conservative availability date, set to `observation_period_start + 14 days`.
- `signal_date`: date the SVI row may first be used as a signal.
- `first_tradeable_at`: first stock trading day on or after `signal_date`.
- `feature_asof_trade_date`: trading day strictly before `first_tradeable_at`; past controls use this date.
- `return_start`: first tradeable date used as the start of forward returns.
- `return_end_*w`: first trading day on or after `return_start + horizon`.

Because historical Google Trends publication timestamps are not proven in this project,
the study is conservative and delays each weekly SVI observation by at least one full
weekly cycle.

## 2. Attention Factor Construction

`attention_z` and `attention_shock` use only trailing SVI data available as of the
current observation:

- `SVI_MA52`: trailing 52-week mean, `min_periods=26`, non-centered.
- `SVI_STD52`: trailing 52-week standard deviation, `min_periods=26`, non-centered.
- `attention_shock = SVI / SVI_MA52 - 1`
- `attention_z = (SVI - SVI_MA52) / SVI_STD52`

Centered rolling windows, full-sample mean/std, and future backfills are prohibited.

## 3. Forward Returns

Forward returns are not measured from the Google Trends weekly label. They start at
`return_start`, the first tradeable date after the delayed signal. If a horizon's endpoint
is missing, the return is left missing rather than filled.

## 4. Event Study

Events are defined on `signal_date`, not the raw Google Trends week label. Top-decile
events are computed within each signal week's cross-section, not from the whole sample.
Post-signal CAR is measured from offset `+1` onward.

## 5. Regressions And Sorts

Fama-MacBeth regressions, residual attention, double sort, institutional-flow controls,
and triple sort all load as-of-safe panels and run no-look-ahead assertions before
analysis.

## 6. Result Provenance

Corrected outputs use `_asof_safe` suffixes and do not overwrite legacy results. Legacy
results are marked in `results/tables/legacy_results_provenance.csv`, and common-key
differences are written to `results/tables/asof_safe_legacy_comparison.csv` when corrected
tables exist.
