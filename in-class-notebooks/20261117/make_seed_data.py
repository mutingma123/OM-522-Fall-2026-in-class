"""Run the Quiz 4 cases for 30 seeds and save them to data/variability-seeds.csv.

The model and measurement are copied from ../20261110/variability_investigation.py, so each seed's
rows match what a student with that seed would get from Quiz 4. Run from this folder:

    pixi run python make_seed_data.py
"""

from pathlib import Path

import polars as pl

from flowsim import Model

MEAN_PROCESSING = 4
UTILIZATIONS = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
CASES = [(1, 1), (1, 0), (1, 4), (0, 1), (0, 0)]
SEEDS = range(1234, 1264)


def sampler(mean, scv):
    if scv == 0:
        return mean
    return lambda rng: rng.gamma(shape=1 / scv, scale=mean * scv)


def one_station(utilization, arrival_scv, processing_scv):
    model = Model(time_unit="minutes")
    jobs = model.source(
        name="Jobs",
        interarrival=sampler(MEAN_PROCESSING / utilization, arrival_scv),
    )
    machine = model.station(
        name="Machine",
        capacity=1,
        service_time=sampler(MEAN_PROCESSING, processing_scv),
    )
    model.route([jobs, machine, model.exit])
    return model


def measure(utilization, arrival_scv, processing_scv, seed):
    experiment = one_station(utilization, arrival_scv, processing_scv).experiment(
        duration=4800,
        replications=10,
        seed=seed,
        warmup=480,
    )
    station = experiment.stations.select(
        pl.col("utilization").mean().alias("observed_utilization"),
        pl.col("mean_wait").mean(),
    )
    system = experiment.summary.select(
        pl.col("mean_wip").mean(),
        pl.col("throughput").mean(),
        pl.col("mean_flow_time").mean(),
    )
    return {
        "utilization": utilization,
        "arrival_scv": arrival_scv,
        "processing_scv": processing_scv,
        **station.row(0, named=True),
        **system.row(0, named=True),
    }


results = pl.DataFrame(
    [
        {**measure(utilization, arrival_scv, processing_scv, seed), "seed": seed}
        for seed in SEEDS
        for arrival_scv, processing_scv in CASES
        for utilization in UTILIZATIONS
    ]
).with_columns(
    pl.format("ca2={}, ce2={}", "arrival_scv", "processing_scv").alias("case"),
)
Path("data").mkdir(exist_ok=True)
results.write_csv("data/variability-seeds.csv")
print(results.shape)
