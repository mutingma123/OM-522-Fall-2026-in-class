"""Utilities for checking, summarizing, and plotting parallel-machine schedules.

A schedule is a dictionary that maps each machine to the list of jobs it
processes, in processing order, e.g., ``{"M1": ["J03", "J07"], "M2": ["J01"]}``.
Every machine starts at time 0 and runs its jobs back to back, so a machine's
load (the sum of its jobs' processing times) is also its completion time.
"""

from collections.abc import Collection, Mapping, Sequence

import matplotlib.pyplot as plt
import polars as pl
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure


Schedule = Mapping[str, Sequence[str]]


def machine_loads(
    schedule: Schedule,
    processing_times: Mapping[str, int],
) -> dict[str, int]:
    """Return each machine's load, rebuilt from the schedule.

    Args:
        schedule: Jobs on each machine, in processing order.
        processing_times: Minutes of processing for each job, keyed by job ID.

    Returns:
        dict[str, int]: Total processing time assigned to each machine. A machine
            with no jobs has load 0.
    """
    return {
        machine: sum(processing_times[job] for job in jobs)
        for machine, jobs in schedule.items()
    }


def makespan(
    schedule: Schedule,
    processing_times: Mapping[str, int],
) -> int:
    """Return the latest machine completion time, rebuilt from the schedule.

    Args:
        schedule: Jobs on each machine, in processing order.
        processing_times: Minutes of processing for each job, keyed by job ID.

    Returns:
        int: The largest machine load, or 0 for an empty schedule.
    """
    return max(machine_loads(schedule, processing_times).values(), default=0)


def validate_schedule(
    schedule: Schedule,
    jobs: Collection[str],
    machines: Collection[str],
) -> None:
    """Raise ValueError listing every way ``schedule`` fails to be feasible.

    A feasible schedule uses only the listed machines and assigns every job to
    exactly one machine. The function returns nothing when the schedule is
    feasible. It never reuses loads computed by the method being checked.

    Args:
        schedule: Jobs on each machine, in processing order.
        jobs: Job IDs that must each be scheduled exactly once.
        machines: Machine IDs that may receive jobs.

    Raises:
        ValueError: If a machine is unknown, a job is unknown, unscheduled, or
            scheduled more than once.
    """
    if isinstance(schedule, (list, tuple)):
        raise TypeError("schedule must be a dictionary of machine -> list of jobs.")

    job_set = set(jobs)
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
            if job not in job_set:
                problems.append(f"Machine {machine} has unknown job {job}.")
            else:
                counts[job] = counts.get(job, 0) + 1

    unscheduled = sorted(job_set - set(counts))
    repeated = sorted(job for job, count in counts.items() if count > 1)
    if unscheduled:
        problems.append(f"Unscheduled jobs: {', '.join(unscheduled)}.")
    if repeated:
        problems.append(f"Jobs scheduled more than once: {', '.join(repeated)}.")
    if problems:
        raise ValueError("\n".join(problems))


def summarize_schedule(
    schedule: Schedule,
    processing_times: Mapping[str, int],
) -> pl.DataFrame:
    """Return one row per machine with its jobs, job count, and load.

    Args:
        schedule: Jobs on each machine, in processing order.
        processing_times: Minutes of processing for each job, keyed by job ID.

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
    processing_times: Mapping[str, int],
    lower_bound: float | None = None,
    title: str | None = None,
    figsize: tuple[float, float] = (9, 4),
) -> tuple[Figure, Axes]:
    """Draw one horizontal bar per machine with its jobs back to back.

    Jobs on every machine that sets the makespan are drawn in orange, and every
    bar ends with its load. An optional lower bound is drawn as a dashed
    vertical line, so the gap between the schedule and the best makespan any
    schedule could reach is visible.

    Args:
        schedule: Jobs on each machine, in processing order.
        processing_times: Minutes of processing for each job, keyed by job ID.
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
            duration = processing_times[job]
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
    axes.set_xlabel("Minutes from the start of the shift")
    axes.set_title(
        title if title is not None else f"Makespan {cmax} minutes (orange mills set it)",
        pad=16 if lower_bound is not None else 6,
    )
    sns.despine(ax=axes)
    return figure, axes
