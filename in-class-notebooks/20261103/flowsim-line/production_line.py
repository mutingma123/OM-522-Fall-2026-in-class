import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    import numpy as np
    import plotly.graph_objects as go
    import polars as pl
    import scipy.stats as st

    # FlowSim is the folder `flowsim/` next to this notebook, so Python imports it directly.
    import flowsim

    SEED = 522
    return SEED, flowsim, go, mo, np, pl, st


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
    3. Turn each fit into a sampler that FlowSim can draw from.
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
def _(pl):
    release_data = pl.read_csv(
        "data/releases.csv", 
        try_parse_dates=True,
    )
    print(f'{release_data.shape = }')

    processing_data = pl.read_csv("data/processing_times.csv")
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

    `best_fit` fits eight common families (normal, lognormal, uniform, triangular, exponential,
    gamma, Weibull, and beta) to one input and ranks them. The columns are:

    - `ks`, the largest vertical gap between the data's cumulative curve and the fitted one
      (the Kolmogorov-Smirnov statistic), where smaller is better and the ranking is the same on
      every run;
    - `params`, the fitted parameters in SciPy's order (any shape parameters, then the location,
      then the scale);
    - `lower` and `upper`, the smallest and largest values the fitted distribution can draw;
    - `loc_fixed`, which marks a fit that `best_fit` redid so that it starts at zero (see below).

    We start with Weld, and first with the fits SciPy gives on its own (`nonnegative=False`).
    """)
    return


@app.cell
def _(flowsim, samples):
    free_weld_fits = flowsim.best_fit(
        data=samples["Weld"], 
        nonnegative=False,
    )

    free_weld_fits
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Look at `lower`. The top-ranked lognormal starts at about −1.2 minutes, even though no weld
    took less than 0.19 minutes, so it will occasionally draw a negative weld time (about 1 draw
    in 1,000). FlowSim stops with an error when a time is negative. One simulated day draws about
    96 weld times, so this fit would produce a negative time about once every ten simulated days,
    and the 500 days in the comparison at the end of the notebook would almost surely stop.

    The shift comes from the fit itself. SciPy fits the starting point (`loc`) along with the
    other parameters, and moving the start below zero can match the bulk of the data better. By
    default (`nonnegative=True`), `best_fit` refits any family that starts below zero with its
    start held at zero and marks it in `loc_fixed`, and it leaves out a family that still reaches
    below zero, such as the normal.
    """)
    return


@app.cell
def _(flowsim, samples):
    weld_fits = flowsim.best_fit(
        data=samples["Weld"],
        nonnegative=True,
    )

    weld_fits
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Every row now starts at zero or above, and the lognormal, held at zero, falls to fourth. Since
    no row can draw a negative time, the rule we use is simple. **Take the first row, i.e., the
    best-fitting nonnegative family.**

    Still read `upper` before using the fit. A finite `upper` is a ceiling that no simulated time
    can exceed. For Weld, the first-ranked beta has a ceiling so high (about 580 billion minutes)
    that it behaves like the gamma it ties with. For the release gap, the beta's ceiling is 107
    minutes, nearly three times the longest gap in the data (38 minutes), so it removes nothing the
    shop has seen. A ceiling close to the largest observation would be a reason to take the next
    row. The plot shows the data with the top three fits for any input.
    """)
    return


@app.cell
def _(flowsim, samples):
    fits = {
        name: flowsim.best_fit(data=values, nonnegative=True)
        for name, values in samples.items()
    }
    # With nonnegative=True, every row starts at zero or above, so the best
    # nonnegative fit is simply the first row (rank 1).
    chosen = {name: table.row(0, named=True) for name, table in fits.items()}
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
def _(chosen, fits, go, input_picker, np, samples, st):
    _name = input_picker.value
    _values = samples[_name]
    _grid = np.linspace(0, np.quantile(_values, 0.995), 300)
    _figure = go.Figure()
    _figure.add_histogram(
        x=_values,
        histnorm="probability density",
        name="data",
        opacity=0.4,
    )
    _shown = fits[_name].head(3).to_dicts()
    if chosen[_name]["family"] not in [_row["family"] for _row in _shown]:
        _shown.append(chosen[_name])
    for _row in _shown:
        _label = f"{_row['rank']}. {_row['family']} (KS {_row['ks']:.3f})"
        if _row["family"] == chosen[_name]["family"]:
            _label += ", chosen"
        _figure.add_scatter(
            x=_grid,
            y=getattr(st, _row["family"]).pdf(_grid, *_row["params"]),
            mode="lines",
            name=_label,
        )
    _figure.update_layout(
        title=f"{_name}, data and fitted densities",
        xaxis_title="minutes",
        yaxis_title="density",
    )
    _figure
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The table lists the family the rule chose for each input. Two of the four are betas held at
    zero, and the exponential, which is what releases at random moments through the day produce,
    is a close second for the release gap (KS 0.018 against 0.014).
    """)
    return


@app.cell
def _(chosen, pl):
    pl.DataFrame(
        [
            {
                "input": name,
                "family": row["family"],
                "rank": row["rank"],
                "ks": row["ks"],
                "lower": row["lower"],
                "upper": row["upper"],
                "loc_fixed": row["loc_fixed"],
            }
            for name, row in chosen.items()
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3, turn a fit into a sampler

    `flowsim.sampler(family, params)` returns a function. Each time we call it with a random-number
    generator, it returns one draw from the fitted distribution. FlowSim calls it the same way
    every time a job starts at a station, so a sampler is how a fitted distribution gets into
    the model. The generator is created from a seed, so the same seed gives the same draws.
    """)
    return


@app.cell
def _(SEED, chosen, flowsim, np):
    weld_time = flowsim.sampler(
        family=chosen["Weld"]["family"],
        params=chosen["Weld"]["params"],
    )
    _rng = np.random.default_rng(SEED)

    [round(weld_time(_rng), 2) for _ in range(5)]
    return (weld_time,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    A check worth doing every time is to draw many values and compare them with the data. If the
    mean, the CV, and the 95th percentile are close, the sampler behaves like the shop.
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
def _(chosen, flowsim, model):
    # Block 2. Jobs released to the line, one release gap at a time.
    jobs = model.source(
        name="Jobs",
        interarrival=flowsim.sampler(
            family=chosen["Release gap"]["family"],
            params=chosen["Release gap"]["params"],
        ),
    )
    return (jobs,)


@app.cell
def _(chosen, flowsim, model):
    # Block 3. Cut, one machine. Released jobs wait in front of it with no limit on space.
    cut = model.station(
        name="Cut",
        capacity=1,
        service_time=flowsim.sampler(
            family=chosen["Cut"]["family"],
            params=chosen["Cut"]["params"],
        ),
    )
    return (cut,)


@app.cell
def _(WELD_RACK, chosen, flowsim, model):
    # Block 4. Weld, one machine, with a rack of WELD_RACK spaces in front of it.
    weld = model.station(
        name="Weld",
        capacity=1,
        service_time=flowsim.sampler(
            family=chosen["Weld"]["family"],
            params=chosen["Weld"]["params"],
        ),
        buffer=WELD_RACK,
        external_overflow="wait",
    )
    return (weld,)


@app.cell
def _(PAINT_RACK, chosen, flowsim, model):
    # Block 5. Paint, one machine, with a rack of PAINT_RACK spaces in front of it.
    paint = model.station(
        name="Paint",
        capacity=1,
        service_time=flowsim.sampler(
            family=chosen["Paint"]["family"],
            params=chosen["Paint"]["params"],
        ),
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
    resource plot shows when each machine was processing, idle, or blocked.
    """)
    return


@app.cell
def _(one_day):
    one_day.queue_plot()
    return


@app.cell
def _(one_day):
    one_day.resource_plot()
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
            interarrival=flowsim.sampler(
                family=chosen["Release gap"]["family"],
                params=chosen["Release gap"]["params"],
            ),
        )
        line_cut = line.station(
            name="Cut",
            capacity=1,
            service_time=flowsim.sampler(
                family=chosen["Cut"]["family"],
                params=chosen["Cut"]["params"],
            ),
        )
        line_weld = line.station(
            name="Weld",
            capacity=1,
            service_time=flowsim.sampler(
                family=chosen["Weld"]["family"],
                params=chosen["Weld"]["params"],
            ),
            buffer=weld_rack,
            external_overflow="wait",
        )
        line_paint = line.station(
            name="Paint",
            capacity=1,
            service_time=flowsim.sampler(
                family=chosen["Paint"]["family"],
                params=chosen["Paint"]["params"],
            ),
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
    2. In `build_line`, replace Weld's `service_time=flowsim.sampler(...)` with a constant, i.e.,
       `service_time=4.56` (the mean of the fitted Weld times). Does the line still need racks?
    3. Set `WELD_RACK = 0` in the settings cell and look at the resource plot for one day. When
       is Cut blocked?
    """)
    return


if __name__ == "__main__":
    app.run()
