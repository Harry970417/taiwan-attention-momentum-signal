# Taiwan Attention Momentum Signal

English README. Chinese version: [README_zh.md](README_zh.md).

## Critical Methodology Status (2026-08-02)

The legacy headline results in this repository are **superseded and invalidated for
predictive/tradable interpretation**.

Root cause: the old pipeline treated a Google Trends weekly row label as if the full
weekly SVI observation were already available for same-week signal generation and forward
return testing. If that label is the weekly bucket start, the old alignment can use
information that was not complete at the assumed trade date.

The corrected pipeline now enforces this as-of contract:

`observation_period_start` -> `observation_period_end` -> `available_at` ->
`signal_date` -> `first_tradeable_at` -> `return_start` -> `return_end`

Because this checkout does not contain real `data/raw/` or `data/processed/`, corrected
`*_asof_safe` empirical results have not yet been regenerated. Until those results exist,
this project must be described only as a **retrospective association study**, not a
real-time tradable predictive strategy.

## What Changed

- Added explicit Google Trends weekly observation and availability fields.
- Delayed each weekly SVI observation by a conservative full weekly cycle.
- Moved forward return starts to the first tradeable date after the delayed signal.
- Made past controls use the trading day strictly before `first_tradeable_at`.
- Replaced panel and result outputs with `_asof_safe` paths so legacy results are not
  silently overwritten.
- Added no-look-ahead assertions to panel builders and downstream loaders.
- Changed top-decile event detection from whole-sample quantiles to weekly cross-sectional
  quantiles.
- Fixed institutional-flow clean reruns by saving and reading the expected raw breakdown
  files.
- Marked legacy outputs in `results/tables/legacy_results_provenance.csv`.

## Current Evidence

No corrected empirical conclusion is available in this checkout. Running
`python scripts\run_event_study.py` stops because `data/raw/price_TAIEX.csv` is missing.
The repository contains only `data/sample/`, which must not be used as real research
evidence.

The old "conditional momentum amplifier" conclusion is now only an uncorrected
retrospective association pending an as-of-safe rerun from real raw data.

## Corrected Pipeline

```powershell
python scripts\run_data_collection.py
python scripts\run_event_study.py
python scripts\run_momentum_control.py
python scripts\run_institutional_flow_analysis.py
```

Expected corrected artifacts include:

- `data/processed/attention_weekly_panel_v03_asof_safe.csv`
- `data/processed/attention_weekly_panel_v03_residual_asof_safe.csv`
- `data/processed/attention_weekly_panel_v04_asof_safe.csv`
- `results/tables/*_asof_safe.csv`
- `results/figures/*_asof_safe.png`
- `results/tables/asof_safe_legacy_comparison.csv`

If Google Trends or FinMind quota, source drift, missing history, or licensing uncertainty
blocks real data collection, stop that subprocess and report it. Do not substitute demo,
mock, synthetic, or sample data for research evidence.

## Tests

```powershell
python -m unittest discover -s tests -v
python -m compileall src scripts tests app
```

The new tests cover weekly boundaries, cross-month and cross-year dates, holidays, missing
forward data, active no-look-ahead failures, and trailing z-score causality.

## Documentation

- [Methodology](docs/methodology.md)
- [Limitations](docs/limitations.md)
- [Research findings status](docs/research_findings.md)
- [Methodology audit](docs/RESEARCH_METHODOLOGY_AUDIT.md)
- [Portfolio writeup](docs/portfolio_writeup_zh.md)
- [Corrected research report](reports/final_research_report.md)

## Not Investment Advice

Nothing in this repository is a recommendation to buy, sell, or hold securities. No
transaction costs, slippage, market impact, short-sale constraints, or live execution
constraints are modeled.
