# Project Explained Simply

## 15 Seconds

This project studies whether Google Trends search attention is associated with Taiwan
large-cap stock momentum. The old predictive conclusion is invalidated until corrected
as-of-safe results are regenerated.

## 60 Seconds

The original project collected weekly Google Trends SVI and daily FinMind market data,
then tested event-study returns, IC, Fama-MacBeth regressions, double/triple sorts, and
institutional-flow controls.

The critical correction is about time: a Google Trends weekly label is treated as the
start of an observation week, not as an immediately tradeable signal. The corrected
pipeline delays weekly SVI by a full weekly cycle before forming a signal, then starts
forward returns only after the signal is actually tradeable.

## Current Conclusion

No corrected empirical conclusion is available in this checkout because real
`data/raw/` and `data/processed/` inputs are missing. The project should be described as
a retrospective association study pending an as-of-safe rerun, not a real-time tradable
predictive strategy.
