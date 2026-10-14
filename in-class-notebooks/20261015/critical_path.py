import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import networkx as nx
    import polars as pl
    import seaborn as sns
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    sns.set_style("whitegrid")
    plt.rcParams["font.family"] = "serif"
    COLORS = sns.color_palette("colorblind").as_hex()
    CRITICAL = COLORS[1]
    NONCRITICAL = COLORS[0]
    return CRITICAL, Line2D, NONCRITICAL, Patch, mo, nx, pl, plt, sns


@app.cell
def _(mo):
    mo.md("""
    # The critical path method

    This notebook schedules the launch of a new production cell, the October 15 class example.
    Each task has a duration in days and a list of predecessors, i.e., tasks that must finish
    before it can start. We store the project as a directed graph in networkx, run the forward
    and backward passes over it, and read the slack and the critical path from the result.
    Moving a slider below changes a duration, and every table and chart recomputes.
    """)
    return


@app.cell
def _():
    TASKS = {
        "A": {"name": "Specify cell", "duration": 4, "predecessors": []},
        "B": {"name": "Order equipment", "duration": 3, "predecessors": ["A"]},
        "C": {"name": "Design layout", "duration": 5, "predecessors": ["A"]},
        "D": {"name": "Prepare utilities", "duration": 4, "predecessors": ["B"]},
        "E": {"name": "Install equipment", "duration": 6, "predecessors": ["B", "C"]},
        "F": {"name": "Train operators", "duration": 3, "predecessors": ["C"]},
        "G": {"name": "Validate cell", "duration": 2, "predecessors": ["D", "E", "F"]},
    }
    return (TASKS,)


@app.cell
def _(TASKS, mo):
    durations = mo.ui.dictionary(
        {
            task: mo.ui.slider(
                start=1,
                stop=12,
                value=data["duration"],
                label=f"{task} {data['name']} (days)",
                show_value=True,
            )
            for task, data in TASKS.items()
        }
    )
    mo.vstack(
        [
            mo.md("## Task durations"),
            durations,
        ]
    )
    return (durations,)


@app.cell
def _(TASKS, durations, nx):
    # One node per task, one edge per precedence requirement (predecessor -> task).
    graph = nx.DiGraph()
    for _task, _data in TASKS.items():
        graph.add_node(
            _task,
            name=_data["name"],
            duration=durations.value[_task],
        )
    for _task, _data in TASKS.items():
        for _predecessor in _data["predecessors"]:
            graph.add_edge(_predecessor, _task)
    return (graph,)


@app.cell
def _(nx):
    def cpm(graph):
        """Return each task's early and late times and slack, and the project duration."""
        order = list(nx.topological_sort(graph))
        times = {}
        # Forward pass: a task starts when its last predecessor finishes.
        for task in order:
            early_start = max(
                (times[predecessor]["EF"] for predecessor in graph.predecessors(task)),
                default=0,
            )
            times[task] = {
                "ES": early_start,
                "EF": early_start + graph.nodes[task]["duration"],
            }
        project_duration = max(task_times["EF"] for task_times in times.values())
        # Backward pass: a task must finish by the time its earliest-due successor must start.
        for task in reversed(order):
            late_finish = min(
                (times[successor]["LS"] for successor in graph.successors(task)),
                default=project_duration,
            )
            times[task]["LF"] = late_finish
            times[task]["LS"] = late_finish - graph.nodes[task]["duration"]
            times[task]["slack"] = times[task]["LS"] - times[task]["ES"]
        return times, project_duration

    return (cpm,)


@app.cell
def _(cpm, graph):
    times, project_duration = cpm(graph)
    critical_tasks = [task for task in graph if times[task]["slack"] == 0]
    return critical_tasks, project_duration, times


@app.cell
def _(graph, nx):
    # Path lengths: add Start and Finish nodes and weight each edge by the duration of the task
    # it leaves, so a path's weight is the sum of its task durations.
    timed = nx.DiGraph()
    for _task in graph:
        _duration = graph.nodes[_task]["duration"]
        if graph.in_degree(_task) == 0:
            timed.add_edge("Start", _task, weight=0)
        if graph.out_degree(_task) == 0:
            timed.add_edge(_task, "Finish", weight=_duration)
        for _successor in graph.successors(_task):
            timed.add_edge(_task, _successor, weight=_duration)
    paths = [
        _path[1:-1]
        for _path in nx.all_simple_paths(
            timed,
            source="Start",
            target="Finish",
        )
    ]
    longest_length = nx.dag_longest_path_length(timed, weight="weight")
    return longest_length, paths


@app.cell
def _(
    critical_tasks,
    graph,
    longest_length,
    mo,
    paths,
    pl,
    project_duration,
    times,
):
    assert longest_length == project_duration, "The longest path should equal the forward pass."
    _path_table = (
        pl.DataFrame(
            {
                "Path": [" → ".join(_path) for _path in paths],
                "Length (days)": [
                    sum(graph.nodes[_task]["duration"] for _task in _path) for _path in paths
                ],
            }
        )
        .with_columns(
            (pl.col("Length (days)") == project_duration).alias("Critical"),
        )
        .sort("Length (days)", descending=True)
    )
    _critical_paths = _path_table.filter(pl.col("Critical")).get_column("Path").to_list()
    _times_table = pl.DataFrame(
        [
            {
                "Task": _task,
                "Name": graph.nodes[_task]["name"],
                "Duration": graph.nodes[_task]["duration"],
                "ES": times[_task]["ES"],
                "EF": times[_task]["EF"],
                "LS": times[_task]["LS"],
                "LF": times[_task]["LF"],
                "Slack": times[_task]["slack"],
            }
            for _task in graph
        ]
    )
    mo.vstack(
        [
            mo.md(
                f"""
                ## Results

                The project takes **{project_duration} days**. The critical tasks (zero slack) are
                {", ".join(critical_tasks)}, and the critical path is
                {" and ".join(_critical_paths)}. The longest path that networkx finds with
                `dag_longest_path_length` is also {longest_length} days, which checks the passes.
                """
            ),
            _times_table,
            mo.md(
                "Every start-to-finish path, longest first. A task's slack is the project "
                "duration minus the longest path through it."
            ),
            _path_table,
        ]
    )
    return


@app.cell
def _(CRITICAL, NONCRITICAL, Patch, graph, nx, plt, times):
    # Columns come from topological generations, so the layout works for any network. Within a
    # column, tasks keep their table order from top to bottom.
    _order = list(graph)
    _positions = {}
    for _layer, _tasks in enumerate(nx.topological_generations(graph)):
        _tasks = sorted(_tasks, key=_order.index)
        for _row, _task in enumerate(_tasks):
            _positions[_task] = (_layer, (len(_tasks) - 1) / 2 - _row)
    _critical_edges = [
        (_u, _v)
        for _u, _v in graph.edges
        if times[_u]["slack"] == 0
        and times[_v]["slack"] == 0
        and times[_u]["EF"] == times[_v]["ES"]
    ]
    _figure, _axis = plt.subplots(figsize=(8, 5))
    nx.draw_networkx_edges(
        graph,
        pos=_positions,
        ax=_axis,
        edge_color="0.6",
        arrowsize=16,
        node_size=2600,
    )
    nx.draw_networkx_edges(
        graph,
        pos=_positions,
        ax=_axis,
        edgelist=_critical_edges,
        edge_color=CRITICAL,
        width=3,
        arrowsize=18,
        node_size=2600,
    )
    nx.draw_networkx_nodes(
        graph,
        pos=_positions,
        ax=_axis,
        node_color=[CRITICAL if times[_task]["slack"] == 0 else NONCRITICAL for _task in graph],
        node_size=2600,
        edgecolors="black",
    )
    nx.draw_networkx_labels(
        graph,
        pos=_positions,
        ax=_axis,
        labels={_task: f"{_task}\n{graph.nodes[_task]['duration']} days" for _task in graph},
        font_family="serif",
        font_size=10,
    )
    for _task, (_x, _y) in _positions.items():
        _axis.annotate(
            f"ES {times[_task]['ES']}, LS {times[_task]['LS']}\nslack {times[_task]['slack']}",
            xy=(_x, _y),
            xytext=(0, -34),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=9,
        )
    _axis.legend(
        handles=[
            Patch(facecolor=CRITICAL, edgecolor="black", label="Critical task (no slack)"),
            Patch(facecolor=NONCRITICAL, edgecolor="black", label="Task with slack"),
        ],
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
    )
    _axis.margins(x=0.12, y=0.25)
    _axis.axis("off")
    _figure.tight_layout()
    network_figure = _figure
    network_figure
    return


@app.cell
def _(CRITICAL, Line2D, NONCRITICAL, Patch, graph, plt, project_duration, sns, times):
    _tasks = list(graph)
    _figure, _axis = plt.subplots(figsize=(8, 5))
    for _row, _task in enumerate(_tasks):
        _axis.barh(
            _row,
            graph.nodes[_task]["duration"],
            left=times[_task]["ES"],
            color=CRITICAL if times[_task]["slack"] == 0 else NONCRITICAL,
            edgecolor="k",
        )
        if times[_task]["slack"] > 0:
            _axis.barh(
                _row,
                times[_task]["slack"],
                left=times[_task]["EF"],
                color="white",
                edgecolor="0.4",
                hatch="//",
            )
    _axis.axvline(project_duration, color="k", linestyle="--", linewidth=1)
    _axis.set_yticks(
        range(len(_tasks)),
        labels=[f"{_task} {graph.nodes[_task]['name']}" for _task in _tasks],
    )
    _axis.invert_yaxis()
    _axis.set_xlim(0, project_duration + 1)
    _axis.set_xlabel("Day")
    _axis.legend(
        handles=[
            Patch(facecolor=CRITICAL, edgecolor="k", label="Critical task"),
            Patch(facecolor=NONCRITICAL, edgecolor="k", label="Task with slack"),
            Patch(facecolor="white", edgecolor="0.4", hatch="//", label="Slack"),
            Line2D(
                [0],
                [0],
                color="k",
                linestyle="--",
                linewidth=1,
                label="Project finish",
            ),
        ],
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
    )
    sns.despine(ax=_axis)
    _figure.tight_layout()
    gantt_figure = _figure
    gantt_figure
    return


@app.cell
def _(TASKS, mo):
    crew_first = mo.ui.dropdown(
        options=list(TASKS),
        value="B",
        label="First task",
    )
    crew_second = mo.ui.dropdown(
        options=list(TASKS),
        value="C",
        label="Second task",
    )
    mo.vstack(
        [
            mo.md(
                """
                ## When two tasks share a crew

                The critical path method assumes every task has the resources it needs. If two
                tasks share one crew, they cannot overlap, so we choose an order. Choosing an
                order adds one precedence edge, and we rerun the passes for each order.
                """
            ),
            mo.hstack(
                [crew_first, crew_second],
                justify="start",
            ),
        ]
    )
    return crew_first, crew_second


@app.cell
def _(
    cpm,
    crew_first,
    crew_second,
    graph,
    mo,
    nx,
    pl,
    project_duration,
    times,
):
    def overlaps(task_times, first, second):
        """Return True when two tasks overlap in the early-start schedule."""
        return max(task_times[first]["ES"], task_times[second]["ES"]) < min(
            task_times[first]["EF"], task_times[second]["EF"]
        )

    _first, _second = crew_first.value, crew_second.value
    if _first == _second:
        _crew_output = mo.md("Choose two different tasks.")
    elif not overlaps(times, _first, _second):
        _crew_output = mo.md(
            f"{_first} and {_second} do not overlap in the CPM schedule, so one crew can do "
            f"both and the project still takes {project_duration} days."
        )
    else:
        _rows = []
        for _before, _after in [(_first, _second), (_second, _first)]:
            _trial = graph.copy()
            _trial.add_edge(_before, _after)
            if nx.is_directed_acyclic_graph(_trial):
                _trial_times, _trial_duration = cpm(_trial)
                _rows.append(
                    {
                        "Crew order": f"{_before} then {_after}",
                        "Second task starts on day": _trial_times[_after]["ES"],
                        "Project duration (days)": _trial_duration,
                    }
                )
        _crew_table = pl.DataFrame(_rows)
        _best = _crew_table.get_column("Project duration (days)").min()
        _crew_output = mo.vstack(
            [
                mo.md(
                    f"In the CPM schedule, {_first} runs from day {times[_first]['ES']} to "
                    f"{times[_first]['EF']} and {_second} from day {times[_second]['ES']} to "
                    f"{times[_second]['EF']}, so they overlap. The better order finishes in "
                    f"**{_best} days**, compared with {project_duration} days for CPM. The CPM "
                    "duration is a lower bound once resources are limited."
                ),
                _crew_table,
            ]
        )
    _crew_output
    return


if __name__ == "__main__":
    app.run()
