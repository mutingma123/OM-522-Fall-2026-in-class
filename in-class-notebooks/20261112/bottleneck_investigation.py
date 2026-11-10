import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import polars as pl

    import flowsim

    # Replace with the last four digits of your CWID.
    SEED = 1234
    return SEED, flowsim, mo, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Draw the line

    Build the line in the handout, then copy the script at the bottom of the page.
    """)
    return


@app.cell
def _(flowsim):
    flowsim.builder()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Your line as a function
    """)
    return


@app.cell
def _():
    def line(machines=(1, 1, 1), racks=(2, 2, 2)):
        # Paste the builder's script here, without its run line. Use machines[0], machines[1],
        # and machines[2] for each station's capacity, racks[0], racks[1], and racks[2] for its
        # buffer, and end with `return model`.
        raise NotImplementedError("Paste the builder's script into line().")

    return (line,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Check the build
    """)
    return


@app.cell
def _(line, pl):
    line().experiment(
        duration=480,
        replications=100,
        seed=42,
        keep_records=False,
    ).summary.select(
        pl.col("completed_at_close").mean().round(2).alias("check_value"),
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Seven versions of the line
    """)
    return


@app.cell
def _(SEED, flowsim, line):
    SCENARIOS = {
        "Today": line(),
        "Second Saw machine": line(machines=(2, 1, 1)),
        "Second Drill machine": line(machines=(1, 2, 1)),
        "Second Pack machine": line(machines=(1, 1, 2)),
        "Rack of 6 at Saw": line(racks=(6, 2, 2)),
        "Rack of 6 at Drill": line(racks=(2, 6, 2)),
        "Rack of 6 at Pack": line(racks=(2, 2, 6)),
    }
    comparison = flowsim.compare(
        scenarios=SCENARIOS,
        duration=480,
        replications=100,
        seed=SEED,
        keep_records=False,
    )
    return (comparison,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Where each station spends its time
    """)
    return


@app.cell
def _(comparison, pl):
    stations = (
        comparison.intervals(metric="utilization")
        .select("scenario", "station", pl.col("mean").alias("utilization"))
        .join(
            comparison.intervals(metric="processing_utilization").select(
                "scenario",
                "station",
                pl.col("mean").alias("processing_utilization"),
            ),
            on=["scenario", "station"],
            maintain_order="left",
        )
        .join(
            comparison.intervals(metric="blocking_fraction").select(
                "scenario",
                "station",
                pl.col("mean").alias("blocking_fraction"),
            ),
            on=["scenario", "station"],
            maintain_order="left",
        )
    )
    stations
    return (stations,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Jobs shipped per shift, compared with today
    """)
    return


@app.cell
def _(comparison):
    gains = comparison.differences(
        "completed_at_close",
        baseline="Today",
    ).select(
        "scenario",
        "mean",
        "lower",
        "upper",
    )
    gains
    return (gains,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## The line as a whole
    """)
    return


@app.cell
def _(comparison, pl):
    METRICS = [
        "completed_at_close",
        "throughput",
        "mean_flow_time",
        "mean_outside_wait",
        "mean_wip",
    ]
    results = pl.concat(
        [
            comparison.intervals(metric=_metric).select(
                "scenario",
                pl.lit(_metric).alias("metric"),
                "mean",
            )
            for _metric in METRICS
        ]
    ).pivot(
        on="metric",
        index="scenario",
        values="mean",
    )
    results
    return (results,)


@app.cell
def _(SEED, gains, pl, results, stations):
    wide_stations = stations.pivot(
        on="station",
        index="scenario",
        values=["utilization", "processing_utilization", "blocking_fraction"],
    )
    (
        results.join(
            gains.select(
                "scenario",
                pl.col("mean").alias("gain"),
                pl.col("lower").alias("gain_lower"),
                pl.col("upper").alias("gain_upper"),
            ),
            on="scenario",
            how="left",
            maintain_order="left",
        )
        .join(
            wide_stations,
            on="scenario",
            maintain_order="left",
        )
        .with_columns(pl.lit(SEED).alias("seed"))
        .write_csv(f"bottleneck-{SEED}.csv")
    )
    f"Saved bottleneck-{SEED}.csv"
    return


if __name__ == "__main__":
    app.run()
