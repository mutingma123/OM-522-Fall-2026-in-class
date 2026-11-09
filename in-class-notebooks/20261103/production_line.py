import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    import numpy as np
    import polars as pl

    # FlowSim is the folder `flowsim/` next to this notebook, so Python imports it directly.
    import flowsim

    SEED = 522
    return SEED, flowsim, mo, np, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Building a production line in FlowSim

    A shop releases jobs to a three-station line (Cut, then Weld, then Paint), with one machine
    at each station, through an eight-hour shift. Released jobs wait in front of Cut with no
    limit on space. Between machines, the shop has small racks, and when a rack is full, a
    finished job stays on the machine before it, which stops that machine from starting its next
    job until space opens (i.e., the machine is *blocked*).

    The question for today is how much rack space the line needs and what it buys. We answer it
    in five steps:

    1. Read ten days of data from the shop.
    2. Fit a distribution to each uncertain input.
    3. Check that each fit draws values like the shop's.
    4. Build the line in FlowSim, one block at a time, and run it.
    5. Compare rack sizes on the same simulated days.

    The folder holds three things, i.e., `flowsim/` (the simulation library), `data/` (the shop's
    files), and this notebook. Because `flowsim/` sits next to the notebook, `import flowsim`
    works with no installation, and every FlowSim function is called as `flowsim.<name>`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1, read the data

    The shop has two files covering ten working days. `releases.csv` has the clock time at which
    each job was released to the line, and `processing_times.csv` has how long each job took at
    each station, in minutes.
    """)
    return


@app.cell
def _(mo, pl):
    data_dir = mo.notebook_dir() / "data"

    release_data = pl.read_csv(
        data_dir / "releases.csv",
        try_parse_dates=True,
    )
    print(f'{release_data.shape = }')

    processing_data = pl.read_csv(data_dir / "processing_times.csv")
    print(f'{processing_data.shape = }')
    return processing_data, release_data


@app.cell
def _(release_data):
    release_data.sort('released').head()
    return


@app.cell
def _(processing_data):
    processing_data.head(6)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    FlowSim needs the time *between* releases, not the release times themselves. We sort the
    releases and take the difference between each release and the one before it, within each
    day (`.over(...)`), so the overnight gap between days is never counted.
    """)
    return


@app.cell
def _(pl, release_data):
    release_gaps = (
        release_data.sort("released")
        .with_columns(
            (pl.col("released").diff().dt.total_seconds() / 60)
            .over(pl.col("released").dt.date())
            .alias("gap"),
        )
        .drop_nulls("gap")
    )
    release_gaps.head()
    return (release_gaps,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We collect the four inputs in one dictionary and summarize each one. The coefficient of
    variation (CV) is the standard deviation divided by the mean, so a CV of 0.2 means a job
    typically lands within about 20 percent of the mean, and a CV of 1 means the times are as
    spread out as their mean.
    """)
    return


@app.cell
def _(pl, processing_data, release_gaps):
    samples = {
        "Release gap": release_gaps["gap"].to_numpy(),
        "Cut": processing_data.filter(pl.col("station") == "Cut")["minutes"].to_numpy(),
        "Weld": processing_data.filter(pl.col("station") == "Weld")["minutes"].to_numpy(),
        "Paint": processing_data.filter(pl.col("station") == "Paint")["minutes"].to_numpy(),
    }
    pl.DataFrame(
        [
            {
                "input": name,
                "n": values.size,
                "mean": values.mean(),
                "cv": values.std(ddof=1) / values.mean(),
                "min": values.min(),
                "max": values.max(),
            }
            for name, values in samples.items()
        ]
    )
    return (samples,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2, fit distributions

    `fit_all` fits five common families to one input (exponential, gamma, lognormal, and Weibull,
    which each start at zero since a time cannot be negative, and normal) and ranks them. The
    columns to read first are:

    - `aic`, the fit's score, where smaller is better. A family with more parameters must earn its
      extra flexibility, and the ranking is the same on every run;
    - `ks`, the largest vertical gap between the data's cumulative curve and the fitted one (the
      Kolmogorov-Smirnov statistic), which we met on October 22;
    - `mean` and `sd`, the fitted distribution's own mean and standard deviation, to compare with
      the data's;
    - `p_negative`, the fitted chance of drawing a time below zero.

    We start with Weld. The warning above the table says that the shop's times are recorded in
    rounded values, which is common in real data and worth knowing.
    """)
    return


@app.cell
def _(flowsim, samples):
    weld_fits = flowsim.fit_all(samples["Weld"])
    weld_fits.table
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Look at `p_negative`. A normal distribution has no lower limit, so a normal fitted to short times
    can draw a negative time, and FlowSim stops with an error when a time is negative. We can never
    gain time by processing a job on a machine.

    That is why we take `.best`, the top-ranked fit whose chance of a negative draw is at most one
    in a million. Rank alone does not show that a family fits well, since it compares only the
    candidates, so the plot of the data against the fits is the check on quality.

    The fits below cover all four inputs. `Cut` shows the rule at work, since its best fit is a
    normal whose `p_negative` is small enough to accept. The `Release gap` data shows what `.failed`
    is for, because it has two gaps of exactly zero (two jobs released in the same rounded minute).
    A family that starts at zero cannot score an exact zero, so gamma, lognormal, and Weibull drop
    out and the table says why.
    """)
    return


@app.cell
def _(flowsim, samples):
    fits = {name: flowsim.fit_all(values) for name, values in samples.items()}
    chosen = {name: table.best for name, table in fits.items()}
    fits["Release gap"].failed
    return chosen, fits


@app.cell
def _(mo, samples):
    input_picker = mo.ui.dropdown(
        options=list(samples),
        value="Weld",
        label="Input to plot",
    )
    input_picker
    return (input_picker,)


@app.cell
def _(fits, input_picker):
    fits[input_picker.value].plot()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The table lists the fit we take for each input. The exponential for the release gap is what
    jobs released at random moments through the day produce.
    """)
    return


@app.cell
def _(chosen, pl):
    pl.DataFrame(
        [
            {
                "input": name,
                "fit": str(fit.distribution),
                "mean": fit.mean,
                "sd": fit.sd,
                "aic": fit.aic,
                "ks": fit.ks,
                "p_negative": fit.p_negative,
            }
            for name, fit in chosen.items()
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3, a fit is something FlowSim can draw from

    A fit is itself a distribution. Each time we call it with a random-number generator, it returns
    one draw, and FlowSim calls it the same way every time a job starts at a station. The generator
    is created from a seed, so the same seed gives the same draws.
    """)
    return


@app.cell
def _(SEED, chosen, np):
    weld_time = chosen["Weld"]
    _rng = np.random.default_rng(SEED)

    [round(weld_time(_rng), 2) for _ in range(5)]
    return (weld_time,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    A check worth doing every time is to draw many values and compare them with the data. If the
    mean, the CV, and the 95th percentile are close, the fit behaves like the shop.
    """)
    return


@app.cell
def _(SEED, np, pl, samples, weld_time):
    _rng = np.random.default_rng(SEED)
    _draws = np.array([weld_time(_rng) for _ in range(10_000)])
    pl.DataFrame(
        [
            {
                "source": label,
                "n": values.size,
                "mean": values.mean(),
                "cv": values.std(ddof=1) / values.mean(),
                "p95": np.quantile(values, 0.95),
                "min": values.min(),
            }
            for label, values in [("Weld data", samples["Weld"]), ("10,000 draws", _draws)]
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 4, build the line one block at a time

    The settings cell holds the numbers the model uses. `buffer` is the rack size in front of a
    station (0 means no rack, so a finished job waits on the machine before it). FlowSim also
    requires `external_overflow` whenever a station has a limited buffer, which says what a job
    arriving from outside the line does when the rack is full. `"wait"` holds it, and no job
    arrives at Weld or Paint from outside, so the setting changes nothing here.

    Change the rack sizes in the settings cell, not inside a block. Marimo then re-runs the cell
    that creates the model and every block after it, in order. A block edited and re-run on its
    own would add a second station with a name the model already has, and FlowSim stops with an
    error.
    """)
    return


@app.cell
def _():
    TIME_UNIT = "minutes"
    SHIFT_MINUTES = 480
    WELD_RACK = 2
    PAINT_RACK = 2
    REPLICATIONS = 100
    return PAINT_RACK, REPLICATIONS, SHIFT_MINUTES, TIME_UNIT, WELD_RACK


@app.cell
def _(TIME_UNIT, flowsim):
    # Block 1. An empty model.
    model = flowsim.Model(time_unit=TIME_UNIT)
    return (model,)


@app.cell
def _(chosen, model):
    # Block 2. Jobs released to the line, one release gap at a time.
    jobs = model.source(
        name="Jobs",
        interarrival=chosen["Release gap"],
    )
    return (jobs,)


@app.cell
def _(chosen, model):
    # Block 3. Cut, one machine. Released jobs wait in front of it with no limit on space.
    cut = model.station(
        name="Cut",
        capacity=1,
        service_time=chosen["Cut"],
    )
    return (cut,)


@app.cell
def _(WELD_RACK, chosen, model):
    # Block 4. Weld, one machine, with a rack of WELD_RACK spaces in front of it.
    weld = model.station(
        name="Weld",
        capacity=1,
        service_time=chosen["Weld"],
        buffer=WELD_RACK,
        external_overflow="wait",
    )
    return (weld,)


@app.cell
def _(PAINT_RACK, chosen, model):
    # Block 5. Paint, one machine, with a rack of PAINT_RACK spaces in front of it.
    paint = model.station(
        name="Paint",
        capacity=1,
        service_time=chosen["Paint"],
        buffer=PAINT_RACK,
        external_overflow="wait",
    )
    return (paint,)


@app.cell
def _(cut, jobs, model, paint, weld):
    # Block 6. The route every job follows, from release to the exit.
    model.route([jobs, cut, weld, paint, model.exit])

    # The finished model gets its own name, so every cell below waits for this block.
    line_model = model
    line_model.diagram()
    return (line_model,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 5, run one day

    `run` simulates one shift. Releases stop at `duration` (480 minutes), and `drain=True` keeps
    the line running until every released job is finished, as the shop does with overtime. The
    first table counts the jobs finished during the shift (`completed_at_close`), the jobs still
    in the line at the end of the shift (`remaining_at_close`), the average time from release to
    leaving Paint (`mean_flow_time`), and the minutes of overtime. The second table separates each
    machine's time into processing and blocked.
    """)
    return


@app.cell
def _(SEED, SHIFT_MINUTES, line_model):
    one_day = line_model.run(
        duration=SHIFT_MINUTES,
        seed=SEED,
        drain=True,
    )
    one_day.summary.select(
        "arrivals",
        "completed_at_close",
        "remaining_at_close",
        "mean_flow_time",
        "overtime",
    )
    return (one_day,)


@app.cell
def _(one_day):
    one_day.stations.select(
        "station",
        "service_completions",
        "mean_wait",
        "max_queue",
        "processing_utilization",
        "blocking_fraction",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The queue plot shows the number of jobs waiting at each station through the day, and the
    resource plot shows when each machine was processing, idle, or blocked. Each plot has a menu
    that chooses a station, so you see one at a time.
    """)
    return


@app.cell
def _(one_day):
    one_day.plot_queue()
    return


@app.cell
def _(one_day):
    one_day.plot_resources()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### What else is in a run?

    Every FlowSim object describes itself. Leave a run as the last line of a cell and it lists its
    settings, its headline measures, its tables, and the calls that usually come next.
    `flowsim.metrics()` lists every measure with its units and meaning, and
    `flowsim.explain("blocking_fraction")` prints one of them. To explore a run in a browser, call
    `one_day.viewer("output/one-day.html").open()`, which saves a page you can reopen without
    internet access.
    """)
    return


@app.cell
def _(one_day):
    one_day
    return


@app.cell
def _(flowsim):
    flowsim.metrics()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 6, many days instead of one

    One day is one draw of the release gaps and processing times, and the next day will differ.
    `experiment` runs `REPLICATIONS` independent days and `intervals` reports the average over
    those days with a 95 percent confidence interval (`lower` to `upper`).
    """)
    return


@app.cell
def _(REPLICATIONS, SEED, SHIFT_MINUTES, line_model, pl):
    experiment = line_model.experiment(
        duration=SHIFT_MINUTES,
        replications=REPLICATIONS,
        seed=SEED,
        drain=True,
    )
    pl.concat(
        [
            experiment.intervals(metric="completed_at_close"),
            experiment.intervals(metric="mean_flow_time"),
            experiment.intervals(metric="overtime"),
            experiment.intervals(metric="blocking_fraction", station="Cut"),
            experiment.intervals(metric="processing_utilization", station="Weld"),
        ],
        how="diagonal",
    ).select("metric", "station", "mean", "lower", "upper")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 7, compare rack sizes

    Each rack plan needs its own model, so `build_line` repeats Blocks 1 to 6 with the plan's
    rack sizes. `flowsim.compare` then runs every plan on the *same* simulated days (the same releases
    and processing times), so a difference between two plans comes from the racks and not from
    luck. Each plan is a pair (Weld rack, Paint rack).
    """)
    return


@app.cell
def _(TIME_UNIT, chosen, flowsim):
    def build_line(weld_rack, paint_rack):
        line = flowsim.Model(time_unit=TIME_UNIT)
        line_jobs = line.source(
            name="Jobs",
            interarrival=chosen["Release gap"],
        )
        line_cut = line.station(
            name="Cut",
            capacity=1,
            service_time=chosen["Cut"],
        )
        line_weld = line.station(
            name="Weld",
            capacity=1,
            service_time=chosen["Weld"],
            buffer=weld_rack,
            external_overflow="wait",
        )
        line_paint = line.station(
            name="Paint",
            capacity=1,
            service_time=chosen["Paint"],
            buffer=paint_rack,
            external_overflow="wait",
        )
        line.route([line_jobs, line_cut, line_weld, line_paint, line.exit])
        return line

    return (build_line,)


@app.cell
def _(REPLICATIONS, SEED, SHIFT_MINUTES, build_line, flowsim):
    RACK_PLANS = {
        "No racks": (0, 0),
        "1 and 1": (1, 1),
        "2 and 2": (2, 2),
        "4 and 4": (4, 4),
        "8 and 8": (8, 8),
    }

    comparison = flowsim.compare(
        scenarios={
            name: build_line(weld_rack=weld_rack, paint_rack=paint_rack)
            for name, (weld_rack, paint_rack) in RACK_PLANS.items()
        },
        duration=SHIFT_MINUTES,
        replications=REPLICATIONS,
        seed=SEED,
        drain=True,
    )
    return (comparison,)


@app.cell
def _(comparison, pl):
    _measures = {
        "jobs finished in shift": comparison.intervals(metric="completed_at_close"),
        "flow time": comparison.intervals(metric="mean_flow_time"),
        "overtime": comparison.intervals(metric="overtime"),
        "Cut blocked": comparison.intervals(metric="blocking_fraction", station="Cut"),
        "Weld blocked": comparison.intervals(metric="blocking_fraction", station="Weld"),
    }
    _table = None
    for _label, _intervals in _measures.items():
        _column = _intervals.select("scenario", pl.col("mean").alias(_label))
        _table = _column if _table is None else _table.join(_column, on="scenario", maintain_order="left")
    _table
    return


@app.cell
def _(comparison):
    comparison.plot(metric="completed_at_close")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Where do the extra jobs come from? The table splits Weld's shift, averaged over the 100
    shifts, into the share spent working on jobs (`processing_utilization`) and the share spent
    blocked, holding a finished job with nowhere to put it (`blocking_fraction`). FlowSim's
    `utilization` is the two added together, i.e., the share of the shift the machine is
    occupied. The utilization in the Quiz 3 investigation is `processing_utilization`.
    """)
    return


@app.cell
def _(comparison, pl):
    (
        comparison.stations
        .filter(pl.col("station") == "Weld")
        .group_by("scenario", maintain_order=True)
        .agg(
            pl.col("processing_utilization").mean(),
            pl.col("blocking_fraction").mean(),
            pl.col("utilization").mean(),
        )
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The next table is each plan minus the current one (racks of 2 and 2), paired day by day.
    An interval that excludes zero is a change the plan reliably makes.
    """)
    return


@app.cell
def _(comparison, pl):
    pl.concat(
        [
            comparison.differences(metric="completed_at_close", baseline="2 and 2"),
            comparison.differences(metric="mean_flow_time", baseline="2 and 2"),
        ]
    ).select("metric", "scenario", "mean", "lower", "upper")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Reading the results

    With no racks, a machine that finishes a job while the next machine is busy has nowhere to
    put it, so it sits blocked, and the line loses capacity it cannot get back later in the day.
    The first rack space recovers most of that loss, and each space after it recovers less.
    Racks never make a machine faster, so beyond a few spaces the line finishes what the
    machines can do, and more rack space buys nothing.

    ## Your turn

    Predict each result before you run it.

    1. The line has four rack spaces in total. Add `"4 and 0": (4, 0)` and `"0 and 4": (0, 4)`
       to `RACK_PLANS`. Which machine is blocked in each plan, and which plan finishes more
       jobs than `"2 and 2"`?
    2. In `build_line`, replace Weld's `service_time=chosen["Weld"]` with a constant, i.e.,
       `service_time=4.56` (the mean of the fitted Weld times). Does the line still need racks?
    3. Set `WELD_RACK = 0` in the settings cell and look at the resource plot for one day. When
       is Cut blocked?
    """)
    return


if __name__ == "__main__":
    app.run()
