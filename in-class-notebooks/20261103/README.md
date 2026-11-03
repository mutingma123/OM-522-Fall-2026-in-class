# OM 522 FlowSim production line, November 3

This folder builds a three-station production line (Cut, Weld, Paint) in FlowSim from shop data,
and compares rack sizes between the machines. It holds three things:

- `flowsim/`, a copy of the FlowSim library (version 0.3.0), so the notebook imports it with
  `from flowsim import ...` and nothing needs installing beyond the environment below;
- `data/`, ten days of shop data, i.e., `releases.csv` (when each job was released to the line)
  and `processing_times.csv` (minutes per job at each station);
- `production_line.py`, the Marimo notebook.

## Run it

```bash
pixi install
pixi run demo
```

## What the notebook does

1. Reads the two files and computes the time between releases within each day.
2. Fits eight common distribution families to each input with `best_fit`. It shows first that
   SciPy's free fit of Weld can start below zero (and so draw a negative time, which stops a
   FlowSim run), then that `best_fit` by default refits such a family at zero and marks it in
   `loc_fixed`. It takes the first row, i.e., the best-fitting nonnegative family, and checks
   its `upper` for a ceiling near the data.
3. Turns each fit into a sampler with `sampler` and checks 10,000 draws against the data.
4. Builds the line one FlowSim call per cell, runs one shift, and then 100 shifts.
5. Compares five rack plans on the same simulated shifts with `compare`.

A full run takes about 20 seconds.
