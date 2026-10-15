# OM 522 Critical Path Demo

This project schedules the launch of a new production cell with the critical
path method (CPM). The launch has seven tasks, from specifying the cell to
validating it, and each task has a duration in days and a list of predecessors,
i.e., tasks that must finish before it can start. We store the project as a
directed graph in networkx, run the forward and backward passes over it, and
read each task's slack and the critical path from the result.

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

`critical_path.py` stores each task's name, duration, and predecessors in one
dictionary, and changing a duration there changes every chart below. The `cpm`
function runs the forward pass (each task starts when its last predecessor
finishes) and the backward pass (each task finishes by the time its earliest-due
successor must start), and returns each task's early and late start and finish
times and slack. Two charts follow, the network with the critical tasks
highlighted and a Gantt chart with each task's slack drawn after its bar.
