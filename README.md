# Location and Spatial Optimization

<!-- portfolio-umbrella:start -->
## Portfolio role

This repository is the primary umbrella repository for this Jors Academy research area. Related projects have been consolidated under `projects/` so the methods, implementations, experiments, and case studies can be maintained and explored from one place.

### Included projects

- [`capacitated-facility-location-tabu-search-julia`](projects/capacitated-facility-location-tabu-search-julia/)
- [`fire-station-location-optimization-pulp`](projects/fire-station-location-optimization-pulp/)
- [`facility-layout-quadratic-assignment`](projects/facility-layout-quadratic-assignment/) — equal-area internal facility layout with exact QAP verification and multi-start 2-exchange search
- [`school-districting-optimization-gurobi`](projects/school-districting-optimization-gurobi/)
- [`school-redistricting-optimization-gurobi`](projects/school-redistricting-optimization-gurobi/)
- [`urban-parking-recommendation-milp`](projects/urban-parking-recommendation-milp/)
- [`wind-farm-layout-optimization`](projects/wind-farm-layout-optimization/)
- [`wind-farm-layout-optimizer`](projects/wind-farm-layout-optimizer/)

Consolidated source projects keep their own files and a `SOURCE_REPOSITORY.md` provenance record. Native extensions may instead live directly under `projects/` with repository-level CI and documentation.
<!-- portfolio-umbrella:end -->

This umbrella repository covers external facility location, spatial allocation, districting, network layout, and internal facility-layout problems. The root executable remains a compact fire-station location model; additional research implementations live under `projects/`.

The example is intentionally fictional. All place names, costs, and travel times were created for educational and non-commercial research use.

## Facility layout / QAP extension

The repository now includes [`facility-layout-quadratic-assignment`](projects/facility-layout-quadratic-assignment/), which addresses a different spatial decision layer from ordinary facility location.

```text
Facility location:
Which sites should be opened?

Facility layout / QAP:
Given a fixed set of internal bays,
which department should occupy each bay?
```

For departments `i,j` and locations `k,l`, the QAP minimizes

```text
sum_i sum_j flow[i,j] * distance[p[i], p[j]]
```

where `p[i]` is the location assigned to department `i`.

The project includes:

- an 8-department, 8-bay synthetic manufacturing layout;
- directed material-flow data;
- Manhattan aisle distance on a 4 × 2 equal-area bay grid;
- flow-centrality greedy baseline;
- deterministic pairwise-swap descent;
- reproducible multi-start 2-exchange local search;
- exact enumeration of all `8! = 40,320` assignments;
- independent permutation and objective audits;
- heuristic optimality-gap reporting against the exact small-instance oracle.

The implementation is deliberately **equal-area and discrete**. Unequal-area facility layout, department dimensions, non-overlap geometry, aspect ratios, orientations, and continuous coordinates are outside the QAP benchmark and require a different formulation.

Run:

```bash
cd projects/facility-layout-quadratic-assignment
python facility_layout_qap.py
python -m unittest discover -s tests -v
```

## Root reference problem: fire-station location


A regional planner must decide which candidate cities should receive fire stations. A station can cover a city only if its travel time is no greater than the response-time threshold.

The model includes the following requirements:

- Minimize total station construction cost.
- Ensure every city is covered within the maximum response time.
- Require double coverage for selected high-priority cities.
- Respect a total construction budget.

The decision variable is binary:

```text
x_j = 1 if a fire station is constructed at candidate location j
      0 otherwise
```

The core covering constraint is:

```text
sum(x_j for j in N_i) >= r_i
```

where `N_i` is the set of candidate stations capable of reaching city `i` within the response-time threshold and `r_i` is the required number of covering stations.

## Root fire-station data

The project uses eight fictional cities and a symmetric travel-time matrix measured in minutes. Two cities are treated as high-priority locations and therefore require coverage from at least two selected stations.

The data are embedded directly in the Python script so that the model can be reproduced without external files.

## Root fire-station requirements

- Python 3.10 or newer
- PuLP
- CBC solver, normally bundled with standard PuLP installations

Install the dependency with:

```bash
pip install -r requirements.txt
```

## Run the root fire-station example

```bash
python fire_station_location.py
```

The script reports:

- solver status,
- selected fire station locations,
- total construction cost,
- budget limit,
- coverage verification for every city.

## Root model notes

This model is a set-covering style facility-location formulation with additional redundancy and budget constraints. It is designed as a compact operations research example rather than as a production emergency-services planning system.

For the current data set, the model has a feasible solution and minimizes construction cost while satisfying all coverage requirements. A more advanced formulation could introduce explicit demand assignment, station capacities, workload balancing, stochastic response times, or scenario-based resilience constraints.

## License

This project is available for personal, academic, educational, and non-commercial research use only. Commercial use is not permitted without prior written authorization. See `LICENSE.md` for the full terms.
