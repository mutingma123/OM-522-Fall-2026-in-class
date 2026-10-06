import marimo

__generated_with = "0.24.2"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    import math
    from pathlib import Path

    import matplotlib.pyplot as plt
    import polars as pl
    import seaborn as sns

    sns.set_style("whitegrid")
    plt.rcParams["font.family"] = "serif"

    from parallel_utils import (
        machine_loads,
        makespan,
        plot_gantt,
        summarize_schedule,
        validate_schedule,
    )

    return (
        Path,
        machine_loads,
        makespan,
        math,
        mo,
        pl,
        plot_gantt,
        summarize_schedule,
        validate_schedule,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # OM 522 Parallel Machines: LPT and Local Improvement

    Clarke–Wright split customers among several trucks. Here a data science
    team splits one night's queue of model-training runs among several identical
    GPU machines. GPUs are scarce and reserved in advance, so the number of
    machines is fixed for the night. Every training run is queued at the start
    of the night and runs on any machine without interruption. A machine runs its
    jobs back to back, so its load (the minutes of training assigned to it) is
    also the time it finishes. The **makespan** is the time the last machine
    finishes, i.e., when the last model is ready for the morning meeting, and we
    want it as small as possible.

    The decision has two parts, which machine gets each job and the order of jobs
    on each machine. For makespan, only the first part matters.

    Lines marked `# IN CLASS` are completed together in class.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Instance settings

    `instance_id` picks one of the ten nightly queues in `data/`, or `"toy"` for
    the board example, and `machine_count` sets the number of identical GPU
    machines.
    """)
    return


@app.cell
def _(Path):
    data_dir = Path(__file__).parent / "data"
    instances = sorted(path.name for path in data_dir.glob("instance_*"))

    instances
    return (data_dir,)


@app.cell
def _(data_dir, pl):
    # "toy" runs the board example on 3 machines. For a real queue, set e.g.
    # instance_id = "instance_007" and machine_count = 5.
    instance_id = "toy"
    machine_count = 3

    if instance_id == "toy":
        processing_times = {
            "J1": 5,
            "J2": 5,
            "J3": 4,
            "J4": 4,
            "J5": 3,
            "J6": 3,
            "J7": 3,
        }
    else:
        jobs = pl.read_parquet(data_dir / instance_id / "jobs.parquet")

        # processing_times["J01"] gives that job's minutes, as demand did for routing.
        processing_times = {
            job: minutes
            for job, minutes in jobs.iter_rows()
        }
    machines = [f"M{_number}" for _number in range(1, machine_count + 1)]
    return instance_id, machine_count, machines, processing_times


@app.cell
def _(machines, processing_times):
    _total_minutes = sum(processing_times.values())
    print(f"Jobs: {len(processing_times)}")
    print(f"Total minutes of work: {_total_minutes}")
    print(
        f"Shortest and longest jobs: {min(processing_times.values())} and "
        f"{max(processing_times.values())} minutes"
    )
    print(
        f"Minutes per machine if spread evenly over {len(machines)} machines: "
        f"{_total_minutes / len(machines):.1f}"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Tools for checking a schedule

    A schedule is a dictionary that maps each machine to the list of jobs it runs,
    in order, e.g., `{"M1": ["J03", "J07"], "M2": ["J01"]}`. This is the same
    shape as `cluster2customer` from Clarke–Wright. `parallel_utils.py`
    provides the following:

    - `machine_loads(schedule, processing_times)` rebuilds every machine's load
      from the schedule.
    - `makespan(schedule, processing_times)` returns the largest load.
    - `validate_schedule(schedule, jobs, machines)` raises an error that lists
      every unknown machine or job and every job scheduled zero times or more than
      once.
    - `summarize_schedule(schedule, processing_times)` returns one row per machine
      with its jobs and load.
    - `plot_gantt(schedule, processing_times, lower_bound)` draws a Gantt chart,
      i.e., one bar per machine with its jobs back to back, and an optional dashed
      line at a lower bound.

    The checker and the load rebuild never reuse loads computed by our own
    method, so a bookkeeping mistake in the method cannot hide itself.

    For example, the cell below deals the jobs to the machines in turn, like
    cards, ignoring their sizes.
    """)
    return


@app.cell
def _(
    machines,
    plot_gantt,
    processing_times,
    summarize_schedule,
    validate_schedule,
):
    _dealt = {_machine: [] for _machine in machines}
    for _position, _job in enumerate(processing_times):
        _dealt[machines[_position % len(machines)]].append(_job)

    validate_schedule(
        schedule=_dealt,
        jobs=processing_times,
        machines=machines,
    )
    print(summarize_schedule(_dealt, processing_times))

    _fig, _ax = plot_gantt(
        schedule=_dealt,
        processing_times=processing_times,
        title="Jobs dealt in turn",
        figsize=(7, 2.5),
    )
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1. Lower bounds

    $$C_{\max} \ge \max_j p_j \qquad\qquad C_{\max} \ge \left\lceil \frac{\sum_j p_j}{m} \right\rceil$$

    The larger of the two is the bound. A schedule that meets it is optimal.
    """)
    return


@app.cell
def _(math):
    def lower_bound(processing_times, machine_count):
        longest_job = max(processing_times.values())
        # IN CLASS: the average load per machine, rounded up to a whole minute.
        average_load = math.ceil(sum(processing_times.values()) / machine_count)
        return max(longest_job, average_load)

    return (lower_bound,)


@app.cell
def _(instance_id, lower_bound, machine_count, processing_times):
    instance_bound = lower_bound(processing_times, machine_count)

    print(
        f"{instance_id}: longest job {max(processing_times.values())} minutes, "
        f"average load {sum(processing_times.values()) / machine_count:.1f} minutes, "
        f"lower bound {instance_bound} minutes"
    )
    return (instance_bound,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2. LPT construction

    Sort the jobs from longest to shortest, then give each job to a machine with
    the smallest current load. Ties go to the lower job ID and the lower machine
    ID, so the result is reproducible.
    """)
    return


@app.function
def lpt(processing_times, machines):
    schedule = {machine: [] for machine in machines}
    loads = {machine: 0 for machine in machines}
    lpt_order = sorted(
        processing_times,
        # IN CLASS: longest job first, ties broken by job ID.
        key=lambda job: (-processing_times[job], job),
    )
    for job in lpt_order:
        # IN CLASS: the least-loaded machine, ties broken by machine ID.
        machine = min(machines, key=lambda m: (loads[m], m))
        schedule[machine].append(job)
        loads[machine] += processing_times[job]
    return schedule


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3. Check and plot the LPT schedule
    """)
    return


@app.cell
def _(
    instance_bound,
    instance_id,
    machines,
    makespan,
    plot_gantt,
    processing_times,
    summarize_schedule,
    validate_schedule,
):
    lpt_schedule = lpt(processing_times, machines)

    validate_schedule(
        schedule=lpt_schedule,
        jobs=processing_times,
        machines=machines,
    )
    _lpt_makespan = makespan(lpt_schedule, processing_times)
    print(
        f"{instance_id}: LPT makespan {_lpt_makespan} minutes against a lower bound "
        f"of {instance_bound}, a gap of {_lpt_makespan - instance_bound} minutes"
    )
    print(summarize_schedule(lpt_schedule, processing_times))
    _fig, _ax = plot_gantt(
        schedule=lpt_schedule,
        processing_times=processing_times,
        lower_bound=instance_bound,
    )
    _fig
    return (lpt_schedule,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 4. Insertion and interchange

    Both moves change which machine runs a job. Neither changes the order of
    jobs on a machine, because order does not affect the makespan.

    - **Insertion** moves job $j$ from machine $a$ to machine $b$, so $a$ loses
      $p_j$ minutes and $b$ gains them.
    - **Interchange** swaps job $j$ on machine $a$ with job $i$ on machine $b$,
      so $a$ loses $p_j - p_i$ minutes and $b$ gains them.

    We call the minutes that leave $a$ the **shift**. Only a machine at the
    makespan gives up work. With $a$ at the makespan, the gap to machine $b$ is
    $L_a - L_b$, and a move is acceptable when $0 < \text{shift} < L_a - L_b$,
    because then $a$ finishes earlier and $b$ still finishes before the old
    makespan. Among acceptable moves, the loop takes the one whose larger
    changed load is smallest, and it repeats until no acceptable move remains.
    When several machines tie at the makespan, an accepted move can leave the
    printed makespan unchanged, because another tied machine still finishes at
    the old makespan. A later move can then take work off that machine.

    Insertion offers whole jobs as shifts, and interchange offers differences
    between jobs. When every job on $a$ is at least as long as the gap, only an
    interchange can help. When no job on $b$ is shorter than the job leaving
    $a$, only an insertion can help.

    Starting from LPT, insertion cannot help on the first pass. LPT gave the
    last (and shortest) job on the bottleneck machine to the least-loaded
    machine, so the gap to every other machine is at most that job's length,
    and no job on the bottleneck is shorter than the gap. A later pass can still
    use an insertion once interchanges have changed the loads. Insertion matters
    most for a starting schedule with uneven job counts, such as the jobs dealt
    in turn above.
    """)
    return


@app.cell
def _(machine_loads, makespan):
    def improve(schedule, processing_times):
        # Work on a copy, because the loop changes the lists in place and the
        # LPT schedule must survive for the comparison.
        schedule = {m: list(jobs) for m, jobs in schedule.items()}
        moves = []
        while True:
            loads = machine_loads(schedule, processing_times)
            cmax = max(loads.values())

            # Collect every acceptable move as (new_max, a, b, j, i), where
            # i is None for an insertion.
            candidates = []
            for a in schedule:
                if loads[a] < cmax:
                    continue  # only machines at the makespan give up work
                for b in schedule:
                    if b == a:
                        continue
                    gap = loads[a] - loads[b]
                    for j in schedule[a]:
                        # Insertion: move j from a to b.
                        # IN CLASS: the shift, i.e., the minutes that leave a.
                        shift = processing_times[j]
                        if 0 < shift < gap:
                            new_max = max(loads[a] - shift, loads[b] + shift)
                            candidates.append((new_max, a, b, j, None))
                        # Interchange: swap j on a with job i on b.
                        for i in schedule[b]:
                            # IN CLASS: the shift, i.e., the minutes that leave a.
                            shift = processing_times[j] - processing_times[i]
                            if 0 < shift < gap:
                                new_max = max(loads[a] - shift, loads[b] + shift)
                                candidates.append((new_max, a, b, j, i))

            if not candidates:
                return schedule, moves
            # Take the move whose larger changed load is smallest.
            _, a, b, j, i = min(candidates, key=lambda move: move[0])
            schedule[a].remove(j)
            schedule[b].append(j)
            if i is not None:
                schedule[b].remove(i)
                schedule[a].append(i)
            moves.append((a, b, j, i, makespan(schedule, processing_times)))

    return (improve,)


@app.function
def print_moves(moves, processing_times):
    """Print one line per move accepted by improve()."""
    for number, (a, b, j, i, cmax_after) in enumerate(moves, start=1):
        if i is None:
            action = f"move {j} ({processing_times[j]}) from {a} to {b}"
        else:
            action = (
                f"swap {j} ({processing_times[j]}) on {a} "
                f"with {i} ({processing_times[i]}) on {b}"
            )
        print(f"Move {number}: {action}, makespan now {cmax_after}")
    print(f"{len(moves)} moves accepted")


@app.cell
def _(
    improve,
    instance_id,
    lpt_schedule,
    machines,
    processing_times,
    validate_schedule,
):
    improved_schedule, moves = improve(lpt_schedule, processing_times)

    validate_schedule(
        schedule=improved_schedule,
        jobs=processing_times,
        machines=machines,
    )
    print(f"{instance_id}, starting from the LPT schedule")
    print_moves(moves, processing_times)
    return (improved_schedule,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 5. Compare
    """)
    return


@app.cell
def _(
    improved_schedule,
    instance_bound,
    instance_id,
    lpt_schedule,
    makespan,
    pl,
    plot_gantt,
    processing_times,
    summarize_schedule,
):
    _lpt_makespan = makespan(lpt_schedule, processing_times)
    _improved_makespan = makespan(improved_schedule, processing_times)
    print(f"{instance_id}, lower bound {instance_bound} minutes")
    print(
        f"LPT makespan {_lpt_makespan} minutes, "
        f"{_lpt_makespan - instance_bound} above the bound"
    )
    print(
        f"Improved makespan {_improved_makespan} minutes, "
        f"{_improved_makespan - instance_bound} above the bound"
    )

    _comparison = (
        summarize_schedule(lpt_schedule, processing_times)
        .select(
            "machine",
            pl.col("load_minutes").alias("lpt_load"),
        )
        .join(
            summarize_schedule(improved_schedule, processing_times).select(
                "machine",
                pl.col("load_minutes").alias("improved_load"),
            ),
            on="machine",
        )
    )
    print(_comparison)

    _fig, _ax = plot_gantt(
        schedule=improved_schedule,
        processing_times=processing_times,
        lower_bound=instance_bound,
    )
    _fig
    return


if __name__ == "__main__":
    app.run()
