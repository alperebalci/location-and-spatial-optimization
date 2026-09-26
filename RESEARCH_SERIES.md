# Location, Allocation, and Spatial Optimization Research Series

This file maps repositories that decide where to locate resources and how to allocate demand or capacity across space. It is an index only: the repositories remain independent because their objectives, assignment structures, capacities, and solution methods differ.

## Emergency and public-service location

- `fire-station-location-covering-optimization` — set-covering style location model with response-time, redundancy, and budget requirements.
- `fire-station-location-optimization-pulp` — explicit demand-to-station assignment model minimizing weighted response time under budget and station-count limits.

These two fire-station repositories should remain separate because one is primarily a covering model and the other is a location-allocation model with explicit assignments.

## General facility location and allocation

- `capacitated-facility-location-tabu-search-julia` — capacitated facility location solved with tabu search rather than an exact MILP workflow.
- `multi-site-resource-allocation-optimization` — allocation across multiple sites.
- `scarce-water-resource-allocation-optimization` — resource allocation under scarcity rather than physical facility-opening decisions.

## Internal facility layout

- `facility-layout-quadratic-assignment` — equal-area department-to-bay assignment using the classical QAP objective `flow × distance`, with exact small-instance enumeration and multi-start 2-exchange search.

Facility layout is kept distinct from facility location. The former assumes the plant/site exists and optimizes internal departmental placement; the latter chooses which external sites or facilities to open.
## Districting and service-area design

- `school-districting-optimization-gurobi` — educational cohort-to-school assignment MILP.
- `school-redistricting-optimization-gurobi` — richer districting toolkit with continuity, utilization, sibling, and socioeconomic-balance terms.
- `urban-parking-recommendation-milp` — spatial allocation/recommendation with an urban-service context.

## Network-design bridge

- `supply-chain-network-design-pyomo` — facility-opening and multi-echelon flow decisions.
- `gurobi-supply-chain-network-optimization` — candidate-DC location plus network-flow optimization.
- `bike-share-network-optimizer` — network/location decisions for shared mobility.

## Portfolio rule

Repositories should remain separate when the mathematical core changes between covering, p-median/location-allocation, capacitated facility location, internal facility layout/QAP, districting, network design, or resource allocation. Geographic similarity is not sufficient evidence for consolidation.
