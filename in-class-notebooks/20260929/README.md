# OM 522 Clarke–Wright Savings Demo

This project sets up a capacitated vehicle routing instance for building the
Clarke–Wright savings method in class. It reuses the 439 store locations and
the road-distance table from the [TSP demo](../TSP/README.md) and adds
simulated demand and one hub store per state.

## Run the demo

```bash
pixi install
pixi run demo
```

Run the checks with:

```bash
pixi run check
pixi run test
```

`clarke_wright.py` loads the instance, maps it, and demonstrates the helper
functions in `routing_utils.py`. The cells for the savings method itself are
left empty for class. Change `selected_states` in the notebook to build a
different instance (e.g., `["GA", "AL"]`). With more than one state selected,
every selected hub is a depot.

## Data

`store_locations.parquet` and `road_distances.parquet` are copies of the TSP
demo files and are described in its README. The distance table is symmetric,
which the savings formula and the TSP helper both assume.

`generate_routing_data.py` (`pixi run data`) writes the two added files, and
rerunning it reproduces them exactly.

| File | Contents |
| --- | --- |
| `store_demand.parquet` | `store` and `demand_pallets`, one row for each of the 439 stores |
| `state_hubs.parquet` | `state`, `hub_store`, and `hub_city`, one row for each of the 10 states |

Demand is simulated because the source files carry none. Each store orders a
whole number of pallets drawn uniformly from 1 to 6 with seed 522. The notebook
uses a truck capacity of 26 pallets, the load of a standard 53-foot trailer.
Treat the demand as a teaching assumption rather than observed data.

Each state's hub is a store in its largest metro area (Birmingham, Little Rock,
Atlanta, Louisville, New Orleans, Jackson, Charlotte, Greenville, and
Nashville). Florida is the one exception, because Miami sits at the southern
tip of the state, so its hub is Winter Haven, between Tampa and Orlando. When a
metro area contains several stores, the hub is the one with the smallest total
road distance to the other stores in its state.
