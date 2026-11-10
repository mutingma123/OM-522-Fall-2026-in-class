import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import polars as pl

    from flowsim import Model, exponential

    return Model, exponential, mo, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # A line released faster than it can work

    Stations take exactly 4, 6, and 5 minutes, and a new job is released every minute.
    """)
    return


@app.cell
def _(Model):
    def saturated_line(rack):
        model = Model()
        orders = model.source(
            name="Orders",
            interarrival=1,
            first_arrival=0,
        )
        first = model.station(
            name="S1",
            capacity=1,
            service_time=4,
            buffer=0,
            external_overflow="wait",
        )
        second = model.station(
            name="S2",
            capacity=1,
            service_time=6,
            buffer=rack,
            external_overflow="wait",
        )
        third = model.station(
            name="S3",
            capacity=1,
            service_time=5,
            buffer=rack,
            external_overflow="wait",
        )
        model.route([orders, first, second, third, model.exit])
        return model

    return (saturated_line,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Which station sets the pace?
    """)
    return


@app.cell
def _(saturated_line):
    no_racks = saturated_line(0).run(
        duration=4800,
        seed=1,
        warmup=480,
    )
    no_racks.stations.select(
        "station",
        "utilization",
        "processing_utilization",
        "blocking_fraction",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Add racks of 1, 2, and 4
    """)
    return


@app.cell
def _(pl, saturated_line):
    racks = pl.concat(
        [
            saturated_line(rack)
            .run(
                duration=4800,
                seed=1,
                warmup=480,
            )
            .summary.select(
                pl.lit(rack).alias("racks"),
                pl.col("mean_wip").alias("jobs_in_line"),
                (pl.col("throughput") * 60).alias("jobs_per_hour"),
                (pl.col("mean_flow_time") - pl.col("mean_outside_wait")).alias("minutes_in_line"),
                pl.col("mean_outside_wait").alias("minutes_outside"),
            )
            for rack in [0, 1, 2, 4]
        ]
    )
    racks
    return (racks,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Little's Law: jobs ÷ jobs per hour
    """)
    return


@app.cell
def _(pl, racks):
    racks.select(
        "racks",
        "minutes_in_line",
        (pl.col("jobs_in_line") / pl.col("jobs_per_hour") * 60).alias("jobs_over_rate_in_minutes"),
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Little's Law with random times

    One machine, 4-minute jobs, 80% busy, over a long run.
    """)
    return


@app.cell
def _(Model, exponential, pl):
    long_run = Model()
    jobs = long_run.source(
        name="Jobs",
        interarrival=exponential(mean=5),
    )
    machine = long_run.station(
        name="Machine",
        capacity=1,
        service_time=exponential(mean=4),
    )
    long_run.route([jobs, machine, long_run.exit])
    long_run.run(
        duration=200_000,
        seed=7,
        warmup=20_000,
    ).summary.select(
        "mean_wip",
        "throughput",
        "mean_flow_time",
        (pl.col("throughput") * pl.col("mean_flow_time")).alias("throughput_x_flow_time"),
    )
    return


if __name__ == "__main__":
    app.run()
