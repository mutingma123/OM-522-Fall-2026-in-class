# OM 522 Eligible Machines Demo

This project extends the October 6 parallel-machine demo to a mixed GPU fleet.
A data science team again splits one night's queue of model-training runs among
several GPU machines to finish as early as possible. The machines now differ:
each has 80, 40, or 24 GB of memory, a run may use only machines with enough
memory, and the 24 GB machines are an older generation that takes twice as
long. The set of machines a run may use is its eligibility set, and a run's
time depends on the machine that runs it.

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

`eligible_machines.py` opens on a seven-job board example. It shows what the
October 6 LPT gets wrong when it ignores eligibility, then adapts the lower
bounds, LPT, and the insertion and interchange moves. Lines marked
`# IN CLASS` are the lines we work through together. Change `instance_id` in
the notebook to run one of the ten queues in `data/`.

## Schedules, processing times, and helpers

A schedule has the same shape as on October 6, a dictionary that maps each
machine to its jobs in order, e.g., `{"G1": ["J03", "J07"], "G2": ["J01"]}`.
Processing times are a dictionary of dictionaries, e.g.,
`{"J01": {"G1": 30, "G3": 60}}`, so `processing_times["J01"]["G3"]` is J01's
minutes on G3, and the machines listed for a job are exactly the machines it
may use.
`eligibility_utils.py` loads an instance, tabulates eligibility, rebuilds loads
and the makespan from a schedule, checks that every job runs exactly once on an
eligible machine, summarizes a schedule by machine, and draws a Gantt chart.

## Data

`generate_eligibility_data.py` (`pixi run data`) writes ten instances to `data/`
from seed 1013, and rerunning it reproduces them exactly. It refuses to
overwrite existing data.

| File | Contents |
| --- | --- |
| `instance_XXX/jobs.parquet` | `job`, `memory_gb` (the memory the run needs), and `base_minutes` (its time on a current card) |
| `instance_XXX/machines.parquet` | `machine`, `memory_gb`, and `slowdown` (1.0 for a current card, 2.0 for an older one) |
| `instance_XXX/processing_times.parquet` | `job`, `machine`, and `minutes`, one row per eligible pair. A pair that does not appear is not allowed |
| `manifest.json` | The seed, the sampling settings, and each instance's job, machine, and eligible-pair counts |

Each queue has 16 to 22 runs of 10 to 60 minutes on a current card. Each run
needs 24, 40, or 80 GB with probabilities 0.5, 0.3, and 0.2. Each fleet
has one or two machines of each memory size, and a run's time on a machine is
its base time times the machine's slowdown, rounded up to a whole minute. The
`processing_times` layout matches `resource_processing_times.csv` in the
option 1 project data. The jobs are simulated teaching data rather than
observed workload data.
