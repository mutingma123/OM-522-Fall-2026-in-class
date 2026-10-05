"""Generate the October 6 identical-parallel-machine instances.

Each instance is one night's queue of model-training runs for a set of
identical GPU machines. Every run is queued at the start of the night, so the
only data a job needs is its processing time in minutes. The number of machines
is a notebook setting rather than part of the data.

A queue has 16 to 22 jobs of 10 to 60 minutes each. With five machines, that is
three to four jobs per machine, which is where a one-pass construction such as
LPT most often leaves room for improvement.

Run with ``pixi run data``. The script refuses to overwrite existing data.
"""

import json
import random
from pathlib import Path

import polars as pl


JOB_SCHEMA = {
    "job": pl.String,
    "processing_time": pl.Int64,
}
SEED = 1006
INSTANCE_COUNT = 10
JOB_COUNT_RANGE = (16, 22)
PROCESSING_TIME_RANGE = (10, 60)
OUTPUT_DIRECTORY = Path(__file__).resolve().parent / "data"


def generate_instance(rng: random.Random) -> pl.DataFrame:
    """Sample one batch of jobs with integer processing times in minutes."""
    number_of_jobs = rng.randint(*JOB_COUNT_RANGE)
    rows = [
        {
            "job": f"J{index + 1:02d}",
            "processing_time": rng.randint(*PROCESSING_TIME_RANGE),
        }
        for index in range(number_of_jobs)
    ]
    return pl.DataFrame(rows, schema=JOB_SCHEMA)


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
        jobs = generate_instance(rng)
        jobs.write_parquet(instance_directory / "jobs.parquet", compression="zstd")
        instances.append(
            {
                "instance_id": instance_id,
                "job_count": jobs.height,
                "total_processing_time": int(jobs.get_column("processing_time").sum()),
                "jobs_file": f"{instance_id}/jobs.parquet",
            }
        )
        print(f"{instance_id}: {jobs.height} jobs")

    manifest = {
        "generator": "generate_parallel_data.py",
        "rng": "random.Random, one seed for all instances in order",
        "seed": SEED,
        "job_count_range": list(JOB_COUNT_RANGE),
        "processing_time_range_minutes": list(PROCESSING_TIME_RANGE),
        "instances": instances,
    }
    with (OUTPUT_DIRECTORY / "manifest.json").open("w", encoding="utf-8") as manifest_file:
        json.dump(manifest, manifest_file, indent=2)
        manifest_file.write("\n")


if __name__ == "__main__":
    main()
