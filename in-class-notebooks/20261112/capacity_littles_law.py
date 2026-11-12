import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import plotly.graph_objects as go
    import polars as pl
    import polars.selectors as cs
    from plotly.subplots import make_subplots

    from flowsim import Model, exponential

    return Model, cs, exponential, go, make_subplots, mo, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Capacity, bottlenecks, and Little's Law

    Today's question is why releasing more work into a line does not ship more. You work through it on
    a three-station line whose times never vary, then check Little's Law, which ties the number of
    jobs in a line to the time each one spends there.

    Each **Question** below has its results and its answer in collapsed sections under it. Think
    about the question first, then run the cell and open the sections.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Vocabulary

    | Term | Meaning | In FlowSim | Units |
    |---|---|---|---|
    | Throughput (TH) | The rate at which finished jobs leave the line | `throughput` | jobs per minute (multiply by 60 for jobs per hour) |
    | Station capacity (r) | The most jobs a station can finish per hour, i.e., machines × 60 ÷ minutes per job | `capacity=` sets the number of machines, not this rate | jobs per hour |
    | Bottleneck | The station with the lowest capacity | | |
    | Bottleneck rate (r_b) | The bottleneck's capacity, i.e., the most the line can ever ship | | jobs per hour |
    | Raw process time (T₀) | The sum of the stations' times, i.e., a job's time in the line if it never waits | | minutes |
    | Work in process (WIP) | The average number of jobs inside the line, waiting or being worked on | `mean_wip` | jobs |
    | Time in line (cycle time) | The time from when a job enters the line until it leaves | `mean_flow_time` minus `mean_outside_wait` | minutes |
    | Critical WIP (W₀) | r_b × T₀, i.e., the fewest jobs that keep the bottleneck always busy when times never vary | | jobs |
    | Utilization | The share of time a machine is occupied, working or blocked | `utilization` | fraction |
    | Processing utilization | The share of time a machine is working on a job | `processing_utilization` | fraction |
    | Blocking fraction | The share of time a machine holds a finished job because the space after it is full | `blocking_fraction` | fraction |
    | Starved | A machine is idle because no job has reached it | | |

    Two rules tie these together.

    - `utilization` = `processing_utilization` + `blocking_fraction`. A blocked machine looks busy
      but is not working, so processing utilization is the measure that finds the bottleneck.
    - **Little's Law** says WIP = TH × cycle time for a stable line over a long run, as long as all
      three use the same boundary and the same time units.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## The line on paper

    A line has three stations with one machine each. Every job visits S1 (4 minutes), then S2
    (6 minutes), then S3 (5 minutes), and the times never vary.

    **Question.** You run the plant. S1 sits idle sometimes, so you tell it to run flat out. How
    many jobs per hour does the line ship? How long does a job take if it never waits?
    """)
    return


@app.cell
def _(pl):
    on_paper = pl.DataFrame(
        {
            "station": ["S1", "S2", "S3"],
            "minutes_per_job": [4, 6, 5],
        }
    ).with_columns(
        (60 / pl.col("minutes_per_job")).alias("jobs_per_hour"),
    )
    bottleneck_rate = on_paper["jobs_per_hour"].min()
    raw_process_time = on_paper["minutes_per_job"].sum()
    critical_wip = bottleneck_rate * raw_process_time / 60
    return bottleneck_rate, critical_wip, on_paper, raw_process_time


@app.cell(hide_code=True)
def _(bottleneck_rate, mo, on_paper, raw_process_time):
    mo.accordion(
        {
            "Result": on_paper,
            "Answer": mo.md(f"""
    The line ships **{bottleneck_rate:.0f} jobs per hour**, the capacity of S2, its bottleneck
    (r_b). Every job passes through every station, so the slowest one caps the line. Running S1 flat
    out makes 15 jobs per hour, and the 5 extra jobs each hour pile up in front of S2.

    A job that never waits takes **{raw_process_time} minutes**, i.e., 4 + 6 + 5. This is the raw
    process time (T₀).
    """),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Holding a fixed number of jobs in the line

    Suppose the shop keeps exactly N jobs in the line and starts a new job only when one finishes.
    With times that never vary, the best the line can do is

    - jobs per hour, TH(N) = min(N ÷ T₀, r_b), and
    - minutes per job, CT(N) = N ÷ TH(N), which is Little's Law rearranged.

    **Question.** As N goes from 1 to 6, where does output stop rising? What happens to the time
    each job takes after that point?
    """)
    return


@app.cell
def _(bottleneck_rate, pl, raw_process_time):
    fixed_wip = (
        pl.DataFrame({"jobs_in_line": list(range(1, 7))})
        .with_columns(
            pl.min_horizontal(
                pl.col("jobs_in_line") * 60 / raw_process_time,
                pl.lit(bottleneck_rate),
            ).alias("jobs_per_hour"),
        )
        .with_columns(
            (pl.col("jobs_in_line") / pl.col("jobs_per_hour") * 60).alias("minutes_per_job"),
        )
    )
    return (fixed_wip,)


@app.cell
def _(critical_wip, fixed_wip, go, make_subplots):
    fixed_wip_chart = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Jobs per hour", "Minutes per job"),
        horizontal_spacing=0.12,
    )
    for _column, _position, _color in [
        ("jobs_per_hour", 1, "#0173B2"),
        ("minutes_per_job", 2, "#DE8F05"),
    ]:
        fixed_wip_chart.add_trace(
            go.Scatter(
                x=fixed_wip["jobs_in_line"].to_list(),
                y=fixed_wip[_column].to_list(),
                mode="lines+markers",
                line={"color": _color, "width": 3},
                marker={"size": 10, "color": _color, "line": {"color": "black", "width": 1}},
                showlegend=False,
            ),
            row=1,
            col=_position,
        )
        _top = fixed_wip[_column].max() * 1.05
        fixed_wip_chart.add_trace(
            go.Scatter(
                x=[critical_wip, critical_wip],
                y=[0, _top],
                mode="lines+text",
                line={"dash": "dash", "color": "gray", "width": 2},
                text=["", f"critical WIP = {critical_wip:.1f}"],
                textposition="top center",
                showlegend=False,
                hoverinfo="skip",
            ),
            row=1,
            col=_position,
        )
    fixed_wip_chart.update_xaxes(title_text="Jobs held in the line (N)", dtick=1)
    fixed_wip_chart.update_yaxes(rangemode="tozero")
    fixed_wip_chart.update_layout(
        template="simple_white",
        height=380,
        margin={"t": 75, "b": 50, "l": 50, "r": 20},
    )
    return (fixed_wip_chart,)


@app.cell(hide_code=True)
def _(bottleneck_rate, critical_wip, fixed_wip, fixed_wip_chart, mo, raw_process_time):
    mo.accordion(
        {
            "Result": mo.vstack([fixed_wip, fixed_wip_chart]),
            "Answer": mo.md(f"""
    Output rises by 4 jobs per hour with each added job until N reaches the **critical WIP**,
    W₀ = r_b × T₀ = {bottleneck_rate:.0f} × {raw_process_time}/60 = **{critical_wip:.1f} jobs**. Below
    it, the line has too few jobs to keep every station fed. Above it, output stays at
    {bottleneck_rate:.0f} per hour, and each added job adds 6 minutes, one cycle of S2, and nothing
    else.
    """),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## The model: release a job every minute

    FlowSim cannot hold a line at exactly N jobs, since it limits the space at each station instead.
    The model below runs the same idea the way many shops do, releasing work faster than the line can
    finish it. Three settings matter.

    - `interarrival=1` releases a job every minute, i.e., 60 per hour, six times what the line can
      ship.
    - `service_time=4`, `6`, and `5` are plain numbers, so the times never vary.
    - S1 has `buffer=0` and `external_overflow="wait"`, so a job that has not started waits outside
      the line. The argument `rack` sets the space in front of S2 and S3.
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

    The run below has no racks and lasts 4,800 minutes, with the first 480 discarded as warm-up. The
    table shows how each station spends its time.

    **Question.** S1 and S2 both read 100% `utilization`. Which one is the bottleneck, and why?
    """)
    return


@app.cell
def _(saturated_line):
    no_racks = saturated_line(0).run(
        duration=4800,
        seed=1,
        warmup=480,
    )
    station_time = no_racks.stations.select(
        "station",
        "utilization",
        "processing_utilization",
        "blocking_fraction",
    )
    return no_racks, station_time


@app.cell(hide_code=True)
def _(cs, mo, station_time):
    _share = {
        row["station"]: row
        for row in station_time.iter_rows(named=True)
    }
    mo.accordion(
        {
            "Result": station_time.with_columns(cs.float().round(3)),
            "Answer": mo.md(f"""
    **S2 is the bottleneck.** It is the only station working the whole time
    (`processing_utilization` {_share["S2"]["processing_utilization"]:.0%}).

    S1's 100% is {_share["S1"]["processing_utilization"]:.0%} work and
    {_share["S1"]["blocking_fraction"]:.0%} blocked. S1 finishes a job every 4 minutes, but S2 takes
    one only every 6, so S1 holds each finished job for 2 minutes with nowhere to put it.

    S3 works {_share["S3"]["processing_utilization"]:.0%} of the time, which is 10 ÷ 12, the
    bottleneck rate over S3's own capacity. The rest of the time S3 is starved, waiting for S2.
    """),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Add racks of 1, 2, and 4

    With no racks, the line ships 10 jobs per hour.

    **Question.** Put a rack of 4 jobs in front of S2 and S3. What happens to jobs per hour, to the
    number of jobs in the line, and to the minutes each job spends in the line?
    """)
    return


@app.cell
def _(pl, saturated_line):
    rack_rows = []
    for _rack in [0, 1, 2, 4]:
        _summary = (
            saturated_line(_rack)
            .run(
                duration=4800,
                seed=1,
                warmup=480,
            )
            .summary.select(
                pl.lit(_rack).alias("racks"),
                pl.col("mean_wip").alias("jobs_in_line"),
                (pl.col("throughput") * 60).alias("jobs_per_hour"),
                (pl.col("mean_flow_time") - pl.col("mean_outside_wait")).alias("minutes_in_line"),
                pl.col("mean_outside_wait").alias("minutes_outside"),
            )
        )
        rack_rows.append(_summary)
    racks = pl.concat(rack_rows)
    return (racks,)


@app.cell(hide_code=True)
def _(cs, mo, racks):
    _no_rack = racks.row(0, named=True)
    _four = racks.row(3, named=True)
    mo.accordion(
        {
            "Result": racks.with_columns(cs.float().round(2)),
            "Answer": mo.md(f"""
    **Output does not move.** It stays at {_four["jobs_per_hour"]:.0f} jobs per hour with racks of 4.
    The line holds {_four["jobs_in_line"]:.2f} jobs instead of {_no_rack["jobs_in_line"]:.2f}, and
    each job spends {_four["minutes_in_line"]:.0f} minutes in the line instead of
    {_no_rack["minutes_in_line"]:.0f}.

    - Each rack slot adds one job and 6 minutes, one cycle of S2. Only S2's rack fills, since S3 is
      faster than S2.
    - Even with no racks, a job spends {_no_rack["minutes_in_line"]:.0f} minutes in the line, not
      T₀ = 15, because S1 holds each finished job for 2 minutes while it is blocked.
    - Last week racks helped, because the times varied and a rack absorbed the variation. Here the
      times never vary, so a rack has nothing to absorb and only adds waiting. November 17 picks
      this up.
    """),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Little's Law

    For a stable line observed over a long run,

    **WIP = TH × cycle time**, so cycle time = WIP ÷ TH.

    It holds whatever the distributions of times, as long as all three use the same boundary and the
    same time units, so any two of the numbers give you the third. For the line with no racks, for
    example, 2.83 jobs ÷ 10 jobs per hour = 0.283 hours, or 17 minutes.

    **Question.** Does jobs ÷ jobs per hour give the minutes in the line for every rack size?
    """)
    return


@app.cell
def _(pl, racks):
    littles_check = racks.select(
        "racks",
        "minutes_in_line",
        (pl.col("jobs_in_line") / pl.col("jobs_per_hour") * 60).alias("jobs_over_rate_in_minutes"),
    )
    return (littles_check,)


@app.cell(hide_code=True)
def _(cs, littles_check, mo):
    mo.accordion(
        {
            "Result": littles_check.with_columns(cs.float().round(2)),
            "Answer": mo.md("""
    Yes. `jobs_over_rate_in_minutes` equals `minutes_in_line` in every row, so the number of jobs
    in the line and the rate they leave it are enough to give the time each job spends there.
    """),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    **Question.** A line holds 8 jobs on average and finishes 9 jobs per hour. How long does a job
    spend inside it?
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "Answer": mo.md("""
    8 ÷ 9 = 0.89 hours, or **53.3 minutes**.
    """),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Little's Law with random times

    Times that never vary make the law look like plain arithmetic. The run below has one machine,
    jobs arriving every 5 minutes on average, and jobs taking 4 minutes on average, both random, so
    the machine is 80% busy. It runs for 200,000 minutes, with the first 20,000 discarded as warm-up.

    **Question.** Does throughput × time in the system still equal the average number of jobs?
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
    random_times = long_run.run(
        duration=200_000,
        seed=7,
        warmup=20_000,
    ).summary.select(
        "mean_wip",
        "throughput",
        "mean_flow_time",
        (pl.col("throughput") * pl.col("mean_flow_time")).alias("throughput_x_flow_time"),
    )
    return (random_times,)


@app.cell(hide_code=True)
def _(cs, mo, random_times):
    _row = random_times.row(0, named=True)
    mo.accordion(
        {
            "Result": random_times.with_columns(cs.float().round(3)),
            "Answer": mo.md(f"""
    Yes. `mean_wip` is {_row["mean_wip"]:.3f} and `throughput_x_flow_time` is
    {_row["throughput_x_flow_time"]:.3f}. The law does not depend on how the times are distributed.
    Quiz 4, after November 17, asks you to find this in your own numbers.
    """),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## The boundary matters

    Go back to the line with no racks. Little's Law gave 17 minutes in the line, but FlowSim's
    `mean_flow_time` for the same run is far larger.

    **Question.** Which number is right, and why do they differ?
    """)
    return


@app.cell
def _(no_racks, pl):
    boundary = no_racks.summary.select(
        "mean_wip",
        (pl.col("throughput") * 60).alias("jobs_per_hour"),
        "mean_flow_time",
        "mean_outside_wait",
        (pl.col("throughput") * pl.col("mean_flow_time")).alias("throughput_x_flow_time"),
        (pl.col("throughput") * (pl.col("mean_flow_time") - pl.col("mean_outside_wait"))).alias(
            "throughput_x_time_in_line"
        ),
    )
    return (boundary,)


@app.cell(hide_code=True)
def _(boundary, cs, mo):
    _row = boundary.row(0, named=True)
    mo.accordion(
        {
            "Result": boundary.with_columns(cs.float().round(2)),
            "Answer": mo.md(f"""
    **Both are right, on different boundaries.** `mean_flow_time`
    ({_row["mean_flow_time"]:,.0f} minutes) starts the clock when a job is released, so it includes
    the {_row["mean_outside_wait"]:,.0f} minutes a job waits outside the line. `mean_wip`
    ({_row["mean_wip"]:.2f} jobs) counts only jobs inside the line.

    - Throughput × the full flow time is {_row["throughput_x_flow_time"]:,.0f} jobs, nowhere near
      `mean_wip`, because the two use different boundaries.
    - Throughput × the time inside the line is {_row["throughput_x_time_in_line"]:.2f} jobs, which
      matches `mean_wip`, because both measure inside the line.
    - The queue outside grows by 50 jobs every hour (60 released, 10 shipped) and never settles, so
      the boundary that includes it is not even stable.

    Over one short shift the law is also only approximate, since the shift starts empty and ends
    partly full. Quiz 3's Part E asks about both effects.
    """),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Wrap-up

    - The bottleneck sets the most a line can ship, here 10 jobs per hour.
    - Work released faster than that only adds waiting, in the racks or outside the line.
    - Little's Law converts jobs into time, WIP = TH × cycle time, when all three use the same
      boundary and the same units.

    **Next.** Quiz 3 applies these ideas to a line whose times vary. Open its notebook from this
    folder with `pixi run quiz3`, and follow the handout on Blackboard.

    **For November 17.** A machine at 90% utilization has 10% spare capacity. Is that safe?
    """)
    return


if __name__ == "__main__":
    app.run()
