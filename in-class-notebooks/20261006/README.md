# OM 522 Parallel Machines Demo

This project sets up identical-parallel-machine instances for building Longest
Processing Time (LPT) construction and local improvement in class. A data
science team splits one night's queue of model-training runs among several
identical GPU machines, and the goal is the smallest makespan, i.e., the time
the last machine finishes and the last model is ready.

## Run the demo

```bash
pixi install
pixi run demo
```

Run the checks with:

```bash
pixi run check
pixi run test
```

`parallel_machines.py` loads an instance, summarizes it, and demonstrates the
helper functions in `parallel_utils.py` on a small board example. The lower
bounds, LPT, and the improvement loop are written except for five lines marked
`# IN CLASS`, which are completed in class.
Change `instance_id` or `machine_count` in the notebook to build a different
instance.

## Schedules and helpers

A schedule is a dictionary that maps each machine to its jobs in processing
order, e.g., `{"M1": ["J03", "J07"], "M2": ["J01"]}`. Every machine starts at
time 0 and runs its jobs back to back, so a machine's load is also its finish
time.
`parallel_utils.py` rebuilds loads and the makespan from a schedule, checks that
every job runs exactly once on a known machine, summarizes a schedule by machine, and
draws a Gantt chart with an optional lower-bound line.

## Data

`generate_parallel_data.py` (`pixi run data`) writes ten instances to `data/`
from seed 1006, and rerunning it reproduces them exactly. It refuses to
overwrite existing data.

| File | Contents |
| --- | --- |
| `instance_XXX/jobs.parquet` | `job` and `processing_time` (whole minutes), one row per job |
| `manifest.json` | The seed, the sampling ranges, and each instance's job count and total minutes |

Each instance has 16 to 22 jobs, and each job takes 10 to 60 minutes, drawn
uniformly. Every job is queued at the start of the night. With five machines
there are three to four jobs per machine, which is where a one-pass construction
most often leaves room for improvement. The jobs are simulated teaching data
rather than observed workload data.
