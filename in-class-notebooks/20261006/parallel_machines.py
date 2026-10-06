import marimo

__generated_with = "0.24.0"
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
        plt,
        sns,
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

    `instance_id` picks one of the ten nightly queues in `data/`, and
    `machine_count` sets the number of identical GPU machines.
    """)
    return


@app.cell
def _():
    instance_id = "instance_007"
    machine_count = 5
    return instance_id, machine_count


@app.cell
def _(Path, instance_id, machine_count, pl):
    data_dir = Path(__file__).parent / "data"
    jobs = pl.read_parquet(data_dir / instance_id / "jobs.parquet")

    # processing_times["J01"] gives that job's minutes, as demand did for routing.
    processing_times = {
        job: minutes
        for job, minutes in jobs.iter_rows()
    }
    machines = [f"M{_number}" for _number in range(1, machine_count + 1)]
    return jobs, machines, processing_times


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


@app.cell
def _(jobs, plt, sns):
    _fig, _ax = plt.subplots(
        nrows=1,
        ncols=1,
        figsize=(6, 3.5),
    )
    sns.histplot(
        x=jobs.get_column("processing_time").to_list(),
        binwidth=5,
        edgecolor="k",
        ax=_ax,
    )
    _ax.set_title("Job processing times")
    _ax.set_xlabel("Minutes")
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The board example

    The seven jobs from the board, on three machines. Trace them by hand first,
    then use them to test the code before running it on the real queue.
    """)
    return


@app.cell
def _():
    toy_processing_times = {
        "J1": 5,
        "J2": 5,
        "J3": 4,
        "J4": 4,
        "J5": 3,
        "J6": 3,
        "J7": 3,
    }
    toy_machines = ["M1", "M2", "M3"]
    return toy_machines, toy_processing_times


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

    For example, the cell below deals the board jobs to the machines in turn, like
    cards, ignoring their sizes.
    """)
    return


@app.cell
def _(
    plot_gantt,
    summarize_schedule,
    toy_machines,
    toy_processing_times,
    validate_schedule,
):
    _dealt = {_machine: [] for _machine in toy_machines}
    for _position, _job in enumerate(toy_processing_times):
        _dealt[toy_machines[_position % len(toy_machines)]].append(_job)

    validate_schedule(
        schedule=_dealt,
        jobs=toy_processing_times,
        machines=toy_machines,
    )
    print(summarize_schedule(_dealt, toy_processing_times))
    _fig, _ax = plot_gantt(
        schedule=_dealt,
        processing_times=toy_processing_times,
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
def _(
    instance_id,
    lower_bound,
    machine_count,
    processing_times,
    toy_machines,
    toy_processing_times,
):
    toy_bound = lower_bound(toy_processing_times, len(toy_machines))
    instance_bound = lower_bound(processing_times, machine_count)

    print(f"Board example: lower bound {toy_bound} minutes")
    print(
        f"{instance_id}: longest job {max(processing_times.values())} minutes, "
        f"average load {sum(processing_times.values()) / machine_count:.1f} minutes, "
        f"lower bound {instance_bound} minutes"
    )
    return instance_bound, toy_bound


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2. LPT construction

    Sort the jobs from longest to shortest, then give each job to a machine with
    the smallest current load. Ties go to the lower job ID and the lower machine
    ID, so the result is reproducible.
    """)
    return


@app.cell
def _():
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

    return (lpt,)


@app.cell
def _(
    lpt,
    makespan,
    plot_gantt,
    summarize_schedule,
    toy_bound,
    toy_machines,
    toy_processing_times,
    validate_schedule,
):
    toy_lpt = lpt(toy_processing_times, toy_machines)

    validate_schedule(
        schedule=toy_lpt,
        jobs=toy_processing_times,
        machines=toy_machines,
    )
    print(
        f"Board example: LPT makespan {makespan(toy_lpt, toy_processing_times)} "
        f"minutes against a lower bound of {toy_bound}"
    )
    print(summarize_schedule(toy_lpt, toy_processing_times))
    _fig, _ax = plot_gantt(
        schedule=toy_lpt,
        processing_times=toy_processing_times,
        lower_bound=toy_bound,
        figsize=(7, 2.5),
    )
    _fig
    return (toy_lpt,)


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
    lpt,
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

    Insertion moves job $j$ from machine $a$ to machine $b$:
    $L_a' = L_a - p_j$ and $L_b' = L_b + p_j$.

    Interchange swaps job $j$ on machine $a$ with job $i$ on machine $b$:
    $L_a' = L_a - p_j + p_i$ and $L_b' = L_b - p_i + p_j$.

    Only moves out of a machine at the makespan are considered, and a move is
    acceptable when both changed loads end below the current makespan. Among
    acceptable moves, the loop takes the one with the smallest larger load and
    repeats until none remains.
    """)
    return


@app.cell
def _(machine_loads):
    def improve(schedule, processing_times):
        # Work on a copy, because the loop changes the lists in place and the
        # LPT schedule must survive for the comparison.
        schedule = {m: list(jobs) for m, jobs in schedule.items()}
        loads = machine_loads(schedule, processing_times)
        moves = []
        while True:
            cmax = max(loads.values())
            best = None
            for a in sorted(schedule):
                if loads[a] < cmax:
                    continue  # only machines at the makespan give up work
                for b in sorted(schedule):
                    if b == a:
                        continue
                    for j in schedule[a]:
                        # IN CLASS: insertion, the larger of the two changed loads
                        # after moving j from a to b.
                        new_max = max(
                            loads[a] - processing_times[j],
                            loads[b] + processing_times[j],
                        )
                        if new_max < cmax and (best is None or new_max < best[0]):
                            best = (new_max, a, b, j, None)
                        # Interchange: swap j on a with a shorter job i on b.
                        for i in schedule[b]:
                            delta = processing_times[j] - processing_times[i]
                            if delta <= 0:
                                continue
                            # IN CLASS: interchange, the larger of the two changed
                            # loads after the swap, written with delta.
                            new_max = max(loads[a] - delta, loads[b] + delta)
                            if new_max < cmax and (best is None or new_max < best[0]):
                                best = (new_max, a, b, j, i)
            if best is None:
                return schedule, moves
            _, a, b, j, i = best
            schedule[a].remove(j)
            schedule[b].append(j)
            loads[a] -= processing_times[j]
            loads[b] += processing_times[j]
            if i is not None:
                schedule[b].remove(i)
                schedule[a].append(i)
                loads[b] -= processing_times[i]
                loads[a] += processing_times[i]
            moves.append((a, b, j, i, max(loads.values())))

    return (improve,)


@app.cell
def _():
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

    return (print_moves,)


@app.cell
def _(
    improve,
    print_moves,
    toy_bound,
    toy_lpt,
    toy_machines,
    toy_processing_times,
    validate_schedule,
):
    toy_improved, toy_moves = improve(toy_lpt, toy_processing_times)

    validate_schedule(
        schedule=toy_improved,
        jobs=toy_processing_times,
        machines=toy_machines,
    )
    print(f"Board example, lower bound {toy_bound}")
    print_moves(toy_moves, toy_processing_times)
    return


@app.cell
def _(
    improve,
    instance_id,
    lpt_schedule,
    machines,
    print_moves,
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
