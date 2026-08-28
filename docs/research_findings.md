# Research Findings

Status date: 2026-08-02

## Corrected Finding

No corrected empirical finding is available yet. The as-of-safe pipeline has been
implemented, but this checkout does not contain the real `data/raw/` and `data/processed/`
inputs needed to regenerate corrected results.

## Legacy Finding Status

The old v0.2-v0.4 findings, including positive CAAR, IC/ICIR, Fama-MacBeth coefficients,
sort results, matched-sample results, and institutional-flow controls, are now marked
**superseded / invalidated for predictive interpretation**.

They were generated before the Google Trends weekly availability contract was enforced.
They may be discussed only as uncorrected retrospective associations and must not be cited
as evidence of a real-time tradable predictive strategy.

## Required Evidence Before Restating a Headline Result

The following corrected artifacts must exist and be compared against legacy outputs:

- `results/tables/caar_event_summary_asof_safe.csv`
- `results/tables/v03_fama_macbeth_summary_asof_safe.csv`
- `results/tables/v03_residual_ic_summary_asof_safe.csv`
- `results/tables/v04_regression_with_chips_summary_asof_safe.csv`
- `results/tables/v04_interaction_model_summary_asof_safe.csv`
- `results/tables/asof_safe_legacy_comparison.csv` with status `compared`

Until then, the final classification is: **retrospective association study, corrected
results blocked by missing real raw data**.
