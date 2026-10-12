"""Utilities for checking, summarizing, and plotting schedules on eligible machines.

A schedule is a dictionary that maps each machine to the list of jobs it
processes, in processing order, e.g., ``{"G1": ["J03", "J07"], "G2": ["J01"]}``.
Every machine starts at time 0 and runs its jobs back to back, so a machine's
load is also its completion time.

Processing times are a dictionary of dictionaries, e.g.,
``{"J01": {"G1": 30, "G3": 60}}``. ``processing_times[job][machine]`` is the
job's minutes on that machine, and the machines listed for a job are exactly
the machines it is eligible for. A machine missing from a job's dictionary
cannot run that job.
"""

from collections.abc import Collection, Mapping, Sequence
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure


Schedule = Mapping[str, Sequence[str]]
ProcessingTimes = Mapping[str, Mapping[str, int]]


def load_instance(
    instance_directory: Path,
) -> tuple[ProcessingTimes, list[str], pl.DataFrame, pl.DataFrame]:
    """Read one instance into processing times, machines, and the two tables.

    Args:
        instance_directory: Folder with ``jobs.parquet``, ``machines.parquet``,
            and ``processing_times.parquet``.

    Returns:
        tuple: ``processing_times[job][machine]`` for every eligible pair, the
            machine IDs in order, the jobs table, and the machines table.
    """
    jobs = pl.read_parquet(instance_directory / "jobs.parquet")
    machines = pl.read_parquet(instance_directory / "machines.parquet")
    times = pl.read_parquet(instance_directory / "processing_times.parquet")
    processing_times = {job: {} for job in jobs.get_column("job")}
    for job, machine, minutes in times.iter_rows():
        processing_times[job][machine] = minutes
    return processing_times, machines.get_column("machine").to_list(), jobs, machines


def eligibility_table(
    processing_times: ProcessingTimes,
    machines: Sequence[str],
) -> pl.DataFrame:
    """Return one row per job with its minutes on each machine.

    An empty cell means the job is not eligible for that machine. The
    ``eligible`` column counts the machines that can run the job, and rows
    are sorted so the most restricted jobs come first.

    Args:
        processing_times: Minutes for each eligible job-machine pair.
        machines: Machine IDs, in column order.

    Returns:
        pl.DataFrame: Columns ``job``, ``eligible``, and one column per machine.
    """
    rows = [
        {
            "job": job,
            "eligible": len(times),
            **{machine: times.get(machine) for machine in machines},
        }
        for job, times in processing_times.items()
    ]
    schema = {"job": pl.String, "eligible": pl.Int64} | {machine: pl.Int64 for machine in machines}
    return pl.DataFrame(rows, schema=schema).sort("eligible", "job")


def machine_loads(
    schedule: Schedule,
    processing_times: ProcessingTimes,
) -> dict[str, int]:
    """Return each machine's load, rebuilt from the schedule.

    Each job counts at its time on the machine that runs it.

    Args:
        schedule: Jobs on each machine, in processing order.
        processing_times: Minutes for each eligible job-machine pair.

    Returns:
        dict[str, int]: Total processing time assigned to each machine. A machine
            with no jobs has load 0.

    Raises:
        ValueError: If a job sits on a machine it is not eligible for, since
            that pair has no processing time.
    """
    loads = {}
    for machine, jobs in schedule.items():
        load = 0
        for job in jobs:
            if machine not in processing_times[job]:
                raise ValueError(
                    f"{job} is not eligible for {machine}, so it has no time there. "
                    "Run validate_schedule to list every problem."
                )
            load += processing_times[job][machine]
        loads[machine] = load
    return loads


def makespan(
    schedule: Schedule,
    processing_times: ProcessingTimes,
) -> int:
    """Return the latest machine completion time, rebuilt from the schedule.

    Args:
        schedule: Jobs on each machine, in processing order.
        processing_times: Minutes for each eligible job-machine pair.

    Returns:
        int: The largest machine load, or 0 for an empty schedule.
    """
    return max(machine_loads(schedule, processing_times).values(), default=0)


def validate_schedule(
    schedule: Schedule,
    processing_times: ProcessingTimes,
    machines: Collection[str],
) -> None:
    """Raise ValueError listing every way ``schedule`` fails to be feasible.

    A feasible schedule uses only the listed machines, assigns every job to
    exactly one machine, and puts every job on a machine it is eligible for.
    The function returns nothing when the schedule is feasible. It never reuses
    loads computed by the method being checked.

    Args:
        schedule: Jobs on each machine, in processing order.
        processing_times: Minutes for each eligible job-machine pair. Its keys
            are the jobs that must each be scheduled exactly once.
        machines: Machine IDs that may receive jobs.

    Raises:
        ValueError: If a machine is unknown, a job is unknown, unscheduled,
            scheduled more than once, or on a machine it is not eligible for.
    """
    if isinstance(schedule, (list, tuple)):
        raise TypeError("schedule must be a dictionary of machine -> list of jobs.")

    machine_set = set(machines)
    problems = []
    counts: dict[str, int] = {}
    for machine, machine_jobs in schedule.items():
        if machine not in machine_set:
            problems.append(f"Unknown machine {machine}.")
        if isinstance(machine_jobs, str):
            problems.append(f"Machine {machine} holds a string, not a list of jobs.")
            continue
        for job in machine_jobs:
            if job not in processing_times:
                problems.append(f"Machine {machine} has unknown job {job}.")
                continue
            counts[job] = counts.get(job, 0) + 1
            if machine in machine_set and machine not in processing_times[job]:
                eligible = ", ".join(sorted(processing_times[job]))
                problems.append(f"{job} is on {machine} but is eligible only for {eligible}.")

    unscheduled = sorted(set(processing_times) - set(counts))
    repeated = sorted(job for job, count in counts.items() if count > 1)
    if unscheduled:
        problems.append(f"Unscheduled jobs: {', '.join(unscheduled)}.")
    if repeated:
        problems.append(f"Jobs scheduled more than once: {', '.join(repeated)}.")
    if problems:
        raise ValueError("\n".join(problems))


def summarize_schedule(
    schedule: Schedule,
    processing_times: ProcessingTimes,
) -> pl.DataFrame:
    """Return one row per machine with its jobs, job count, and load.

    Args:
        schedule: Jobs on each machine, in processing order.
        processing_times: Minutes for each eligible job-machine pair.

    Returns:
        pl.DataFrame: Columns ``machine``, ``jobs``, ``job_count``, and
            ``load_minutes``, sorted by machine.
    """
    loads = machine_loads(schedule, processing_times)
    return pl.DataFrame(
        [
            {
                "machine": machine,
                "jobs": ", ".join(schedule[machine]),
                "job_count": len(schedule[machine]),
                "load_minutes": loads[machine],
            }
            for machine in sorted(schedule)
        ],
        schema={
            "machine": pl.String,
            "jobs": pl.String,
            "job_count": pl.Int64,
            "load_minutes": pl.Int64,
        },
    )


def plot_gantt(
    schedule: Schedule,
    processing_times: ProcessingTimes,
    lower_bound: float | None = None,
    title: str | None = None,
    figsize: tuple[float, float] = (9, 4),
) -> tuple[Figure, Axes]:
    """Draw one horizontal bar per machine with its jobs back to back.

    Each job is drawn at its time on the machine that runs it. Jobs on every
    machine that sets the makespan are drawn in orange, and every bar ends with
    its load. An optional lower bound is drawn as a dashed vertical line, so the
    gap between the schedule and the best makespan any schedule could reach is
    visible.

    Args:
        schedule: Jobs on each machine, in processing order.
        processing_times: Minutes for each eligible job-machine pair.
        lower_bound: Makespan lower bound to draw, or None to omit it.
        title: Axes title, or None for a title that states the makespan.
        figsize: Figure width and height in inches.

    Returns:
        tuple[Figure, Axes]: The Matplotlib figure and axes.
    """
    machines = sorted(schedule)
    loads = machine_loads(schedule, processing_times)
    cmax = max(loads.values(), default=0)
    palette = sns.color_palette(palette="colorblind")
    other_color, makespan_color = palette[0], palette[1]

    figure, axes = plt.subplots(
        nrows=1,
        ncols=1,
        figsize=figsize,
        layout="constrained",
    )
    axes.set_axisbelow(True)
    axes.yaxis.grid(False)
    for row, machine in enumerate(machines):
        on_makespan = cmax > 0 and loads[machine] == cmax
        start = 0
        for job in schedule[machine]:
            duration = processing_times[job][machine]
            axes.barh(
                y=row,
                width=duration,
                left=start,
                height=0.6,
                color=makespan_color if on_makespan else other_color,
                edgecolor="k",
                linewidth=0.8,
                alpha=0.8,
                zorder=2,
            )
            axes.text(
                x=start + duration / 2,
                y=row,
                s=job,
                ha="center",
                va="center",
                fontsize=8,
                zorder=3,
            )
            start += duration
        axes.text(
            x=loads[machine] + cmax * 0.012,
            y=row,
            s=str(loads[machine]),
            ha="left",
            va="center",
            fontsize=9,
            fontweight="bold" if on_makespan else "normal",
            bbox={"boxstyle": "square,pad=0.1", "facecolor": "white", "edgecolor": "none"},
            zorder=4,
        )

    if lower_bound is not None:
        axes.axvline(
            x=lower_bound,
            color="#d62728",
            linestyle="--",
            linewidth=1.2,
            zorder=1,
        )
        axes.annotate(
            text=f"Lower bound {lower_bound:g}",
            xy=(lower_bound, 1.0),
            xycoords=("data", "axes fraction"),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            color="#d62728",
        )

    axes.set_yticks(
        ticks=range(len(machines)),
        labels=machines,
    )
    axes.invert_yaxis()
    axes.set_xlim(0, cmax * 1.08 if cmax else 1)
    axes.set_xlabel("Minutes from the start of the night")
    axes.set_title(
        title if title is not None else f"Makespan {cmax} minutes (orange machines set it)",
        pad=16 if lower_bound is not None else 6,
    )
    sns.despine(ax=axes)
    return figure, axes
