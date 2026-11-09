# OM 522 FlowSim production line, November 3

This folder builds a three-station production line (Cut, Weld, Paint) in FlowSim from shop data,
and compares rack sizes between the machines. It holds three things:

- `flowsim/`, a copy of the FlowSim library (version 2.0.2), so the notebook imports it with
  `import flowsim` and nothing needs installing beyond the environment below;
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
2. Fits five common distribution families to each input with `fit_all`. It reads each fit's
   `p_negative`, the chance of drawing a negative time, which stops a FlowSim run, and takes
   `.best`, the top-ranked fit whose chance is at most one in a million.
3. Checks 10,000 draws from the Weld fit against the data. A fit goes directly into a model.
4. Builds the line one FlowSim call per cell, runs one shift, and then 100 shifts.
5. Compares five rack plans on the same simulated shifts with `compare`.

A full run takes under 20 seconds. The class on November 3 used an earlier version of FlowSim, so the
calls and a few numbers differ slightly from the recording, and the November 3 notes list each difference.
