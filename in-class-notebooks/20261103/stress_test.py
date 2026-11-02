import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    import pathlib
    import warnings

    import matplotlib.pyplot as plt
    import numpy as np
    import polars as pl
    import scipy.stats as st
    import seaborn as sns

    sns.set_style("whitegrid")

    SEED = 522
    return SEED, mo, np, pathlib, pl, plt, sns, st, warnings


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Fitting a distribution with one function call
    """)
    return


@app.cell
def _():
    # Eight common families instead of SciPy's 100-plus. The search takes a fraction of a
    # second, and the winner is a distribution we can explain. FlowSim has the same list
    # as flowsim.FAMILIES and the same search as flowsim.best_fit.
    families = [
        "norm",
        "lognorm",
        "uniform",
        "triang",
        "expon",
        "gamma",
        "weibull_min",
        "beta",
    ]
    return (families,)


@app.cell
def _(pl, st, warnings):
    def best_fit(data, families):
        rows = []
        for name in families:
            family = getattr(st, name)
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    params = family.fit(data)
                    ks = st.kstest(data, family(*params).cdf).statistic
            except Exception:
                continue
            rows.append({"family": name, "ks": ks, "params": list(params)})
        return (
            pl.DataFrame(rows)
            .filter(pl.col("ks").is_not_nan())
            .sort("ks")
            .with_row_index("rank", offset=1)
        )

    return (best_fit,)


@app.cell
def _(pathlib, pl):
    data_filepaths = sorted(pathlib.Path("data-samples").glob("*.csv"))

    # Change the index to fit another of the eight files.
    data_filepath = data_filepaths[0]
    data_sample = pl.read_csv(data_filepath)["x"].to_numpy()
    data_filepath.name, len(data_sample)
    return data_filepath, data_sample


@app.cell
def _(best_fit, data_sample, families):
    fits = best_fit(data_sample, families)
    fits
    return (fits,)


@app.cell
def _(data_filepath, data_sample, fits, np, plt, sns, st):
    _best = fits.row(0, named=True)
    fitted = getattr(st, _best["family"])(*_best["params"])

    _x = np.linspace(data_sample.min(), data_sample.max(), 400)
    _fig, _axes = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(11, 3.5),
    )
    sns.histplot(
        data_sample,
        bins=20,
        stat="density",
        edgecolor="k",
        alpha=0.6,
        ax=_axes[0],
    )
    _axes[0].plot(_x, fitted.pdf(_x), color="orange", linewidth=2)
    _axes[0].set_title("Density")
    sns.ecdfplot(data_sample, ax=_axes[1], label="data")
    _axes[1].plot(_x, fitted.cdf(_x), color="orange", linewidth=2, label=_best["family"])
    _axes[1].set_title("Cumulative")
    _axes[1].legend()
    _fig.suptitle(f"{data_filepath.name}: best fit {_best['family']}")
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Two fixed plans for one machine
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
    mo.md("""
    # Saving the scenarios
    """)
    return


@app.cell
def _(SEED, jobs, np, pl, st):
    SCENARIOS = 30
    CV = 0.2

    # SciPy's lognormal takes s, the standard deviation of log(X), and scale, exp of the mean
    # of log(X). These two lines choose them so that X has mean 1 and coefficient of variation CV.
    _sigma = np.sqrt(np.log(1 + CV**2))
    factor = st.lognorm(s=_sigma, scale=np.exp(-(_sigma**2) / 2))

    _factors = factor.rvs(size=(SCENARIOS, jobs.height), random_state=SEED)
    scenarios = (
        pl.DataFrame(_factors, schema=jobs["job"].to_list(), orient="row")
        .with_row_index("scenario", offset=1)
        .unpivot(index="scenario", variable_name="job", value_name="factor")
        .join(jobs.select("job", "processing_time"), on="job")
        .select(
            "scenario",
            "job",
            (pl.col("factor") * pl.col("processing_time")).alias("realized_time"),
        )
        .sort("scenario", "job")
    )
    scenarios.write_csv("scenarios.csv")
    factor.mean(), factor.std() / factor.mean()
    return SCENARIOS, scenarios


@app.cell
def _(SCENARIOS, jobs, pl, scenarios):
    saved = pl.read_csv("scenarios.csv")

    assert saved.height == SCENARIOS * jobs.height
    assert saved.select("scenario", "job").equals(scenarios.select("scenario", "job"))
    saved.head(8)
    return (saved,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Running both plans unchanged through every scenario
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
    return


@app.cell
def _(pl, results):
    paired = (
        results.pivot(on="plan", index="scenario", values="total_tardiness")
        .with_columns((pl.col("Interchange") - pl.col("EDD")).alias("difference"))
    )
    paired.select(
        pl.col("difference").mean().alias("mean_difference"),
        (pl.col("difference") < 0).sum().alias("interchange_better"),
        (pl.col("difference") > 0).sum().alias("edd_better"),
    )
    return


@app.cell
def _(LATE_LIMIT, deterministic, plans, plt, results):
    _fig, _axes = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(12, 3.8),
    )
    for _name, _color in zip(plans, ["tab:blue", "tab:orange"]):
        _runs = results.filter(plan=_name)
        _planned = deterministic.filter(plan=_name).row(0, named=True)
        for _ax, _metric in zip(_axes, ["total_tardiness", "max_lateness"]):
            _ax.plot(_runs["scenario"], _runs[_metric], "o-", color=_color, label=_name)
            _ax.axhline(_planned[_metric], color=_color, linestyle=":")
    _axes[1].axhline(LATE_LIMIT, color="red", label="late limit")
    _axes[0].set_title("Total tardiness (dotted: planned times)")
    _axes[1].set_title("Maximum lateness (dotted: planned times)")
    for _ax in _axes:
        _ax.set_xlabel("Scenario")
        _ax.set_ylabel("Minutes")
    _axes[1].legend()
    _fig.tight_layout()
    _fig
    return


if __name__ == "__main__":
    app.run()
