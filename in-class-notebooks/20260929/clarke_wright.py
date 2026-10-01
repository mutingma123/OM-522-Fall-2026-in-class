import marimo

__generated_with = "0.24.0"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    from pathlib import Path

    import matplotlib.pyplot as plt
    import numpy as np
    import polars as pl
    import seaborn as sns

    sns.set_style("whitegrid")
    plt.rcParams["font.family"] = "serif"

    from routing_utils import (
        build_distance_lookup,
        plot_locations,
        route_distance,
        route_load,
        solve_tsp,
        summarize_routes,
        validate_routes,
    )

    return (
        Path,
        build_distance_lookup,
        mo,
        np,
        pl,
        plot_locations,
        plt,
        route_distance,
        route_load,
        sns,
        solve_tsp,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # OM 522 Clarke–Wright Savings

    The TSP meetings built one tour through every store. Here a hub ships pallets
    to its stores with trucks of limited capacity, so the stores must be split
    into several routes, each starting and ending at the depot. The Clarke–Wright
    savings method starts with one truck per customer and repeatedly merges routes
    whose combined load still fits on a truck.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Instance settings

    `selected_states` controls which stores are in the instance. Each state has
    one hub store, and the hubs of the selected states are the depots. A 53-foot
    trailer holds 26 standard pallets.
    """)
    return


@app.cell
def _():
    selected_states = ["GA"]
    vehicle_capacity = 26
    return selected_states, vehicle_capacity


@app.cell
def _(Path, pl):
    data_dir = Path(__file__).parent / "data"
    all_locations = pl.read_parquet(data_dir / "store_locations.parquet")
    all_road_distances = pl.read_parquet(data_dir / "road_distances.parquet")
    store_demand = pl.read_parquet(data_dir / "store_demand.parquet")
    state_hubs = pl.read_parquet(data_dir / "state_hubs.parquet")
    return all_locations, all_road_distances, state_hubs, store_demand


@app.cell
def _(
    all_locations,
    all_road_distances,
    build_distance_lookup,
    pl,
    selected_states,
    state_hubs,
    store_demand,
):
    locations = all_locations.filter(pl.col("state").is_in(selected_states))
    hubs = state_hubs.filter(pl.col("state").is_in(selected_states))

    depots = hubs.get_column("hub_store").to_list()
    customers = sorted(set(locations.get_column("store").to_list()) - set(depots))

    # Pallets ordered by each customer. Depots place no orders.
    demand = {
        store: pallets
        for store, pallets in store_demand.iter_rows()
        if store in customers
    }

    # distance_dict[(origin, destination)] gives road miles, as in the TSP notebook.
    distance_dict = build_distance_lookup(
        road_distances=all_road_distances,
        stores=locations.get_column("store").to_list(),
    )
    return customers, demand, depots, distance_dict, locations


@app.cell(hide_code=True)
def _(customers, demand, depots, mo, np, vehicle_capacity):
    _total_pallets = sum(demand.values())
    _minimum_trucks = int(np.ceil(_total_pallets / vehicle_capacity))

    mo.md(f"""
    The instance has **{len(customers)} customer stores** and
    **{len(depots)} depot{"s" if len(depots) > 1 else ""}**. Customers order
    **{_total_pallets} pallets** in total, between {min(demand.values())} and
    {max(demand.values())} each. With {vehicle_capacity} pallets per truck, any
    feasible plan needs at least **{_minimum_trucks} trucks**.
    """)
    return


@app.cell
def _(depots, locations, plot_locations):
    _instance_figure, _instance_axes = plot_locations(
        locations=locations,
        depots=depots,
        figsize=(8, 5),
    )
    _instance_figure
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Tools carried over from the TSP meetings

    A route is a list of store IDs whose first entry is its depot, e.g.,
    `["L210", "L194", "L240"]`. The return to the depot is implied, so the depot
    is never repeated at the end. `routing_utils.py` provides the following:

    - `route_distance(route, distances)` returns road miles, including the
      return leg.
    - `route_load(route, demand)` returns the pallets delivered on the route.
    - `solve_tsp(depot, stops, distances)` sequences one truck's stops with
      multistart Nearest Neighbor followed by subsequence reversal (2-opt), and
      returns a route that starts at the depot.
    - `validate_routes(routes, depots, customers, demand, capacity)` raises an
      error that lists every customer left unserved or served twice, every
      route that passes through a depot, and every route over capacity.
    - `summarize_routes(routes, demand, distances)` returns one row per route
      with its stops, load, and miles.
    - `plot_locations(locations, routes, depots)` draws the routes and numbers
      each one.

    For example, the cell below sequences the five Georgia customers closest to
    the Atlanta hub (L210) as a single truck. The store IDs are written out, so
    the cell runs only when `selected_states` includes `"GA"`.
    """)
    return


@app.cell
def _(demand, distance_dict, route_distance, route_load, solve_tsp):
    _depot = "L210"
    _stops = ["L195", "L227", "L253", "L230", "L194"]
    _example_route = solve_tsp(
        depot=_depot,
        stops=_stops,
        distances=distance_dict,
    )
    _distance = route_distance(
        route=_example_route,
        distances=distance_dict,
    )
    _route_load = route_load(
        route=_example_route,
        demand=demand,
    )

    print(_example_route)
    print(f"{_distance:,.1f} road miles")
    print(f"{_route_load} pallets")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    With more than one state selected, `depots` lists every selected hub.
    Deciding which depot serves each customer is then an additional decision
    that comes before the savings step, because the savings formula measures
    distances from a single depot.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Setup
    """)
    return


@app.cell
def _(customers, demand, depots, plt, sns, vehicle_capacity):
    cw_depot = depots[0]
    cw_customers = list(customers)
    cw_capacity = vehicle_capacity

    print(f" - {cw_depot = }")
    print(f" - Number of customers: {len(cw_customers):,}")
    print(f" - {cw_capacity = :,}")

    _fig, _ax = plt.subplots(
        nrows=1,
        ncols=1,
        figsize=(6, 4),
    )
    sns.histplot(
        x=list(demand.values()),
        edgecolor="k",
        discrete=True,
        stat="density",
        ax=_ax,
    )
    _ax.set_title("Customer demand")
    _ax.set_xlabel("Pallets ordered")
    _fig
    return (cw_depot,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1. Savings

    $$s_{ij} = d_{0i} + d_{0j} - d_{ij}$$
    """)
    return


@app.cell
def _(customers, cw_depot, distance_dict, pl):
    cluster2customer = {}
    customer2cluster = {}
    for _idx, _customer in enumerate(customers, start=1):
        cluster2customer[f'C{_idx}'] = [_customer]
        customer2cluster[_customer] = f'C{_idx}'


    savings = []
    for _i in customers:
        for _j in customers:
            if _i < _j:
                _pair_savings = distance_dict[cw_depot, _i] + distance_dict[cw_depot, _j] - distance_dict[_i, _j]
                savings.append({
                    'customer1': _i,
                    'customer2': _j,
                    'savings': _pair_savings
                })

    savings = pl.DataFrame(
        savings
    ).sort(
        by='savings',
        descending=True,
    ).to_dicts()
    return cluster2customer, customer2cluster, savings


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2. Merge routes in savings order
    """)
    return


@app.cell
def _(cluster2customer, customer2cluster, demand, savings):
    _entry = savings[0]
    _customer1 = _entry.get('customer1')
    _customer2 = _entry.get('customer2')

    _cluster1 = customer2cluster[_customer1]
    _cluster2 = customer2cluster[_customer2]

    same_cluster = _cluster1 == _cluster2

    if not same_cluster:
        print('Not the same')
        _cluster1_customers = cluster2customer[_cluster1]
        _cluster2_customers = cluster2customer[_cluster2]

    _all_customers = set(_cluster1_customers).union(set(_cluster2_customers))
    sum(d for customer, d in demand.items() if customer in  _all_customers)
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3. Check the routes and sequence each truck
    """)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
