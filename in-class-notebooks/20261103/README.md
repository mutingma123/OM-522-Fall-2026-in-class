# OM 522 Stress Test of Fixed Plans

The final project tests how each method's plan holds up when the data are not exact. This
notebook wraps the October 22 distribution search in one function, then runs two fixed plans for
one machine through 30 saved scenarios of uncertain processing times.

## Run the demo

```bash
pixi install
pixi run demo
```

Check the notebook without changing it with:

```bash
pixi run check
```

## What the notebook shows

`stress_test.py` has three parts.

1. `best_fit(data, families)` fits every continuous distribution in `scipy.stats` (except the
   two slow ones) to a data file and ranks them by the one-sample Kolmogorov-Smirnov statistic
   against the fitted CDF. The statistic uses no random draws, so the ranking is the same on every
   run. The eight files in `data-samples/` are the October 22 files.
2. Eight jobs on one machine have two fixed plans, the earliest due date (EDD) sequence and the
   sequence that pairwise interchange reaches from it. `execute` runs a plan as early as the
   processing times allow and reports total tardiness, maximum lateness, and whether any job is
   more than 20 minutes late.
3. Each processing time is multiplied by an independent lognormal factor with mean 1 and
   coefficient of variation 0.2. The notebook draws 30 scenarios from seed 522, saves them to
   `scenarios.csv`, reads them back, runs both plans unchanged through every scenario, and reports
   the mean, the 90th percentile, the count of scenarios that break the limit, and a per-scenario
   plot.
