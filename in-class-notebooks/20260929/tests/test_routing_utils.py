from itertools import permutations
from pathlib import Path

import polars as pl
import pytest

from routing_utils import (
    build_distance_lookup,
    plot_locations,
    route_distance,
    route_load,
    solve_tsp,
    summarize_routes,
    validate_routes,
)


DATA_DIR = Path(__file__).parents[1] / "data"


@pytest.fixture(scope="module")
def georgia():
    locations = pl.read_parquet(DATA_DIR / "store_locations.parquet").filter(
        pl.col("state") == "GA"
    )
    stores = locations.get_column("store").to_list()
    distances = build_distance_lookup(
        road_distances=pl.read_parquet(DATA_DIR / "road_distances.parquet"),
        stores=stores,
    )
    demand = dict(pl.read_parquet(DATA_DIR / "store_demand.parquet").iter_rows())
    return locations, stores, distances, demand


def test_generated_data_covers_every_store_and_state():
    locations = pl.read_parquet(DATA_DIR / "store_locations.parquet")
    demand = pl.read_parquet(DATA_DIR / "store_demand.parquet")
    hubs = pl.read_parquet(DATA_DIR / "state_hubs.parquet")

    assert sorted(demand.get_column("store").to_list()) == sorted(
        locations.get_column("store").to_list()
    )
    assert demand.get_column("demand_pallets").is_between(1, 6).all()
    assert sorted(hubs.get_column("state").to_list()) == sorted(
        locations.get_column("state").unique().to_list()
    )
    hub_states = hubs.join(
        other=locations.select(
            pl.col("store").alias("hub_store"),
            pl.col("state").alias("store_state"),
        ),
        on="hub_store",
        how="inner",
    )
    assert (hub_states.get_column("state") == hub_states.get_column("store_state")).all()
    assert hubs.filter(pl.col("state") == "GA").item(0, "hub_store") == "L210"


def test_route_distance_includes_return_leg(georgia):
    _, stores, distances, _ = georgia
    depot, first, second = stores[:3]
    expected = (
        distances[(depot, first)]
        + distances[(first, second)]
        + distances[(second, depot)]
    )
    assert route_distance([depot, first, second], distances) == pytest.approx(expected)
    assert route_distance([depot], distances) == 0.0


def test_route_load_excludes_depot(georgia):
    _, stores, _, demand = georgia
    depot, first, second = stores[:3]
    assert route_load([depot, first, second], demand) == demand[first] + demand[second]


def test_solve_tsp_matches_brute_force_on_small_route(georgia):
    _, stores, distances, _ = georgia
    depot = "L210"
    stops = [store for store in stores if store != depot][:6]
    route = solve_tsp(
        depot=depot,
        stops=stops,
        distances=distances,
    )
    assert route[0] == depot
    assert sorted(route[1:]) == sorted(stops)

    optimum = min(
        route_distance([depot, *order], distances) for order in permutations(stops)
    )
    assert route_distance(route, distances) == pytest.approx(optimum)


def test_solve_tsp_is_no_worse_than_input_order(georgia):
    _, stores, distances, _ = georgia
    depot = "L210"
    stops = [store for store in stores if store != depot][:25]
    route = solve_tsp(
        depot=depot,
        stops=stops,
        distances=distances,
    )
    assert sorted(route[1:]) == sorted(stops)
    assert route_distance(route, distances) <= route_distance([depot, *stops], distances)


def test_validate_routes_accepts_one_truck_per_customer(georgia):
    _, stores, _, demand = georgia
    customers = [store for store in stores if store != "L210"]
    validate_routes(
        [["L210", customer] for customer in customers],
        depots=["L210"],
        customers=customers,
        demand=demand,
        capacity=26,
    )


def test_validate_routes_reports_every_problem(georgia):
    _, stores, _, demand = georgia
    customers = [store for store in stores if store != "L210"]
    heavy = sorted(customers, key=lambda store: -demand[store])[:6]
    routes = [
        ["L210", *heavy],
        [customers[0], "L210"],
        ["L210", heavy[0]],
    ]
    with pytest.raises(ValueError) as error:
        validate_routes(
            routes,
            depots=["L210"],
            customers=customers,
            demand=demand,
            capacity=26,
        )
    message = str(error.value)
    assert "above capacity" in message
    assert "not a depot" in message
    assert "passes through depot" in message
    assert "Unserved customers" in message
    assert "more than once" in message


def test_summarize_routes_columns(georgia):
    _, stores, distances, demand = georgia
    summary = summarize_routes(
        [["L210", stores[0]], ["L210", stores[1], stores[2]]],
        demand=demand,
        distances=distances,
    )
    assert summary.columns == ["route", "depot", "stops", "load_pallets", "road_miles"]
    assert summary.get_column("stops").to_list() == [1, 2]


def test_plot_accepts_several_depots():
    locations = pl.read_parquet(DATA_DIR / "store_locations.parquet").filter(
        pl.col("state").is_in(["GA", "AL"])
    )
    figure, _ = plot_locations(
        locations=locations,
        routes=[["L210", "L194", "L240"], ["L3", "L1"]],
        depots=["L210", "L3"],
    )
    assert figure is not None
