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

`critical_path.py` opens with a slider for each task's duration, and every
table and chart below recomputes when a slider moves. The `cpm` function runs
the forward pass (each task starts when its last predecessor finishes) and the
backward pass (each task finishes by the time its earliest-due successor must
start), and the notebook reports the early and late start and finish times and
the slack for every task. It then lists every start-to-finish path with its
length and checks the passes against networkx's `dag_longest_path_length`,
because the critical path is the longest path through the network. Two charts
follow, the network with the critical tasks highlighted and a Gantt chart with
each task's slack drawn after its bar.

The last section assigns two tasks to one shared crew, so the two tasks cannot
overlap. The notebook adds a precedence edge in each order, reruns the passes,
and compares the project duration with the CPM duration, which is a lower bound
once resources are limited. Lengthening one task (e.g., B) until its slack is
used up, and then by one more day, shows when a second critical path appears
and when the project finish moves.
