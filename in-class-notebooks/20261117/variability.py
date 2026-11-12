import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    import plotly.express as px
    import polars as pl

    from flowsim import Model, compare, exponential, gamma

    return Model, compare, exponential, gamma, mo, pl, px


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Thirty runs of the variability experiment

    One machine, 4-minute jobs on average, five cases at six utilizations. Each seed is a different
    random history, run exactly as in Quiz 4, which you do with your own seed after this class
    (`make_seed_data.py` wrote the file).
    """)
    return


@app.cell
def _(pl):
    seeds = pl.read_csv("data/variability-seeds.csv")
    seeds
    return (seeds,)


@app.cell
def _(px, seeds):
    px.line(
        seeds,
        x="utilization",
        y="mean_wait",
        color="case",
        line_group="seed",
        facet_col="case",
        facet_col_wrap=3,
        markers=True,
        labels={"utilization": "Utilization", "mean_wait": "Mean wait (minutes)"},
    ).update_traces(opacity=0.4)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## One seed, as a table

    Seed 1234, the notebook's default. Mean wait in minutes.
    """)
    return


@app.cell
def _(pl, seeds):
    (
        seeds.filter(pl.col("seed") == 1234)
        .pivot(
            on="case",
            index="utilization",
            values="mean_wait",
        )
        .with_columns(pl.exclude("utilization").round(1))
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Where do the seeds disagree most?

    Random arrivals and random processing, ca2 = ce2 = 1.
    """)
    return


@app.cell
def _(pl, seeds):
    (
        seeds.filter(
            pl.col("arrival_scv") == 1,
            pl.col("processing_scv") == 1,
        )
        .group_by("utilization")
        .agg(
            pl.col("mean_wait").min().round(1).alias("lowest"),
            pl.col("mean_wait").median().round(1).alias("median"),
            pl.col("mean_wait").max().round(1).alias("highest"),
        )
        .sort("utilization")
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # How good is the formula?

    Wait ≈ (ca2 + ce2)/2 × u/(1 − u) × 4 minutes, against longer simulated runs.
    """)
    return


@app.cell
def _(gamma):
    def spread(mean, scv):
        # A gamma with shape 1/scv has squared coefficient of variation scv. Zero means every
        # value equals the mean.
        if scv == 0:
            return mean
        return gamma(
            shape=1 / scv,
            scale=mean * scv,
        )

    return (spread,)


@app.cell
def _(Model, pl, spread):
    FORMULA_CASES = [
        (0.5, 1, 1),
        (0.8, 1, 1),
        (0.9, 1, 1),
        (0.9, 1, 4),
        (0.5, 0.25, 0.25),
        (0.9, 0.25, 0.25),
    ]

    def simulated_wait(utilization, arrival_scv, processing_scv):
        model = Model()
        jobs = model.source(
            name="Jobs",
            interarrival=spread(4 / utilization, arrival_scv),
        )
        machine = model.station(
            name="Machine",
            capacity=1,
            service_time=spread(4, processing_scv),
        )
        model.route([jobs, machine, model.exit])
        interval = model.experiment(
            duration=20_000,
            replications=20,
            seed=522,
            warmup=2_000,
            keep_records=False,
        ).intervals("mean_wait", station="Machine")
        return interval["mean"][0]

    def formula_wait(utilization, arrival_scv, processing_scv):
        return (arrival_scv + processing_scv) / 2 * utilization / (1 - utilization) * 4

    pl.DataFrame(
        [
            {
                "u": utilization,
                "ca2": arrival_scv,
                "ce2": processing_scv,
                "formula": round(formula_wait(utilization, arrival_scv, processing_scv), 1),
                "simulated": round(simulated_wait(utilization, arrival_scv, processing_scv), 1),
            }
            for utilization, arrival_scv, processing_scv in FORMULA_CASES
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Propagation

    Jobs arrive about every 5 minutes. Station 1 takes 4.5 minutes on average, and only its
    variability changes. Station 2 takes 4 minutes and never changes.
    """)
    return


@app.cell
def _(Model, exponential, spread):
    def two_stations(first_scv):
        model = Model()
        jobs = model.source(
            name="Jobs",
            interarrival=exponential(mean=5),
        )
        first = model.station(
            name="Station 1",
            capacity=1,
            service_time=spread(4.5, first_scv),
        )
        second = model.station(
            name="Station 2",
            capacity=1,
            service_time=spread(4, 0.25),
        )
        model.route([jobs, first, second, model.exit])
        return model

    return (two_stations,)


@app.cell
def _(compare, two_stations):
    propagation = compare(
        scenarios={
            "Station 1 regular (ce2 = 0)": two_stations(0),
            "Station 1 random (ce2 = 1)": two_stations(1),
            "Station 1 very irregular (ce2 = 4)": two_stations(4),
        },
        duration=20_000,
        replications=20,
        seed=522,
        warmup=2_000,
        keep_records=False,
    )
    propagation.intervals("mean_wait", station="Station 2").select("scenario", "mean", "lower", "upper")
    return


if __name__ == "__main__":
    app.run()
