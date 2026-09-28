"""Generate simulated store demand and one hub store per state.

The store and road-distance tables carry no demand, so this script simulates
one: every store orders a whole number of pallets drawn uniformly from 1 to 6
with a fixed seed. A 53-foot trailer holds 26 standard pallets, which the
notebook uses as the vehicle capacity.

Each state's hub is a store in its largest metro area. Florida is the one
exception: its largest metro (Miami) sits at the southern tip, so the hub is
Winter Haven, between Tampa and Orlando. When a metro contains several stores,
the hub is the one with the smallest total road distance to the other stores in
its state.

Run with ``pixi run data``. The script never modifies the two source tables.
"""

from pathlib import Path

import numpy as np
import polars as pl


DATA_DIR = Path(__file__).parent / "data"
DEMAND_SEED = 522
MIN_PALLETS = 1
MAX_PALLETS = 6

# Cities as recorded in store_locations.parquet. Little Rock and North Little
# Rock form one metro area.
HUB_CITIES = {
    "AL": ["Birmingham"],
    "AR": ["Little Rock", "North Little Rock"],
    "FL": ["Winter Haven"],
    "GA": ["Atlanta"],
    "KY": ["Louisville"],
    "LA": ["New Orleans"],
    "MS": ["Jackson"],
    "NC": ["Charlotte"],
    "SC": ["Greenville"],
    "TN": ["Nashville"],
}


def generate_demand(locations: pl.DataFrame) -> pl.DataFrame:
    """Draw seeded integer pallet demand for every store, in store-ID order."""
    stores = locations.get_column("store").sort()
    rng = np.random.default_rng(seed=DEMAND_SEED)
    pallets = rng.integers(
        low=MIN_PALLETS,
        high=MAX_PALLETS + 1,
        size=stores.len(),
    )
    return pl.DataFrame(
        {
            "store": stores,
            "demand_pallets": pallets,
        }
    ).with_columns(pl.col("demand_pallets").cast(pl.Int64))


def choose_hubs(
    locations: pl.DataFrame,
    road_distances: pl.DataFrame,
) -> pl.DataFrame:
    """Return one hub store per state from the cities in HUB_CITIES."""
    states = locations.select(
        pl.col("store"),
        pl.col("state"),
    )
    within_state_totals = (
        road_distances
        .join(
            other=states.rename({"store": "store1", "state": "state1"}),
            on="store1",
            how="inner",
        )
        .join(
            other=states.rename({"store": "store2", "state": "state2"}),
            on="store2",
            how="inner",
        )
        .filter(pl.col("state1") == pl.col("state2"))
        .group_by("store1")
        .agg(pl.col("distance_miles").sum().alias("within_state_miles"))
        .rename({"store1": "store"})
    )
    hub_cities = pl.DataFrame(
        [
            {"state": state, "city": city}
            for state, cities in HUB_CITIES.items()
            for city in cities
        ]
    )
    candidates = (
        locations
        .join(
            other=hub_cities,
            on=["state", "city"],
            how="inner",
        )
        .join(
            other=within_state_totals,
            on="store",
            how="inner",
        )
    )
    missing = set(HUB_CITIES) - set(candidates.get_column("state").to_list())
    if missing:
        raise ValueError(f"No hub candidate found for: {', '.join(sorted(missing))}")

    return (
        candidates
        .sort(
            by=["state", "within_state_miles", "store"],
        )
        .group_by("state", maintain_order=True)
        .first()
        .select(
            pl.col("state"),
            pl.col("store").alias("hub_store"),
            pl.col("city").alias("hub_city"),
        )
    )


def main() -> None:
    locations = pl.read_parquet(DATA_DIR / "store_locations.parquet")
    road_distances = pl.read_parquet(DATA_DIR / "road_distances.parquet")

    demand = generate_demand(locations)
    hubs = choose_hubs(
        locations=locations,
        road_distances=road_distances,
    )
    if demand.height != locations.height:
        raise ValueError("Demand must cover every store exactly once.")
    if hubs.height != locations.get_column("state").n_unique():
        raise ValueError("Every state must have exactly one hub.")

    demand.write_parquet(DATA_DIR / "store_demand.parquet")
    hubs.write_parquet(DATA_DIR / "state_hubs.parquet")
    print(f"Wrote demand for {demand.height} stores and {hubs.height} state hubs.")
    print(hubs)


if __name__ == "__main__":
    main()
