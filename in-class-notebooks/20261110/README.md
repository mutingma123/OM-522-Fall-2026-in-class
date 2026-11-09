# OM 522, November 10: the stress test and Quiz 3

This folder has its own environment and a copy of the FlowSim library (version 2.0.2), so it runs
with nothing else installed.

| Notebook | Open it with | What it is |
|---|---|---|
| `stress_test.py` | `pixi run stress-test` | The stress test of fixed plans that your final submission requires, on a small example |
| `variability_investigation.py` | `pixi run quiz3` | The notebook for Quiz 3 (see the handout on Blackboard) |

Run `pixi install` once, from this folder, before the first command.

```bash
cd in-class-notebooks/20261110
pixi install
pixi run stress-test
```

`stress_test.py` writes `scenarios.csv` next to the notebook. `variability_investigation.py` writes
`variability-<seed>.csv` to the folder you run it from, and that file is what you submit.
