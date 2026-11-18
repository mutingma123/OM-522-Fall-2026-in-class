# OM 522, November 19: push versus a limit on work in the shop

This folder has its own Pixi environment and a copy of the FlowSim library (version 2.0.2).
With Pixi installed, it needs nothing else.

| Notebook | Open it with | What it is |
|---|---|---|
| `push_and_limits.py` | `pixi run class` | It runs a three-station shop two ways on the same 100 shifts of orders. Under push, every order enters when it arrives. Under a limit, S1 holds one job and S2 and S3 have racks of 2 or 1. The rest of the orders wait outside. |
| `limit_game.html` | Double-click it | A game on the same line and the same 100 shifts. You choose push or a limit and the rack sizes, then compare minutes in the shop with minutes from order. It needs no Pixi and no network. |

Run these commands from the root of the in-class repository. `pixi install` is needed only the first time.

```bash
cd in-class-notebooks/20261119
pixi install
pixi run class
```
