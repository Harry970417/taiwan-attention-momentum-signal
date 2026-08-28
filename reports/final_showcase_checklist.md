# Final Showcase Checklist

Status date: 2026-08-02

## Current Showcase Position

The project should be showcased as a methodology remediation and reproducible research
engineering project, not as a validated trading signal.

## Must Say

- Legacy results are superseded / invalidated for predictive interpretation.
- Google Trends weekly availability was the critical issue.
- The corrected code adds an explicit as-of contract and no-look-ahead tests.
- Corrected empirical results are blocked in this checkout because real raw data is
  missing.
- The study is currently a retrospective association study, not a real-time tradable
  predictive strategy.

## Must Not Say

- Do not claim corrected CAAR, IC, Fama-MacBeth, sort, matched-sample, or institutional
  flow significance until `*_asof_safe` tables exist.
- Do not use `data/sample/` as research evidence.
- Do not describe the old "conditional momentum amplifier" result as a corrected finding.

## Current Artifacts

- `README.md`
- `README_zh.md`
- `docs/methodology.md`
- `docs/limitations.md`
- `docs/research_findings.md`
- `docs/portfolio_writeup_zh.md`
- `reports/final_research_report.md`
- `results/tables/legacy_results_provenance.csv`
- `results/tables/asof_safe_legacy_comparison.csv`
