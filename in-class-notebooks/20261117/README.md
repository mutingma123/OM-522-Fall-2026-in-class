# OM 522, November 17: variability

This folder has its own environment and a copy of the FlowSim library (version 2.0.2), so it runs
with nothing else installed.

| File | Open it with | What it is |
|---|---|---|
| `variability.py` | `pixi run class` | Thirty runs of the Quiz 3 experiment, the waiting-time formula against simulation, and one station's variability reaching the next |
| `make_seed_data.py` | `pixi run python make_seed_data.py` | Writes `data/quiz3-seeds.csv`: the Quiz 3 cases for seeds 1234 to 1263 |

Run `pixi install` once, from this folder, before the first command.

```bash
cd in-class-notebooks/20261117
pixi install
pixi run class
```
