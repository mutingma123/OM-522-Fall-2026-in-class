import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import networkx as nx
    import seaborn as sns
    from matplotlib.patches import Patch

    sns.set_style("whitegrid")
    plt.rcParams["font.family"] = "serif"
    _colors = sns.color_palette("colorblind").as_hex()
    CRITICAL = _colors[1]
    NONCRITICAL = _colors[0]
    return CRITICAL, NONCRITICAL, Patch, mo, nx, plt, sns


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # The critical path method

    This notebook schedules the launch of a new production cell, the October 15 class example.
    Each task has a duration in days and a list of predecessors, i.e., tasks that must finish
    before it can start. We store the project as a directed graph in networkx, run the forward
    and backward passes over it, and read the slack and the critical path from the result.

    The forward pass gives each task's earliest start (ES) and earliest finish (EF). The
    backward pass gives its latest start (LS) and latest finish (LF), i.e., the latest times
    that still let the project finish on time. A task's slack is LS minus ES, and a task with
    zero slack is critical.
    """)
    return


@app.cell
def _():
    TASKS = {
        "A": {"name": "Specify cell", "predecessors": [], "duration": 4},
        "B": {"name": "Order equipment", "predecessors": ["A"], "duration": 3},
        "C": {"name": "Design layout", "predecessors": ["A"], "duration": 5},
        "D": {"name": "Prepare utilities", "predecessors": ["B"], "duration": 4},
        "E": {"name": "Install equipment", "predecessors": ["B", "C"], "duration": 6},
        "F": {"name": "Train operators", "predecessors": ["C"], "duration": 3},
        "G": {"name": "Validate cell", "predecessors": ["D", "E", "F"], "duration": 2},
    }
    return (TASKS,)


@app.cell
def _(TASKS, nx):
    # One node per task, one edge per precedence requirement (predecessor -> task).
    graph = nx.DiGraph()
    for _task, _data in TASKS.items():
        graph.add_node(
            _task,
            name=_data["name"],
            duration=_data["duration"],
        )
    for _task, _data in TASKS.items():
        for _predecessor in _data["predecessors"]:
            graph.add_edge(_predecessor, _task)
    return (graph,)


@app.cell
def _(nx):
    def cpm(graph):
        """Run the forward and backward passes over a task graph.

        Returns (times, project_duration), where times[task] holds the task's ES, EF, LS, LF,
        and slack.
        """
        # Topological order puts every task after all of its predecessors.
        order = list(nx.topological_sort(graph))
        times = {}
        # Forward pass: a task starts when its last predecessor finishes, or on day 0 if it
        # has no predecessors.
        for _task in order:
            _duration = graph.nodes[_task].get("duration")
            _early_start = max(
                [times[_predecessor]["EF"] for _predecessor in graph.predecessors(_task)],
                default=0,
            )
            times[_task] = {
                "ES": _early_start,
                "EF": _early_start + _duration,
            }
        _project_duration = max([_entry["EF"] for _entry in times.values()])
        # Backward pass: a task must finish by the earliest LS among its successors, or by
        # the project finish if it has no successors.
        for _task in reversed(order):
            _duration = graph.nodes[_task].get("duration")
            _late_finish = min(
                [times[_successor]["LS"] for _successor in graph.successors(_task)],
                default=_project_duration,
            )
            times[_task]["LF"] = _late_finish
            times[_task]["LS"] = _late_finish - _duration
            times[_task]["slack"] = times[_task]["LS"] - times[_task]["ES"]
        return times, _project_duration

    return (cpm,)


@app.cell
def _(cpm, graph):
    times, project_duration = cpm(graph)
    critical_tasks = {task for task in graph if times[task]["slack"] == 0}
    return critical_tasks, project_duration, times


@app.cell
def _(CRITICAL, NONCRITICAL, Patch, critical_tasks, graph, nx, plt, times):
    # Each topological generation is a column. Within a column, tasks keep their TASKS order
    # from top to bottom, centered on y = 0.
    _order = list(graph)
    _positions = {}
    for _column, _generation in enumerate(nx.topological_generations(graph)):
        _column_tasks = sorted(_generation, key=_order.index)
        for _row, _task in enumerate(_column_tasks):
            _positions[_task] = (_column, (len(_column_tasks) - 1) / 2 - _row)
    # An edge is critical when both tasks are critical and the second starts the moment the
    # first finishes. The last test matters when two critical paths tie.
    _critical_edges = [
        (_before, _after)
        for _before, _after in graph.edges
        if _before in critical_tasks
        and _after in critical_tasks
        and times[_before]["EF"] == times[_after]["ES"]
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
        node_color=[CRITICAL if _task in critical_tasks else NONCRITICAL for _task in graph],
        node_size=2600,
        edgecolors="k",
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
            # Offset in points, enough to clear the node circle.
            xytext=(0, -34),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=9,
        )
    _axis.legend(
        handles=[
            Patch(
                facecolor=CRITICAL,
                edgecolor="k",
                label="Critical task (no slack)",
            ),
            Patch(
                facecolor=NONCRITICAL,
                edgecolor="k",
                label="Task with slack",
            ),
        ],
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
    )
    _axis.margins(
        x=0.12,
        y=0.25,
    )
    _axis.axis("off")
    _figure.tight_layout()
    _figure
    return


@app.cell
def _(
    CRITICAL,
    NONCRITICAL,
    Patch,
    critical_tasks,
    graph,
    plt,
    project_duration,
    sns,
    times,
):
    _tasks = list(graph)
    _figure, _axis = plt.subplots(figsize=(8, 5))
    for _row, _task in enumerate(_tasks):
        _axis.barh(
            _row,
            graph.nodes[_task]["duration"],
            left=times[_task]["ES"],
            color=CRITICAL if _task in critical_tasks else NONCRITICAL,
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
    _finish_line = _axis.axvline(
        project_duration,
        color="k",
        linestyle="--",
        linewidth=1,
        label="Project finish",
    )
    _axis.set_yticks(
        range(len(_tasks)),
        labels=[f"{_task} {graph.nodes[_task]['name']}" for _task in _tasks],
    )
    _axis.invert_yaxis()
    _axis.set_xlim(0, project_duration + 1)
    _axis.set_xlabel("Day")
    _axis.legend(
        handles=[
            Patch(
                facecolor=CRITICAL,
                edgecolor="k",
                label="Critical task",
            ),
            Patch(
                facecolor=NONCRITICAL,
                edgecolor="k",
                label="Task with slack",
            ),
            Patch(
                facecolor="white",
                edgecolor="0.4",
                hatch="//",
                label="Slack",
            ),
            _finish_line,
        ],
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
    )
    sns.despine(ax=_axis)
    _figure.tight_layout()
    _figure
    return


if __name__ == "__main__":
    app.run()
