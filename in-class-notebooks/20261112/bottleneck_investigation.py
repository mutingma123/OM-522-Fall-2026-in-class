import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import polars as pl

    import flowsim

    # Replace 1234 with the last four digits of your CWID (handout, "Set up the notebook", step 3).
    SEED = 1234
    return SEED, flowsim, mo, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Quiz 3: bottlenecks, machines, and racks

    Write your predictions (P1 to P3 in the handout) before you run anything. Then work down this
    notebook in order. Each section below names the handout questions it is for.

    | Section | Handout questions |
    |---|---|
    | Draw the line | A1 |
    | Your line as a function | A2 |
    | Check the build | A3 (must show 79.49) |
    | Seven versions of the line | Runs once A3 passes, in about 10 seconds |
    | Stations table | B2, C2, C3, D3 |
    | Gains table | C1, D1 |
    | Line table | B3, D2, E1 |
    | Little's Law | E1, E2 (add your own cells there) |

    B1 uses Table 1 of the handout only, so it has no section here.

    ## Draw the line (A1)

    Build the line in Table 1 of the handout, then copy the script at the bottom of the builder.
    """)
    return


@app.cell
def _(flowsim):
    flowsim.builder()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Your line as a function (A2)
    """)
    return


@app.cell
def _():
    def line(machines=(1, 1, 1), racks=(2, 2, 2)):
        # A2, in five steps:
        # 1. Paste the builder's whole script below these comments. Then select the pasted lines
        #    and press Tab, so every line sits one level inside line(), like this comment.
        # 2. Delete the last two parts of the script: the `results = model.run(...)` call and the
        #    `print(results)` line.
        # 3. In each station, change `capacity=1` (the number of machines) to machines[0] for the
        #    Saw, machines[1] for the Drill, and machines[2] for the Pack. Change `buffer=2` to
        #    racks[0], racks[1], and racks[2] the same way.
        # 4. Add `return model` as the last line, at the same indent as the lines above it.
        #    Without it, line() hands back nothing and the check below fails.
        # 5. Delete the raise line.
        #
        # The function should end like this:
        #     model.route([orders, saw, drill, pack, model.exit])
        #     return model
        raise NotImplementedError("Paste the builder's script into line().")

    return (line,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Check the build (A3)

    This cell must show 79.49. If it shows an error or another number, see the Troubleshooting box
    at the end of the handout.
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

    Run this cell once the check shows 79.49. It runs today's line and six changes to it with your
    seed, and takes about 10 seconds. It shows no output, and the three tables below read its results.
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
    ## Stations table

    Where each station spends its time. Used in B2, C2, C3, and D3. Each row is one station in one version of the line. For a station
    with two machines, each column is the average over its two machines.
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
    ## Gains table

    Jobs shipped per shift by each change, compared with today. Used in C1 and D1. The `mean` column is the gain, i.e., the jobs per shift each change ships
    minus what today's line ships. The `lower` and `upper` columns are its 95% interval.
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
    ## Line table

    The line as a whole. Used in B3, D2, and E1. Each row is one version of the line, averaged over
    100 shifts. The table is stored as `results`, which E1 uses.
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


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Little's Law (E1 and E2)

    Use the empty cell below for E1. For E2, add another cell (hover over a cell and click the +
    button that appears beside it). Copy the code from the handout, and give each new table its own
    name, since marimo does not allow two cells to define the same name.
    """)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
