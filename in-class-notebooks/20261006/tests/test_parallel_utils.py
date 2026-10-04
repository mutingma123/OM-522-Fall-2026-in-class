import json
import random
from pathlib import Path

import matplotlib
import polars as pl
import pytest

from generate_parallel_data import (
    INSTANCE_COUNT,
    JOB_COUNT_RANGE,
    PROCESSING_TIME_RANGE,
    SEED,
    generate_instance,
)
from parallel_utils import (
    machine_loads,
    makespan,
    plot_gantt,
    summarize_schedule,
    validate_schedule,
)

matplotlib.use("Agg")

DATA_DIR = Path(__file__).parents[1] / "data"

# The seven-job board example: processing times 5, 5, 4, 4, 3, 3, 3 on three machines.
TOY_TIMES = {"J1": 5, "J2": 5, "J3": 4, "J4": 4, "J5": 3, "J6": 3, "J7": 3}
TOY_MACHINES = ["M1", "M2", "M3"]
TOY_LPT = {"M1": ["J1", "J5", "J7"], "M2": ["J2", "J6"], "M3": ["J3", "J4"]}


def test_stored_data_matches_the_generator():
    manifest = json.loads((DATA_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["seed"] == SEED
    assert len(manifest["instances"]) == INSTANCE_COUNT

    rng = random.Random(SEED)
    for entry in manifest["instances"]:
        stored = pl.read_parquet(DATA_DIR / entry["jobs_file"])
        assert stored.equals(generate_instance(rng))
        assert stored.height == entry["job_count"]
        assert JOB_COUNT_RANGE[0] <= stored.height <= JOB_COUNT_RANGE[1]
        assert stored.get_column("processing_time").is_between(*PROCESSING_TIME_RANGE).all()
        assert stored.get_column("job").is_unique().all()
        assert int(stored.get_column("processing_time").sum()) == entry["total_processing_time"]


def test_loads_and_makespan_are_rebuilt_from_the_schedule():
    assert machine_loads(TOY_LPT, TOY_TIMES) == {"M1": 11, "M2": 8, "M3": 8}
    assert makespan(TOY_LPT, TOY_TIMES) == 11
    assert makespan({}, TOY_TIMES) == 0
    assert machine_loads({"M1": [], "M2": ["J1"]}, TOY_TIMES) == {"M1": 0, "M2": 5}


def test_validate_schedule_accepts_a_feasible_schedule():
    validate_schedule(
        schedule=TOY_LPT,
        jobs=TOY_TIMES,
        machines=TOY_MACHINES,
    )


def test_validate_schedule_reports_every_problem():
    broken = {
        "M1": ["J1", "J5", "J7", "J1"],
        "M2": ["J2", "J9"],
        "M4": ["J3"],
    }
    with pytest.raises(ValueError) as error:
        validate_schedule(
            schedule=broken,
            jobs=TOY_TIMES,
            machines=TOY_MACHINES,
        )
    message = str(error.value)
    assert "Unknown machine M4" in message
    assert "unknown job J9" in message
    assert "Unscheduled jobs: J4, J6." in message
    assert "more than once: J1." in message


def test_validate_schedule_rejects_a_string_of_jobs():
    with pytest.raises(ValueError, match="holds a string"):
        validate_schedule(
            schedule={"M1": "J1"},
            jobs=["J1"],
            machines=["M1"],
        )


def test_summarize_schedule_has_one_row_per_machine():
    summary = summarize_schedule(TOY_LPT, TOY_TIMES)
    assert summary.get_column("machine").to_list() == TOY_MACHINES
    assert summary.get_column("load_minutes").to_list() == [11, 8, 8]
    assert summary.get_column("job_count").to_list() == [3, 2, 2]
    assert summary.item(0, "jobs") == "J1, J5, J7"


def test_plot_gantt_draws_every_job_and_the_bound():
    figure, axes = plot_gantt(
        schedule=TOY_LPT,
        processing_times=TOY_TIMES,
        lower_bound=9,
    )
    assert len(axes.patches) == len(TOY_TIMES)
    assert axes.get_title() == "Makespan 11 minutes (orange mills set it)"
    assert [label.get_text() for label in axes.get_yticklabels()] == TOY_MACHINES
    assert any(line.get_linestyle() == "--" for line in axes.get_lines())
    matplotlib.pyplot.close(figure)
