# Research Methodology Audit

Status date: 2026-08-02

## Critical Finding

The previous audit conclusion that no forward-return look-ahead issue was found is
superseded. A critical availability bias was identified in the Google Trends weekly
alignment:

- Raw weekly Google Trends labels were used as the analysis `week`.
- The same date was used to build events and forward returns.
- If the label is a weekly bucket start, the full week's SVI was not knowable at that
  date.

## Remediation

The code now enforces an as-of-safe contract:

`observation_period_start` -> `observation_period_end` -> `available_at` ->
`signal_date` -> `first_tradeable_at` -> `return_start` -> `return_end`

Google Trends weekly observations are delayed by at least one full weekly cycle unless a
stronger historical publication timestamp can be proven.

## Tests Added

`tests/test_asof_contract.py` covers weekly boundaries, cross-month and cross-year dates,
holiday first-tradeable alignment, missing forward data, no-look-ahead assertion failure,
and trailing z-score causality.

## Current Blocker

Corrected empirical results cannot be regenerated in this checkout because real
`data/raw/` and `data/processed/` inputs are absent. The old results are marked
superseded / invalidated in `results/tables/legacy_results_provenance.csv`.
