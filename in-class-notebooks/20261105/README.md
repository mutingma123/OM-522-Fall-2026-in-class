# OM 522 Variability Investigation

The November 5 investigation simulates one machine with FlowSim and varies how busy it is, how
irregular the arrivals are, and how irregular the processing times are. The handout on Blackboard
lists the steps, the questions, and what to submit.

## Run the notebook

The notebook runs inside the FlowSim folder, so it needs no environment of its own. Copy
`variability_investigation.py` into `~/OM522/flowsim`, next to `pixi.toml`, and run

```bash
cd ~/OM522/flowsim
pixi run marimo edit variability_investigation.py
```

Set `SEED` in the first cell to the last four digits of a student ID number before running the
investigation. The last cell writes `variability-<seed>.csv` into the same folder.
