import itertools
import json
import random
from pathlib import Path

import matplotlib
import polars as pl
import pytest

from eligibility_utils import (
    eligibility_table,
    load_instance,
    machine_loads,
    makespan,
    plot_gantt,
    summarize_schedule,
    validate_schedule,
)
from eligible_machines import flow_makespan, identical_lpt, johnson_order, lpt
from generate_eligibility_data import (
    BASE_MINUTES_RANGE,
    INSTANCE_COUNT,
    JOB_COUNT_RANGE,
    SEED,
    generate_instance,
)

matplotlib.use("Agg")

DATA_DIR = Path(__file__).parents[1] / "data"

# The board example: G1 has 80 GB, G2 has 40 GB, and G3 is an older 24 GB card
# that takes twice as long.
TOY_TIMES = {
    "J1": {"G1": 5},
    "J2": {"G1": 5},
    "J3": {"G1": 5, "G2": 5, "G3": 10},
    "J4": {"G1": 4, "G2": 4, "G3": 8},
    "J5": {"G1": 2, "G2": 2},
    "J6": {"G1": 2, "G2": 2},
    "J7": {"G1": 2, "G2": 2, "G3": 4},
}
TOY_MACHINES = ["G1", "G2", "G3"]
TOY_LPT = {"G1": ["J1", "J2"], "G2": ["J3", "J5", "J6", "J7"], "G3": ["J4"]}


def test_stored_data_matches_the_generator():
    manifest = json.loads((DATA_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["seed"] == SEED
    assert len(manifest["instances"]) == INSTANCE_COUNT

    rng = random.Random(SEED)
    for entry in manifest["instances"]:
        directory = DATA_DIR / entry["directory"]
        jobs, machines, times = generate_instance(rng)
        assert pl.read_parquet(directory / "jobs.parquet").equals(jobs)
        assert pl.read_parquet(directory / "machines.parquet").equals(machines)
        assert pl.read_parquet(directory / "processing_times.parquet").equals(times)
        assert JOB_COUNT_RANGE[0] <= jobs.height <= JOB_COUNT_RANGE[1]
        assert jobs.get_column("base_minutes").is_between(*BASE_MINUTES_RANGE).all()
        assert times.height == entry["eligible_pair_count"]
        # Every job has at least one eligible machine.
        assert set(times.get_column("job")) == set(jobs.get_column("job"))


def test_load_instance_keeps_only_eligible_pairs():
    processing_times, machines, jobs, fleet = load_instance(DATA_DIR / "instance_006")
    assert machines == fleet.get_column("machine").to_list()
    assert set(processing_times) == set(jobs.get_column("job"))
    memory = dict(fleet.select("machine", "memory_gb").iter_rows())
    for job, need in jobs.select("job", "memory_gb").iter_rows():
        assert set(processing_times[job]) == {m for m in machines if memory[m] >= need}


def test_eligibility_table_puts_restricted_jobs_first():
    table = eligibility_table(TOY_TIMES, TOY_MACHINES)
    assert table.get_column("job").to_list()[:2] == ["J1", "J2"]
    assert table.filter(pl.col("job") == "J5").item(0, "G3") is None


def test_loads_use_each_jobs_time_on_its_machine():
    assert machine_loads(TOY_LPT, TOY_TIMES) == {"G1": 10, "G2": 11, "G3": 8}
    assert makespan(TOY_LPT, TOY_TIMES) == 11
    assert makespan({}, TOY_TIMES) == 0
    with pytest.raises(ValueError, match="J1 is not eligible for G3"):
        machine_loads({"G3": ["J1"]}, TOY_TIMES)


def test_validate_schedule_accepts_a_feasible_schedule():
    validate_schedule(
        schedule=TOY_LPT,
        processing_times=TOY_TIMES,
        machines=TOY_MACHINES,
    )


def test_validate_schedule_reports_every_problem():
    broken = {
        "G1": ["J1", "J1"],
        "G2": ["J2", "J9"],
        "G3": ["J5", "J3"],
        "G4": ["J4"],
    }
    with pytest.raises(ValueError) as error:
        validate_schedule(
            schedule=broken,
            processing_times=TOY_TIMES,
            machines=TOY_MACHINES,
        )
    message = str(error.value)
    assert "Unknown machine G4" in message
    assert "unknown job J9" in message
    assert "J2 is on G2 but is eligible only for G1." in message
    assert "J5 is on G3 but is eligible only for G1, G2." in message
    assert "Unscheduled jobs: J6, J7." in message
    assert "more than once: J1." in message


def test_validate_schedule_rejects_a_string_of_jobs():
    with pytest.raises(ValueError, match="holds a string"):
        validate_schedule(
            schedule={"G1": "J1"},
            processing_times={"J1": {"G1": 5}},
            machines=["G1"],
        )


def test_identical_lpt_breaks_eligibility_on_the_toy():
    base_minutes = {job: min(times.values()) for job, times in TOY_TIMES.items()}
    schedule, claimed_loads = identical_lpt(base_minutes, TOY_MACHINES)
    assert max(claimed_loads.values()) == 9
    with pytest.raises(ValueError, match="J2 is on G2"):
        validate_schedule(
            schedule=schedule,
            processing_times=TOY_TIMES,
            machines=TOY_MACHINES,
        )


def test_lpt_by_completion_beats_least_load_on_the_toy():
    assert lpt(TOY_TIMES, TOY_MACHINES) == TOY_LPT
    assert makespan(lpt(TOY_TIMES, TOY_MACHINES, by_completion=False), TOY_TIMES) == 12


def test_toy_optimum_is_ten_by_enumeration():
    # Try all 1 * 1 * 3 * 3 * 2 * 2 * 3 = 108 eligible assignments, independent
    # of any heuristic.
    jobs = list(TOY_TIMES)
    best = min(
        max(
            sum(TOY_TIMES[job][machine] for job, machine in zip(jobs, choice) if machine == m)
            for m in TOY_MACHINES
        )
        for choice in itertools.product(*(TOY_TIMES[job] for job in jobs))
    )
    assert best == 10


def test_summarize_schedule_has_one_row_per_machine():
    summary = summarize_schedule(TOY_LPT, TOY_TIMES)
    assert summary.get_column("machine").to_list() == TOY_MACHINES
    assert summary.get_column("load_minutes").to_list() == [10, 11, 8]
    assert summary.get_column("job_count").to_list() == [2, 4, 1]
    assert summary.item(1, "jobs") == "J3, J5, J6, J7"


def test_plot_gantt_draws_every_job_at_its_machine_time():
    figure, axes = plot_gantt(
        schedule=TOY_LPT,
        processing_times=TOY_TIMES,
        lower_bound=10,
    )
    assert len(axes.patches) == len(TOY_TIMES)
    # J4 is the only job on G3 and runs 8 minutes there.
    assert any(patch.get_width() == 8 for patch in axes.patches)
    assert axes.get_title() == "Makespan 11 minutes (orange machines set it)"
    assert [label.get_text() for label in axes.get_yticklabels()] == TOY_MACHINES
    assert any(line.get_linestyle() == "--" for line in axes.get_lines())
    matplotlib.pyplot.close(figure)


FLOW_RUNS = {"A": (4, 6), "B": (7, 3), "C": (2, 5), "D": (6, 7), "E": (5, 2)}


def test_johnson_order_on_the_board_runs():
    assert johnson_order(FLOW_RUNS) == ["C", "A", "D", "B", "E"]
    makespans = [flow_makespan(order, FLOW_RUNS) for order in itertools.permutations(FLOW_RUNS)]
    assert flow_makespan(johnson_order(FLOW_RUNS), FLOW_RUNS) == min(makespans) == 26
    assert makespans.count(26) == 2 and max(makespans) == 36


def test_johnson_order_is_optimal_on_random_two_stage_instances():
    rng = random.Random(1013)
    for _ in range(200):
        runs = {f"R{i}": (rng.randint(1, 9), rng.randint(1, 9)) for i in range(6)}
        best = min(flow_makespan(order, runs) for order in itertools.permutations(runs))
        assert flow_makespan(johnson_order(runs), runs) == best
