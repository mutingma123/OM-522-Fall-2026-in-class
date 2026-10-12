"""Generate the October 13 eligibility-constrained parallel-machine instances.

Each instance is one night's queue of model-training runs for a mixed fleet of
GPU machines. A machine has 80, 40, or 24 GB of memory, and a run can use a
machine only if the machine has at least the memory the run needs. The 80 and
40 GB machines are current cards, and the 24 GB machines are an older
generation that takes twice as long, so a run's time depends on its machine.

A job's ``base_minutes`` is its time on a current card. Its time on a machine
is ``base_minutes`` times the machine's slowdown, rounded up to a whole minute.
``processing_times.parquet`` holds one row per eligible job-machine pair, and a
pair that does not appear is not allowed, as in the option 1 project data.

Run with ``pixi run data``. The script refuses to overwrite existing data.
"""

import json
import math
import random
from pathlib import Path

import polars as pl


JOB_SCHEMA = {
    "job": pl.String,
    "memory_gb": pl.Int64,
    "base_minutes": pl.Int64,
}
MACHINE_SCHEMA = {
    "machine": pl.String,
    "memory_gb": pl.Int64,
    "slowdown": pl.Float64,
}
TIME_SCHEMA = {
    "job": pl.String,
    "machine": pl.String,
    "minutes": pl.Int64,
}
SEED = 1013
INSTANCE_COUNT = 10
JOB_COUNT_RANGE = (16, 22)
BASE_MINUTES_RANGE = (10, 60)
# Memory tier (GB) -> slowdown relative to a current card.
SLOWDOWN = {80: 1.0, 40: 1.0, 24: 2.0}
# Share of runs that need each amount of memory.
MEMORY_NEED_WEIGHTS = {24: 0.5, 40: 0.3, 80: 0.2}
# Each fleet has one or two machines of every tier, so every run has at least
# one eligible machine and the fleet has three to six machines.
MACHINES_PER_TIER_RANGE = (1, 2)
OUTPUT_DIRECTORY = Path(__file__).resolve().parent / "data"


def generate_machines(rng: random.Random) -> pl.DataFrame:
    """Sample a fleet, numbered from the largest memory tier down."""
    memories = []
    for memory_gb in sorted(SLOWDOWN, reverse=True):
        memories.extend([memory_gb] * rng.randint(*MACHINES_PER_TIER_RANGE))
    rows = [
        {
            "machine": f"G{index + 1}",
            "memory_gb": memory_gb,
            "slowdown": SLOWDOWN[memory_gb],
        }
        for index, memory_gb in enumerate(memories)
    ]
    return pl.DataFrame(rows, schema=MACHINE_SCHEMA)


def generate_jobs(rng: random.Random) -> pl.DataFrame:
    """Sample one night's runs with a memory need and a base time in minutes."""
    number_of_jobs = rng.randint(*JOB_COUNT_RANGE)
    needs = list(MEMORY_NEED_WEIGHTS)
    weights = list(MEMORY_NEED_WEIGHTS.values())
    rows = [
        {
            "job": f"J{index + 1:02d}",
            "memory_gb": rng.choices(needs, weights=weights)[0],
            "base_minutes": rng.randint(*BASE_MINUTES_RANGE),
        }
        for index in range(number_of_jobs)
    ]
    return pl.DataFrame(rows, schema=JOB_SCHEMA)


def eligible_times(jobs: pl.DataFrame, machines: pl.DataFrame) -> pl.DataFrame:
    """Return one row per eligible job-machine pair with its minutes."""
    rows = [
        {
            "job": job,
            "machine": machine,
            "minutes": math.ceil(base_minutes * slowdown),
        }
        for job, need, base_minutes in jobs.iter_rows()
        for machine, memory_gb, slowdown in machines.iter_rows()
        if memory_gb >= need
    ]
    return pl.DataFrame(rows, schema=TIME_SCHEMA)


def generate_instance(rng: random.Random) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Sample a fleet and a queue, then derive the eligible pairs."""
    machines = generate_machines(rng)
    jobs = generate_jobs(rng)
    return jobs, machines, eligible_times(jobs, machines)


def main() -> None:
    if OUTPUT_DIRECTORY.exists() and next(OUTPUT_DIRECTORY.iterdir(), None) is not None:
        raise FileExistsError(
            f"Output directory is not empty: {OUTPUT_DIRECTORY}. "
            "Remove it before regenerating the data."
        )

    rng = random.Random(SEED)
    instances = []
    for number in range(1, INSTANCE_COUNT + 1):
        instance_id = f"instance_{number:03d}"
        instance_directory = OUTPUT_DIRECTORY / instance_id
        instance_directory.mkdir(parents=True)
        jobs, machines, times = generate_instance(rng)
        jobs.write_parquet(instance_directory / "jobs.parquet", compression="zstd")
        machines.write_parquet(instance_directory / "machines.parquet", compression="zstd")
        times.write_parquet(instance_directory / "processing_times.parquet", compression="zstd")
        instances.append(
            {
                "instance_id": instance_id,
                "job_count": jobs.height,
                "machine_count": machines.height,
                "eligible_pair_count": times.height,
                "directory": instance_id,
            }
        )
        print(f"{instance_id}: {jobs.height} jobs, {machines.height} machines")

    manifest = {
        "generator": "generate_eligibility_data.py",
        "rng": "random.Random, one seed for all instances in order",
        "seed": SEED,
        "job_count_range": list(JOB_COUNT_RANGE),
        "base_minutes_range": list(BASE_MINUTES_RANGE),
        "slowdown_by_memory_gb": {str(memory): slowdown for memory, slowdown in SLOWDOWN.items()},
        "memory_need_weights": {str(memory): weight for memory, weight in MEMORY_NEED_WEIGHTS.items()},
        "machines_per_tier_range": list(MACHINES_PER_TIER_RANGE),
        "instances": instances,
    }
    with (OUTPUT_DIRECTORY / "manifest.json").open("w", encoding="utf-8") as manifest_file:
        json.dump(manifest, manifest_file, indent=2)
        manifest_file.write("\n")


if __name__ == "__main__":
    main()
