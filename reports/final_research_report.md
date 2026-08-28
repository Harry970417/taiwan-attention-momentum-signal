# Attention Meets Momentum: Corrected Research Status

Status date: 2026-08-02

## Abstract

The original version of this project tested whether weekly Google Trends search-volume
spikes predict short-term excess returns for 50 Taiwan large-cap stocks. Those legacy
results are now **superseded and invalidated for predictive/tradable interpretation**
because the weekly Google Trends observation label was treated as if the signal were
available for same-week trading.

The corrected code now enforces an explicit information-availability contract:

`observation_period_start` -> `observation_period_end` -> `available_at` ->
`signal_date` -> `first_tradeable_at` -> `return_start` -> `return_end`

Because this checkout does not contain `data/raw/` or `data/processed/`, corrected
`*_asof_safe` research results have not yet been regenerated from real raw data. The
project must therefore be described as a **retrospective association study**, not a
real-time tradable predictive strategy.

## Root Cause

The old pipeline used the Google Trends weekly row label as `week` and calculated forward
returns from that same date or the next nearby trading day. In the local sample, weekly
labels are Sundays, consistent with a weekly bucket start. A bucket-start label cannot be
assumed to mean the full week's SVI was available at that time.

The conservative corrected assumption is:

- A Google Trends weekly row represents `observation_period_start` through
  `observation_period_end`.
- The row is not used until `available_at = observation_period_start + 14 days`.
- `signal_date = available_at`.
- `first_tradeable_at` is the first stock trading day on or after `signal_date`.
- Past controls use `feature_asof_trade_date`, the trading day strictly before
  `first_tradeable_at`.
- Forward returns start at `return_start = first_tradeable_at`.

## Corrected Pipeline

The corrected outputs use `_asof_safe` suffixes and do not overwrite legacy artifacts:

- `data/processed/attention_weekly_panel_v03_asof_safe.csv`
- `data/processed/attention_weekly_panel_v03_residual_asof_safe.csv`
- `data/processed/attention_weekly_panel_v04_asof_safe.csv`
- `results/tables/*_asof_safe.csv`
- `results/figures/*_asof_safe.png`

No-look-ahead assertions are applied when panels are built and loaded by downstream
analysis scripts.

## Current Empirical Results

No corrected empirical conclusion is available in this checkout. Running
`python scripts\run_event_study.py` stops because the real raw benchmark file
`data/raw/price_TAIEX.csv` is missing. The repository contains only `data/sample/`, which
must not be used as research evidence.

Legacy tables are retained for provenance only and are marked in
`results/tables/legacy_results_provenance.csv`.

## Conclusion

The previous "conditional momentum amplifier" conclusion is not a corrected finding. It
is downgraded to an uncorrected retrospective association pending an as-of-safe rerun from
real raw data. If corrected results later show that significance disappears or direction
changes, the headline conclusion must follow the corrected results.
