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

    from eligibility_utils import (
        eligibility_table,
        load_instance,
        machine_loads,
        makespan,
        plot_gantt,
        summarize_schedule,
        validate_schedule,
    )

    return (
        Path,
        eligibility_table,
        load_instance,
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
    # OM 522 Eligible Machines: When Not Every Job Fits Every Machine

    On October 6 the data science team split one night's training runs among
    identical GPU machines. The fleet is now mixed. Each machine has 80, 40, or
    24 GB of memory, and a run can use a machine only if the machine has at
    least the memory the run needs. The set of machines that can run job $j$ is
    its **eligibility set** $E_j$. The 24 GB machines are an older generation
    that takes twice as long, so a run's time $p_{jk}$ depends on machine $k$.

    The goal is unchanged, i.e., the smallest makespan. Two things change. Every
    job must go to a machine in its eligibility set, and every load must use the
    job's time on the machine that runs it.

    Lines marked `# IN CLASS` are the lines we work through together.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Instance settings

    `instance_id` picks one of the ten nightly queues in `data/`, or `"toy"` for
    the board example. Each queue comes with its own fleet, so the number of
    machines is part of the data.
    """)
    return


@app.cell
def _(Path):
    data_dir = Path(__file__).parent / "data"
    instances = sorted(path.name for path in data_dir.glob("instance_*"))

    instances
    return (data_dir,)


@app.cell
def _(data_dir, load_instance, pl):
    # "toy" runs the board example. For a real queue, set e.g.
    # instance_id = "instance_006".
    instance_id = "toy"

    if instance_id == "toy":
        # G1 has 80 GB, G2 has 40 GB, and G3 is an older 24 GB card that takes
        # twice as long. A job lists only the machines it is eligible for.
        processing_times = {
            "J1": {"G1": 5},
            "J2": {"G1": 5},
            "J3": {"G1": 5, "G2": 5, "G3": 10},
            "J4": {"G1": 4, "G2": 4, "G3": 8},
            "J5": {"G1": 2, "G2": 2},
            "J6": {"G1": 2, "G2": 2},
            "J7": {"G1": 2, "G2": 2, "G3": 4},
        }
        machines = ["G1", "G2", "G3"]
        fleet = pl.DataFrame(
            {
                "machine": machines,
                "memory_gb": [80, 40, 24],
                "slowdown": [1.0, 1.0, 2.0],
            }
        )
    else:
        processing_times, machines, _jobs, fleet = load_instance(data_dir / instance_id)

    # A job's time on a current card, which is all the October 6 method knows.
    base_minutes = {job: min(times.values()) for job, times in processing_times.items()}
    return base_minutes, fleet, instance_id, machines, processing_times


@app.cell
def _(base_minutes, fleet, machines, processing_times):
    print(f"Jobs: {len(processing_times)}, machines: {len(machines)}")
    print(f"Eligible job-machine pairs: {sum(len(times) for times in processing_times.values())}")
    print(f"Total minutes of work on current cards: {sum(base_minutes.values())}")
    fleet
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Tools for checking a schedule

    A schedule has the same shape as on October 6, a dictionary from each
    machine to its jobs in order. Processing times are now a dictionary of
    dictionaries, so `processing_times["J3"]["G3"]` is J3's minutes on G3, and
    `processing_times["J3"]` lists exactly the machines J3 may use.
    `eligibility_utils.py` provides the following:

    - `eligibility_table(processing_times, machines)` shows each job's minutes
      on each machine, with an empty cell where the job is not allowed.
    - `machine_loads` and `makespan` rebuild loads from the schedule, counting
      each job at its time on its own machine.
    - `validate_schedule(schedule, processing_times, machines)` raises an error
      that lists every unknown machine or job, every job scheduled zero times or
      more than once, and every job on a machine it is not eligible for.
    - `summarize_schedule` and `plot_gantt` work as on October 6.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1. Who can run where

    Read the table from the most restricted job down. A job with one eligible
    machine has no choice, so its time is committed to that machine before any
    method runs. A job with few eligible machines competes for the large-memory
    cards that every other job may also use.
    """)
    return


@app.cell
def _(eligibility_table, machines, pl, processing_times):
    _table = eligibility_table(processing_times, machines)
    print(
        _table.group_by("eligible")
        .agg(
            pl.len().alias("job_count"),
            pl.col("job").str.join(", ").alias("jobs"),
        )
        .sort("eligible")
    )
    _table
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2. What breaks if we ignore eligibility

    The cell below runs the October 6 LPT unchanged. It sees one time per job
    (the time on a current card) and treats every machine as identical. The
    checker then reports every assignment the fleet cannot run.
    """)
    return


@app.function
def identical_lpt(base_minutes, machines):
    """The October 6 LPT, which assumes every job can use every machine."""
    schedule = {machine: [] for machine in machines}
    loads = {machine: 0 for machine in machines}
    for job in sorted(base_minutes, key=lambda job: (-base_minutes[job], job)):
        machine = min(machines, key=lambda m: (loads[m], m))
        schedule[machine].append(job)
        loads[machine] += base_minutes[job]
    return schedule, loads


@app.cell
def _(base_minutes, instance_id, machines, processing_times, validate_schedule):
    unrestricted_schedule, _claimed_loads = identical_lpt(base_minutes, machines)
    print(f"{instance_id}: the October 6 LPT claims a makespan of {max(_claimed_loads.values())}")
    print(unrestricted_schedule)
    try:
        validate_schedule(
            schedule=unrestricted_schedule,
            processing_times=processing_times,
            machines=machines,
        )
        print("The checker accepts it.")
    except ValueError as _error:
        print(f"The checker rejects it:\n{_error}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3. Lower bounds

    Let $f_j$ be job $j$'s time on a current card, its fastest time. The makespan
    is at least the longest $f_j$.

    For the average-load bound, an older card does half the work of a current
    card in the same minutes, so it counts as half a machine. Give machine $k$
    a capacity $c_k$ of 1 for a current card and $\tfrac{1}{2}$ for an older
    card. By time $C_{\max}$, machine $k$ has done at most $c_k C_{\max}$
    current-card minutes of work.

    For any group of machines $S$, every job with $E_j \subseteq S$ must run
    somewhere in $S$, so

    $$C_{\max} \ge \left\lceil \frac{\sum_{j:\,E_j \subseteq S} f_j}{\sum_{k \in S} c_k} \right\rceil$$

    With $S$ equal to the whole fleet this is the October 6 average-load bound,
    with the older cards counted at half. With $S$ equal to the large-memory
    machines it shows how much work is confined to them. We check every group
    that is some job's eligibility set, plus the whole fleet, and the largest
    value is the bound.
    """)
    return


@app.cell
def _(math):
    def lower_bounds(processing_times, base_minutes, capacity):
        bounds = {"longest job": max(base_minutes.values())}
        groups = {frozenset(times) for times in processing_times.values()}
        groups.add(frozenset(capacity))
        for group in sorted(groups, key=lambda g: (len(g), sorted(g))):
            confined = [job for job, times in processing_times.items() if set(times) <= group]
            # IN CLASS: the group's capacity, counting an older card as half a machine.
            group_capacity = sum(capacity[machine] for machine in group)
            bounds["jobs confined to " + ", ".join(sorted(group))] = math.ceil(
                sum(base_minutes[job] for job in confined) / group_capacity
            )
        return bounds

    return (lower_bounds,)


@app.cell
def _(base_minutes, fleet, instance_id, lower_bounds, processing_times):
    # Capacity in current-card machines, e.g., 0.5 for an older card.
    capacity = {
        machine: 1 / slowdown
        for machine, slowdown in fleet.select("machine", "slowdown").iter_rows()
    }
    _bounds = lower_bounds(processing_times, base_minutes, capacity)
    for _name, _value in _bounds.items():
        print(f"{_name}: {_value}")
    instance_bound = max(_bounds.values())
    print(f"{instance_id}: lower bound {instance_bound} minutes")
    return (instance_bound,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 4. Eligibility-aware LPT

    Sort the jobs by fastest eligible time, longest first. Give each job to the
    eligible machine that would **finish it earliest**, i.e., the smallest
    current load plus the job's time on that machine. Ties go to the lower job
    ID and the lower machine ID.

    On October 6 the least-loaded machine and the earliest finish were the same
    machine, because every job took the same time everywhere. With an older,
    slower machine they can differ. Setting `by_completion=False` gives each job
    to its least-loaded eligible machine instead, for comparison.
    """)
    return


@app.function
def lpt(processing_times, machines, by_completion=True):
    schedule = {machine: [] for machine in machines}
    loads = {machine: 0 for machine in machines}
    fastest = {job: min(times.values()) for job, times in processing_times.items()}
    # IN CLASS: longest fastest time first, ties broken by job ID.
    lpt_order = sorted(processing_times, key=lambda job: (-fastest[job], job))
    for job in lpt_order:
        eligible = processing_times[job]  # only the machines this job may use
        if by_completion:
            # IN CLASS: the eligible machine that finishes the job earliest.
            machine = min(eligible, key=lambda m: (loads[m] + eligible[m], m))
        else:
            machine = min(eligible, key=lambda m: (loads[m], m))
        schedule[machine].append(job)
        loads[machine] += eligible[machine]
    return schedule


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 5. Check and plot the LPT schedule
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
        processing_times=processing_times,
        machines=machines,
    )
    _lpt_makespan = makespan(lpt_schedule, processing_times)
    _least_load_makespan = makespan(
        lpt(processing_times, machines, by_completion=False),
        processing_times,
    )
    print(
        f"{instance_id}: LPT makespan {_lpt_makespan} minutes against a lower bound "
        f"of {instance_bound}, a gap of {_lpt_makespan - instance_bound} minutes"
    )
    print(f"Choosing the least-loaded eligible machine instead gives {_least_load_makespan}")
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
    ## Step 6. Eligibility-aware insertion and interchange

    The moves are the October 6 moves with two changes.

    - **A move must keep every job eligible.** Insertion of job $j$ from $a$ to
      $b$ needs $b \in E_j$. Interchange of $j$ on $a$ with $i$ on $b$ needs
      $b \in E_j$ and $a \in E_i$. We filter while generating moves, so an
      ineligible neighbor is never built.
    - **A job's time changes when it moves.** On October 6 the minutes that left
      $a$ were the minutes that arrived at $b$. Now job $j$ leaves $a$ at
      $p_{ja}$ and arrives at $b$ at $p_{jb}$, so we compute both new loads
      directly:

    $$L_a' = L_a - p_{ja} + p_{ia}, \qquad L_b' = L_b - p_{ib} + p_{jb}$$

    with the $i$ terms dropped for an insertion. As before, only a machine at
    the makespan gives up work, and a move is acceptable when both new loads
    are below $L_a$. Among acceptable moves, the loop takes the one whose
    larger new load is smallest, and it repeats until no acceptable move
    remains.
    """)
    return


@app.cell
def _(machine_loads, makespan):
    def improve(schedule, processing_times):
        # Work on a copy, because the loop changes the lists in place and the
        # LPT schedule must survive for the comparison.
        schedule = {m: list(jobs) for m, jobs in schedule.items()}
        p = processing_times
        moves = []
        while True:
            loads = machine_loads(schedule, p)
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
                    for j in schedule[a]:
                        # IN CLASS: j may move to b only if b is eligible for j.
                        if b not in p[j]:
                            continue
                        # Insertion: move j from a to b.
                        new_a = loads[a] - p[j][a]
                        new_b = loads[b] + p[j][b]
                        if max(new_a, new_b) < loads[a]:
                            candidates.append((max(new_a, new_b), a, b, j, None))
                        # Interchange: swap j on a with job i on b.
                        for i in schedule[b]:
                            # IN CLASS: i may come back to a only if a is eligible for i.
                            if a not in p[i]:
                                continue
                            # IN CLASS: each job counts at its time on its new machine.
                            new_a = loads[a] - p[j][a] + p[i][a]
                            new_b = loads[b] - p[i][b] + p[j][b]
                            if max(new_a, new_b) < loads[a]:
                                candidates.append((max(new_a, new_b), a, b, j, i))

            if not candidates:
                return schedule, moves
            # Take the move whose larger new load is smallest.
            _, a, b, j, i = min(candidates, key=lambda move: move[0])
            schedule[a].remove(j)
            schedule[b].append(j)
            if i is not None:
                schedule[b].remove(i)
                schedule[a].append(i)
            moves.append((a, b, j, i, makespan(schedule, p)))

    return (improve,)


@app.function
def print_moves(moves, processing_times):
    """Print one line per move accepted by improve()."""
    p = processing_times
    for number, (a, b, j, i, cmax_after) in enumerate(moves, start=1):
        if i is None:
            action = f"move {j} from {a} ({p[j][a]}) to {b} ({p[j][b]})"
        else:
            action = (
                f"swap {j} on {a} with {i} on {b}: "
                f"{j} goes {p[j][a]} -> {p[j][b]}, {i} goes {p[i][b]} -> {p[i][a]}"
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
        processing_times=processing_times,
        machines=machines,
    )
    print(f"{instance_id}, starting from the LPT schedule")
    print_moves(moves, processing_times)
    return (improved_schedule,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 7. Compare
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 8. Who is using the scarce machines

    The table lists each machine's jobs in the improved schedule, with the
    number of machines each job could have used in parentheses. A job that
    could run anywhere but sits on a large-memory card is feasible, but it uses
    capacity that a restricted job cannot get anywhere else.

    **Question.** Should a flexible job ever take the only machine a restricted
    job can use? When does it help the makespan, and when does it only look
    efficient?
    """)
    return


@app.cell
def _(fleet, improved_schedule, machine_loads, pl, processing_times):
    _loads = machine_loads(improved_schedule, processing_times)
    (
        fleet.select("machine", "memory_gb")
        .join(
            pl.DataFrame(
                [
                    {
                        "machine": _machine,
                        "load_minutes": _loads[_machine],
                        "jobs (eligible machines)": ", ".join(
                            f"{_job} ({len(processing_times[_job])})" for _job in _jobs
                        ),
                    }
                    for _machine, _jobs in improved_schedule.items()
                ]
            ),
            on="machine",
        )
        .sort("machine")
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 9. A different shape: a two-stage flow shop

    Each training run is first prepared on a CPU node and then trained on the
    GPU, and the runs keep one order at both machines. The only decision is the
    order. Johnson's rule (1954) finds the order with the smallest makespan:
    runs whose prep is shorter than their training go first, shortest prep
    first, and the rest go last, longest training first.

    The cell checks the rule against all 120 orders of the five runs. Johnson's
    rule is optimal only for two stages and the makespan. Option 6 has more
    stages and due dates, so there it is a starting point, not an answer.
    """)
    return


@app.function
def flow_makespan(order, prep_train):
    """Makespan when the runs go through prep and then training in `order`."""
    prep_free = gpu_free = 0
    for run in order:
        prep, train = prep_train[run]
        prep_free += prep
        gpu_free = max(prep_free, gpu_free) + train
    return gpu_free


@app.function
def johnson_order(prep_train):
    """Johnson's rule for two stages, with ties broken by run ID."""
    # IN CLASS: runs with a shorter prep than training go first, shortest prep first.
    first = sorted(
        (run for run, (prep, train) in prep_train.items() if prep < train),
        key=lambda run: (prep_train[run][0], run),
    )
    # IN CLASS: the rest go last, longest training first.
    last = sorted(
        (run for run, (prep, train) in prep_train.items() if prep >= train),
        key=lambda run: (-prep_train[run][1], run),
    )
    return first + last


@app.cell
def _(pl):
    from itertools import permutations as _permutations

    # Minutes of prep, then minutes of training, for each run.
    prep_train = {"A": (4, 6), "B": (7, 3), "C": (2, 5), "D": (6, 7), "E": (5, 2)}

    _total = {_run: sum(_times) for _run, _times in prep_train.items()}
    _orders = {
        "Letter order": sorted(prep_train),
        "Longest total first": sorted(prep_train, key=lambda _run: (-_total[_run], _run)),
        "Shortest total first": sorted(prep_train, key=lambda _run: (_total[_run], _run)),
        "Johnson's rule": johnson_order(prep_train),
    }
    _all = [flow_makespan(_order, prep_train) for _order in _permutations(prep_train)]
    _bound = max(
        sum(_prep for _prep, _ in prep_train.values()) + min(_train for _, _train in prep_train.values()),
        min(_prep for _prep, _ in prep_train.values()) + sum(_train for _, _train in prep_train.values()),
    )
    print(f"Lower bound {_bound} minutes")
    print(f"Best of {len(_all)} orders {min(_all)}, reached by {_all.count(min(_all))}; worst {max(_all)}")
    pl.DataFrame(
        {
            "rule": list(_orders),
            "order": [", ".join(_order) for _order in _orders.values()],
            "makespan": [flow_makespan(_order, prep_train) for _order in _orders.values()],
        }
    )
    return (prep_train,)


if __name__ == "__main__":
    app.run()
