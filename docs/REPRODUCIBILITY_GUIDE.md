# Reproducibility Guide

Status date: 2026-08-02

## Data Requirement

Real research reruns require `data/raw/` and then `data/processed/`. These directories are
gitignored and absent in this checkout. `data/sample/` is for demonstration only and must
not be used as empirical evidence.

## Clean Environment

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Corrected Pipeline

```powershell
python scripts\run_data_collection.py
python scripts\run_event_study.py
python scripts\run_momentum_control.py
python scripts\run_institutional_flow_analysis.py
```

Corrected artifacts use `_asof_safe` suffixes. Legacy outputs must not be overwritten.

## Verification

```powershell
python -m unittest discover -s tests -v
python -m compileall src scripts tests app
python src\result_comparison.py
```

`results/tables/asof_safe_legacy_comparison.csv` should show `compared` rows only after
corrected result tables exist. If it shows `blocked_missing_table`, the empirical rerun is
not complete.

## Blocking Conditions

If Google Trends / FinMind quota, source schema drift, missing history, or licensing
uncertainty blocks collection, stop and report the blocker. Do not use mock, synthetic, or
sample data as research evidence.
