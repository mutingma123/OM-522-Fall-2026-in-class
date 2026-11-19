# OM 522, November 17: variability and Quiz 4

This folder has the November 17 class notebook, the Quiz 4 notebook, and the Quiz 4 handout. It
has its own Pixi environment and a copy of the FlowSim library (version 2.0.2). With Pixi
installed, it needs nothing else.

| File | Open it with | What it is |
|---|---|---|
| `variability.py` | `pixi run class` | The class notebook. It runs a three-station line (4, 6, and 5 minutes per job) in three parts. First, the line holds 1 to 6 jobs, plus the critical WIP of 2.5. Then a job arrives every minute, with racks of 0 to 4. Last, it compares thirty seeds of the Quiz 4 experiment with the waiting-time formula. |
| `variability_investigation.py` | `pixi run quiz4` | The Quiz 4 notebook. The Quiz 4 handout walks through it. It saves your results as `variability-SEED.csv` in this folder. |
| `quiz-04-variability-investigation.pdf` | Double-click it | The Quiz 4 handout, the same one as on Blackboard |
| `make_seed_data.py` | `pixi run python make_seed_data.py` | Already run. Its output is `data/variability-seeds.csv`, the Quiz 4 cases for seeds 1234 to 1263. Rerun it only to regenerate that file. |

Run these commands from the root of the in-class repository. `pixi install` is needed only the
first time.

```bash
cd in-class-notebooks/20261117
pixi install
pixi run class
```

Open the Quiz 4 notebook from the same folder with `pixi run quiz4`.
