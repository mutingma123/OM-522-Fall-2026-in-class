# OM 522, November 10: the stress test and the Quiz 4 notebook

This folder has its own environment and a copy of the FlowSim library (version 2.0.2), so it runs
with nothing else installed.

| Notebook | Open it with | What it is |
|---|---|---|
| `stress_test.py` | `pixi run stress-test` | The stress test of fixed plans that your final submission requires, on a small example |
| `variability_investigation.py` | `pixi run quiz4` | The notebook for Quiz 4, which starts after the November 17 class (see the handout on Blackboard) |

Run `pixi install` once, from this folder, before the first command.

```bash
cd in-class-notebooks/20261110
pixi install
pixi run stress-test
```

`stress_test.py` writes `scenarios.csv` next to the notebook. For Quiz 4, you submit one document,
as the handout's "What to submit" section describes.
