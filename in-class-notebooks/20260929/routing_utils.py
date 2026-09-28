"""Utilities for plotting, checking, and sequencing vehicle routes.

A route is a list of store IDs whose first entry is the depot it leaves from,
e.g., ``["L210", "L194", "L240"]``. Every route closes back to its depot
automatically, so the depot is never repeated at the end.
"""

from collections.abc import Collection, Mapping, Sequence
from math import ceil, floor

import matplotlib.pyplot as plt
import polars as pl
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from mpl_toolkits.basemap import Basemap


Route = Sequence[str]
DistanceLookup = Mapping[tuple[str, str], float]


def _require_columns(
    dataframe: pl.DataFrame,
    required: Sequence[str],
    dataframe_name: str,
) -> None:
    missing = sorted(set(required) - set(dataframe.columns))
    if missing:
        raise ValueError(
            f"{dataframe_name} is missing required columns: {', '.join(missing)}"
        )


def _validate_route(route: Route) -> list[str]:
    if isinstance(route, (str, bytes)):
        raise TypeError("A route must be a sequence of store IDs, not a string.")

    values = list(route)
    if not all(isinstance(store_id, str) for store_id in values):
        raise TypeError("Every route entry must be a string store ID.")
    return values


def _close_route(route: Route) -> list[str]:
    values = _validate_route(route)
    if len(values) > 1 and values[-1] != values[0]:
        values.append(values[0])
    return values


def _normalize_routes(routes: Route | Sequence[Route] | None) -> list[list[str]]:
    if routes is None:
        return []
    if isinstance(routes, (str, bytes)):
        raise TypeError("routes must be a list of store IDs or a list of routes.")

    values = list(routes)
    if not values:
        return []
    if all(isinstance(value, str) for value in values):
        return [_validate_route(values)]
    if any(isinstance(value, (str, bytes)) for value in values):
        raise TypeError("Do not mix store IDs and nested routes in routes.")
    return [_validate_route(value) for value in values]


def _validated_locations(locations: pl.DataFrame) -> pl.DataFrame:
    if not isinstance(locations, pl.DataFrame):
        raise TypeError("locations must be a Polars DataFrame.")
    _require_columns(
        dataframe=locations,
        required=["store", "latitude", "longitude"],
        dataframe_name="locations",
    )
    if locations.is_empty():
        raise ValueError("locations must contain at least one row.")

    selected = locations.select(
        pl.col("store"),
        pl.col("latitude").cast(pl.Float64),
        pl.col("longitude").cast(pl.Float64),
    )
    if any(selected.null_count().row(0)):
        raise ValueError("locations contains null IDs or coordinates.")
    if selected.get_column("store").is_duplicated().any():
        raise ValueError("locations contains duplicate store IDs.")
    return selected


def build_distance_lookup(
    road_distances: pl.DataFrame,
    stores: Collection[str],
) -> dict[tuple[str, str], float]:
    """Return ``{(origin, destination): miles}`` for every pair of ``stores``.

    The lookup is checked for completeness and symmetry, because the TSP helper
    and the savings formula both assume that d(i, j) equals d(j, i).
    """
    _require_columns(
        dataframe=road_distances,
        required=["store1", "store2", "distance_miles"],
        dataframe_name="road_distances",
    )
    store_set = set(stores)
    lookup = {
        (origin, destination): float(miles)
        for origin, destination, miles in road_distances
        .filter(
            pl.col("store1").is_in(store_set),
            pl.col("store2").is_in(store_set),
            pl.col("store1") != pl.col("store2"),
        )
        .select(
            pl.col("store1"),
            pl.col("store2"),
            pl.col("distance_miles"),
        )
        .iter_rows()
    }
    expected_pairs = len(store_set) * (len(store_set) - 1)
    if len(lookup) != expected_pairs:
        raise ValueError(
            f"Expected {expected_pairs} ordered pairs but found {len(lookup)}."
        )
    asymmetric = [
        (origin, destination)
        for (origin, destination), miles in lookup.items()
        if abs(miles - lookup[(destination, origin)]) > 1e-9
    ]
    if asymmetric:
        raise ValueError(f"Distances are not symmetric for {asymmetric[:5]}.")
    return lookup


def route_distance(route: Route, distances: DistanceLookup) -> float:
    """Return the road miles of a route, including the return to its depot."""
    values = _validate_route(route)
    if len(values) < 2:
        return 0.0
    return sum(
        distances[(origin, destination)]
        for origin, destination in zip(values, values[1:] + values[:1])
    )


def route_load(route: Route, demand: Mapping[str, int]) -> int:
    """Return the pallets delivered on a route. The depot adds no demand."""
    return sum(demand[store_id] for store_id in _validate_route(route)[1:])


def validate_routes(
    routes: Sequence[Route],
    *,
    depots: Collection[str],
    customers: Collection[str],
    demand: Mapping[str, int],
    capacity: int,
) -> None:
    """Raise ValueError listing every way ``routes`` fails to be a feasible plan.

    A feasible plan starts every route at a depot, never visits a depot
    mid-route, serves every customer exactly once, and keeps every route's load
    within ``capacity``.
    """
    depot_set = set(depots)
    customer_set = set(customers)
    problems = []
    visit_counts: dict[str, int] = {}
    for route_number, route in enumerate(routes, start=1):
        values = _validate_route(route)
        if not values:
            problems.append(f"Route {route_number} is empty.")
            continue
        if values[0] not in depot_set:
            problems.append(f"Route {route_number} starts at {values[0]}, not a depot.")
        for store_id in values[1:]:
            if store_id in depot_set:
                problems.append(f"Route {route_number} passes through depot {store_id}.")
            elif store_id not in customer_set:
                problems.append(f"Route {route_number} visits unknown store {store_id}.")
            else:
                visit_counts[store_id] = visit_counts.get(store_id, 0) + 1
        load = sum(demand.get(store_id, 0) for store_id in values[1:])
        if load > capacity:
            problems.append(
                f"Route {route_number} carries {load} pallets, above capacity {capacity}."
            )

    unserved = sorted(customer_set - set(visit_counts))
    repeated = sorted(store_id for store_id, count in visit_counts.items() if count > 1)
    if unserved:
        problems.append(f"Unserved customers: {', '.join(unserved)}.")
    if repeated:
        problems.append(f"Customers served more than once: {', '.join(repeated)}.")
    if problems:
        raise ValueError("\n".join(problems))


def summarize_routes(
    routes: Sequence[Route],
    *,
    demand: Mapping[str, int],
    distances: DistanceLookup,
) -> pl.DataFrame:
    """Return one row per route with its depot, stop count, load, and miles."""
    return pl.DataFrame(
        [
            {
                "route": route_number,
                "depot": route[0],
                "stops": len(route) - 1,
                "load_pallets": route_load(route, demand),
                "road_miles": route_distance(route, distances),
            }
            for route_number, route in enumerate(routes, start=1)
        ],
        schema={
            "route": pl.Int64,
            "depot": pl.String,
            "stops": pl.Int64,
            "load_pallets": pl.Int64,
            "road_miles": pl.Float64,
        },
    )


def solve_tsp(
    depot: str,
    stops: Collection[str],
    distances: DistanceLookup,
) -> list[str]:
    """Sequence one vehicle's stops and return a route that starts at ``depot``.

    This is the two-phase heuristic from the TSP meetings. Multistart Nearest
    Neighbor builds a tour from every node (ties go to the lower store ID), and
    subsequence reversal (2-opt) then accepts improving reversals until none
    remains. The reversal search checks every pair of positions rather than
    sampling, so the result is deterministic and 2-opt locally optimal. It is not
    guaranteed to be the shortest possible route.
    """
    nodes = sorted({depot, *stops})
    if depot in stops:
        raise ValueError("The depot must not appear in stops.")
    if len(nodes) <= 3:
        return [depot, *sorted(stops)]

    best_tour: list[str] = []
    best_miles = float("inf")
    for start in nodes:
        tour = [start]
        unvisited = set(nodes) - {start}
        while unvisited:
            current = tour[-1]
            nearest = min(
                unvisited,
                key=lambda store_id: (distances[(current, store_id)], store_id),
            )
            tour.append(nearest)
            unvisited.remove(nearest)
        miles = route_distance(tour, distances)
        if miles < best_miles:
            best_tour = tour
            best_miles = miles

    depot_position = best_tour.index(depot)
    tour = best_tour[depot_position:] + best_tour[:depot_position]
    size = len(tour)
    improved = True
    while improved:
        improved = False
        # The depot stays in position 0. Reversing a segment that wraps past
        # the depot gives the same cycle as reversing its complement.
        for left in range(1, size - 1):
            for right in range(left + 1, size):
                before = tour[left - 1]
                first = tour[left]
                last = tour[right]
                after = tour[(right + 1) % size]
                change = (
                    distances[(before, last)]
                    + distances[(first, after)]
                    - distances[(before, first)]
                    - distances[(last, after)]
                )
                if change < -1e-9:
                    tour[left : right + 1] = tour[left : right + 1][::-1]
                    improved = True
    return tour


def plot_locations(
    locations: pl.DataFrame,
    routes: Route | Sequence[Route] | None = None,
    *,
    depots: Collection[str] = (),
    figsize: tuple[float, float] = (9, 7),
) -> tuple[Figure, Axes]:
    """Plot stores, depots, and optional closed routes over an offline map.

    A flat list of store IDs is one route and a nested list is one route per
    vehicle. Each route is numbered at the stop farthest from its first entry,
    so the map stays readable when there are more routes than distinct colors.
    ``depots`` are drawn as stars. ``figsize`` is the width and height in inches.
    """
    selected = _validated_locations(locations)
    normalized_routes = _normalize_routes(routes)
    known_ids = set(selected.get_column("store").to_list())
    route_ids = {store_id for route in normalized_routes for store_id in route}
    unknown_ids = sorted((route_ids | set(depots)) - known_ids)
    if unknown_ids:
        raise ValueError(f"Unknown store IDs: {', '.join(unknown_ids)}")

    minimum_latitude = selected.get_column("latitude").min()
    maximum_latitude = selected.get_column("latitude").max()
    minimum_longitude = selected.get_column("longitude").min()
    maximum_longitude = selected.get_column("longitude").max()
    latitude_padding = max(0.5, (maximum_latitude - minimum_latitude) * 0.05)
    longitude_padding = max(0.5, (maximum_longitude - minimum_longitude) * 0.05)

    with sns.axes_style("white"):
        figure, axes = plt.subplots(
            nrows=1,
            ncols=1,
            figsize=figsize,
            layout="constrained",
        )

    basemap = Basemap(
        projection="merc",
        llcrnrlat=minimum_latitude - latitude_padding,
        urcrnrlat=maximum_latitude + latitude_padding,
        llcrnrlon=minimum_longitude - longitude_padding,
        urcrnrlon=maximum_longitude + longitude_padding,
        resolution="l",
        ax=axes,
    )
    map_boundary = basemap.drawmapboundary(
        fill_color="white",
        linewidth=0.8,
    )
    map_boundary.set_zorder(-1)
    basemap.drawlsmask(
        land_color="#f2efe9",
        ocean_color="#dbe9f6",
        lakes=True,
        resolution="l",
        grid=5,
    )
    basemap.drawcoastlines(
        color="#4d4d4d",
        linewidth=0.8,
    )
    basemap.drawcountries(
        color="#4d4d4d",
        linewidth=0.8,
    )
    basemap.drawstates(
        color="#777777",
        linewidth=0.6,
    )
    basemap.drawparallels(
        circles=range(floor(minimum_latitude), ceil(maximum_latitude) + 1, 2),
        labels=[True, False, False, False],
        color="#c7c7c7",
        linewidth=0.4,
        fontsize=8,
    )
    basemap.drawmeridians(
        meridians=range(floor(minimum_longitude), ceil(maximum_longitude) + 1, 2),
        labels=[False, False, False, True],
        color="#c7c7c7",
        linewidth=0.4,
        fontsize=8,
    )

    location_lookup = {
        row["store"]: basemap(row["longitude"], row["latitude"])
        for row in selected.iter_rows(named=True)
    }
    customer_points = [
        point for store_id, point in location_lookup.items() if store_id not in depots
    ]
    if customer_points:
        axes.scatter(
            x=[x_value for x_value, _ in customer_points],
            y=[y_value for _, y_value in customer_points],
            s=28,
            color="steelblue",
            edgecolor="k",
            linewidth=0.5,
            alpha=0.65,
            label="Stores",
            zorder=4,
        )
    if depots:
        axes.scatter(
            x=[location_lookup[store_id][0] for store_id in depots],
            y=[location_lookup[store_id][1] for store_id in depots],
            s=260,
            marker="*",
            color="#d62728",
            edgecolor="k",
            linewidth=0.8,
            label="Depots" if len(depots) > 1 else "Depot",
            zorder=7,
        )

    colors = sns.color_palette(palette="colorblind")
    for route_number, route in enumerate(normalized_routes, start=1):
        closed_route = _close_route(route)
        if len(closed_route) < 2:
            continue
        color = colors[(route_number - 1) % len(colors)]
        route_x = [location_lookup[store_id][0] for store_id in closed_route]
        route_y = [location_lookup[store_id][1] for store_id in closed_route]
        axes.plot(
            route_x,
            route_y,
            color=color,
            linewidth=2.0,
            alpha=0.9,
            zorder=5,
        )
        start_x, start_y = route_x[0], route_y[0]
        label_x, label_y = max(
            zip(route_x, route_y),
            key=lambda point: (point[0] - start_x) ** 2 + (point[1] - start_y) ** 2,
        )
        axes.annotate(
            text=str(route_number),
            xy=(label_x, label_y),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=8,
            color="k",
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": "white",
                "edgecolor": color,
                "linewidth": 1.2,
            },
            zorder=8,
        )

    axes.legend(
        bbox_to_anchor=(1.01, 1.0),
        loc="upper left",
        borderaxespad=0.0,
        frameon=True,
    )
    return figure, axes
