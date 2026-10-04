# Multiple Testing Family Contract

This document is the single authoritative definition of which hypothesis
tests in this project are corrected together as one family, and why. Any
figure, table, or portfolio write-up that reports FDR-corrected significance
must match this contract; if it doesn't, the contract wins and the
downstream document is stale.

## The 30-test family (authoritative)

All 30 tests below are corrected together with one Benjamini-Hochberg
(BH-FDR) pass, at both q=0.10 and q=0.05 (`scripts/run_fdr_correction.py`,
output `results/tables/fdr_correction_all_tests_asof_safe.csv`).

| Group | Count | Composition |
|---|---:|---|
| Event study | 3 | `attention_z2`, `attention_ratio`, `attention_top_decile` CAAR definitions (date-clustered NW-HAC test, see below) |
| Regression | 15 | M1-M4 Fama-MacBeth x 3 horizons (1w/2w/4w) = 12, + M5 two-way FE x 3 horizons = 3 |
| Interaction | 12 | Model E, 4 terms (`attention_z`, `attention_z_x_past_4w_return`, `attention_z_x_total_inst_net_buy_ratio_4w`, `total_inst_net_buy_ratio_4w`) x 3 horizons |

**Why one family, not three.** All 30 tests ask variants of the same
underlying question -- "does attention_z (or an interaction involving it)
predict returns in this sample?" -- against the same 50-stock, ~5-year panel.
They are not independent research questions run on independent data; they
are the same panel sliced by event-definition, control set, and horizon.
Correcting them separately would let a researcher pick whichever
slicing makes a result survive, which is exactly the data-snooping problem
FDR correction exists to guard against. Pooling them into one family is the
conservative, defensible default whenever tests share a data-generating
process and a research question, which is the case here.

## Secondary sensitivity (non-authoritative)

`results/tables/fdr_correction_by_family_sensitivity_asof_safe.csv` also
reports each of the three groups corrected **separately** (event study alone,
regression alone, interaction alone), at both q=0.10 and q=0.05. This is
disclosed for transparency and to show whether family-scoping changes which
results survive -- it is not a second rule to choose from after the fact.
The 30-test pooled family above is the only number used for "how many tests
survived multiple-testing correction" claims in any write-up.

## Event-study inference note

The event-study p-values that enter this family are the **date-clustered,
Newey-West HAC** p-values (`t_stat_date_clustered_hac` /
`p_value_date_clustered_hac` in `caar_event_summary_asof_safe.csv`), not the
naive per-event t-test. See `src/event_study.py` module docstring for why:
events cluster in calendar time and forward-return windows overlap, so a
plain per-event t-test overstates the effective sample size before FDR
correction is even applied. Feeding FDR the naive p-values would understate
the true multiple-testing problem twice over.
