import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    import numpy as np
    import plotly.graph_objects as go
    import polars as pl
    from plotly.subplots import make_subplots

    import flowsim

    SEED = 522
    return SEED, flowsim, go, make_subplots, mo, np, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # The stress test of fixed plans

    Your final submission tests how each method's plan holds up when the data are not exact. This
    notebook runs the whole test on a small example, so you can see every step before you build it
    for your own option. The steps are the same for every team:

    1. State how one input varies.
    2. Generate 30 scenarios from a recorded seed and save them to a file before any plan runs.
    3. Run each fixed plan, unchanged, through every saved scenario.
    4. Report the mean, the 90th percentile, the number of broken limits, and a plot by scenario.

    FlowSim simulates how a line behaves, with jobs served in the order they arrive. Here the plan
    sets the order, so we run the plan with the small function below (your brief's execution rule
    plays this part in your project). FlowSim supplies the distribution we draw from.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Two fixed plans for one machine

    Eight jobs share one machine. A job more than 20 minutes late misses its truck, which is the hard
    limit. EDD sorts by due date, and the second plan improves it with pairwise interchange.
    """)
    return


@app.cell
def _(pl):
    jobs = pl.DataFrame(
        {
            "job": ["J1", "J2", "J3", "J4", "J5", "J6", "J7", "J8"],
            "processing_time": [5, 7, 11, 13, 13, 4, 9, 4],
            "due_date": [26, 27, 37, 45, 47, 49, 50, 55],
        }
    )

    # A job more than this many minutes late misses its truck.
    LATE_LIMIT = 20

    plans = {
        "EDD": ["J1", "J2", "J3", "J4", "J5", "J6", "J7", "J8"],
        "Interchange": ["J1", "J2", "J3", "J4", "J7", "J6", "J8", "J5"],
    }
    jobs
    return LATE_LIMIT, jobs, plans


@app.cell
def _(LATE_LIMIT):
    def execute(plan, processing_times, due_dates):
        clock = 0
        total_tardiness = 0
        max_lateness = None
        for job in plan:
            clock += processing_times[job]
            lateness = clock - due_dates[job]
            total_tardiness += max(lateness, 0)
            if max_lateness is None or lateness > max_lateness:
                max_lateness = lateness
        return {
            "total_tardiness": total_tardiness,
            "max_lateness": max_lateness,
            "violation": max_lateness > LATE_LIMIT,
        }

    return (execute,)


@app.cell
def _(execute, jobs, pl, plans):
    planned_times = dict(zip(jobs["job"], jobs["processing_time"]))
    due_dates = dict(zip(jobs["job"], jobs["due_date"]))

    deterministic = pl.DataFrame(
        [{"plan": name, **execute(plan, planned_times, due_dates)} for name, plan in plans.items()]
    )
    deterministic
    return deterministic, due_dates


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Saving the scenarios

    We state how the input varies: each processing time is multiplied by its own random factor with
    mean 1 and a coefficient of variation of 0.2. In FlowSim, that is `lognormal(mean=1, sd=0.2)`. If
    you have data on actual times, you can fit a distribution as we did on November 3 and draw from
    the fit in the same way.

    The scenarios go to a file before any plan runs, so both plans face identical numbers and a
    grader can open the file.
    """)
    return


@app.cell
def _(SEED, flowsim, jobs, mo, np, pl):
    SCENARIOS = 30
    scenario_file = mo.notebook_dir() / "scenarios.csv"

    factor = flowsim.lognormal(mean=1, sd=0.2)
    _rng = np.random.default_rng(SEED)

    scenarios = pl.DataFrame(
        [
            {
                "scenario": scenario,
                "job": job,
                "realized_time": factor(_rng) * planned,
            }
            for scenario in range(1, SCENARIOS + 1)
            for job, planned in zip(jobs["job"], jobs["processing_time"])
        ]
    )
    scenarios.write_csv(scenario_file)
    factor
    return SCENARIOS, scenario_file, scenarios


@app.cell
def _(SCENARIOS, jobs, pl, scenario_file, scenarios):
    # Read the file back, so every result below comes from what was saved.
    saved = pl.read_csv(scenario_file)

    assert saved.height == SCENARIOS * jobs.height
    assert saved.select("scenario", "job").equals(scenarios.select("scenario", "job"))
    saved.head(8)
    return (saved,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Running both plans unchanged through every scenario

    The plans never change. Only the realized times change from one scenario to the next.
    """)
    return


@app.cell
def _(due_dates, execute, pl, plans, saved):
    _rows = []
    for (_scenario,), _group in saved.group_by("scenario", maintain_order=True):
        _realized = dict(zip(_group["job"], _group["realized_time"]))
        for _name, _plan in plans.items():
            _rows.append({"scenario": _scenario, "plan": _name, **execute(_plan, _realized, due_dates)})
    results = pl.DataFrame(_rows)
    results.head(6)
    return (results,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Reading the results

    Report the average, a bad day (the 90th percentile), and how often the hard limit breaks. Then
    compare the plans scenario by scenario, since both faced the same numbers in each one.
    """)
    return


@app.cell
def _(pl, results):
    summary = results.group_by("plan", maintain_order=True).agg(
        pl.col("total_tardiness").mean().alias("mean_tardiness"),
        pl.col("total_tardiness").quantile(0.9, interpolation="linear").alias("p90_tardiness"),
        pl.col("max_lateness").mean().alias("mean_max_lateness"),
        pl.col("max_lateness").quantile(0.9, interpolation="linear").alias("p90_max_lateness"),
        pl.col("violation").sum().alias("violations"),
    )
    summary
    return (summary,)


@app.cell
def _(pl, results):
    paired = (
        results.pivot(on="plan", index="scenario", values="total_tardiness")
        .with_columns((pl.col("Interchange") - pl.col("EDD")).alias("difference"))
        .select(
            pl.col("difference").mean().alias("mean_difference"),
            (pl.col("difference") < 0).sum().alias("interchange_better"),
            (pl.col("difference") > 0).sum().alias("edd_better"),
        )
    )
    paired
    return (paired,)


@app.cell
def _(LATE_LIMIT, deterministic, go, make_subplots, plans, results):
    _figure = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=[
            "Total tardiness (dotted: planned times)",
            "Maximum lateness (dotted: planned times)",
        ],
    )
    for _name, _color in zip(plans, ["#2F6690", "#DE8F05"]):
        _runs = results.filter(plan=_name)
        _planned = deterministic.filter(plan=_name).row(0, named=True)
        for _col, _metric in enumerate(["total_tardiness", "max_lateness"], start=1):
            _figure.add_scatter(
                x=_runs["scenario"].to_list(),
                y=_runs[_metric].to_list(),
                mode="lines+markers",
                name=_name,
                legendgroup=_name,
                showlegend=_col == 1,
                line={"color": _color},
                row=1,
                col=_col,
            )
            _figure.add_hline(
                y=_planned[_metric],
                line={"color": _color, "dash": "dot"},
                row=1,
                col=_col,
            )
    _figure.add_hline(
        y=LATE_LIMIT,
        line={"color": "#A63D40"},
        annotation_text="late limit",
        row=1,
        col=2,
    )
    _figure.update_xaxes(title_text="Scenario")
    _figure.update_yaxes(title_text="Minutes")
    _figure.update_layout(height=420)
    _figure
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## For your project

    Your team writes the same steps for its option:

    - Choose one uncertain input from your brief and state how it varies.
    - Save 30 scenarios from a documented seed before running anything.
    - Run each method's plan on the medium development instance, unchanged, using your brief's
      execution rule.
    - For each method, report the mean and 90th percentile of the primary and secondary measures,
      the number of scenarios that break a hard constraint, and a per-scenario plot.

    The project guide's section on the stress test is the full requirement, and it is worth 5 points
    of the final submission.

    ## Your turn

    Predict each result before you run it.

    1. Change the factor to `lognormal(mean=1, sd=0.4)`. Which plan's violation count grows faster?
    2. Replace it with `lognormal(mean=1.1, sd=0.2)`, i.e., everything runs 10 percent long. Does the
       same plan still win on total tardiness?
    """)
    return


if __name__ == "__main__":
    app.run()
