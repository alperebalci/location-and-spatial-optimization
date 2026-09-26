# Facility Layout Optimization with the Quadratic Assignment Problem

A verification-first facility-layout benchmark for the
`location-and-spatial-optimization` umbrella repository.

The project models an **equal-area discrete facility layout** as a classical
Quadratic Assignment Problem (QAP): each department must be assigned to exactly
one candidate bay, and each bay receives exactly one department.

## Decision problem

Let

- `f[i,j]` be directed material flow from department `i` to department `j`;
- `d[k,l]` be travel distance between facility locations `k` and `l`;
- `p[i]` be the location assigned to department `i`.

The objective is

```text
minimize sum_i sum_j f[i,j] * d[p[i], p[j]]
```

This directly minimizes flow-distance material-handling effort.

The flow matrix may be asymmetric because material movement does not need to be
balanced in both directions. The location-distance matrix is symmetric.

## Industrial fixture

The executable fixture contains eight departments:

```text
Receiving
Machining
Welding
Painting
Assembly
Inspection
Packaging
Shipping
```

and eight equal-area bays arranged on a 4 × 2 grid.

Manhattan distance represents aisle travel between bay centroids. Directed
unit-load movements represent one planning period of interdepartmental material
flow.

The data are synthetic and are not presented as measurements from a named plant.

## Methods

### Greedy flow-centrality baseline

Departments with the highest total inbound + outbound flow are assigned first to
locations with the lowest aggregate distance to all other bays.

This is a transparent baseline, not an optimization certificate.

### Pairwise-swap descent

Starting from a feasible permutation, every pair of department assignments is
tested. The best improving swap is accepted until a 2-exchange local optimum is
reached.

### Multi-start 2-exchange

The local search is started from:

- the greedy baseline;
- reproducible random permutations.

The best local optimum is retained.

### Exact enumeration

For small layouts, every department-to-location permutation is enumerated. The
default eight-department fixture contains

```text
8! = 40,320
```

assignments, so exact verification is practical.

Enumeration is disabled by default beyond nine departments because factorial
growth makes it unsuitable as a scalable facility-layout solver.

## Independent audit

Every reported solution is checked independently for:

- one-to-one department/location assignment;
- complete use of all locations;
- objective recomputation from the original flow and distance matrices.

The benchmark reports the heuristic gap against the exact small-instance
optimum.

## Run

From this project directory:

```bash
python facility_layout_qap.py
python facility_layout_qap.py --restarts 100 --seed 42
```

Tests:

```bash
python -m unittest discover -s tests -v
```

## Scope boundary

This project is the classical **equal-area QAP facility-layout problem**.

It does **not** claim to solve the unequal-area facility layout problem, where
department dimensions, aspect ratios, non-overlap geometry, aisle design,
orientation, and continuous coordinates become explicit decision variables.
Those problems require a different formulation such as MILP/MINLP, slicing-tree
methods, or specialized metaheuristics.

Likewise, the exact enumerator is a correctness oracle for small fixtures rather
than an industrial-scale QAP algorithm.

Natural future extensions are:

- unequal-area facility layout;
- fixed/dead-zone locations;
- adjacency or separation constraints;
- stochastic material flows;
- multi-floor layouts;
- QAPLIB benchmark ingestion;
- tabu search, simulated annealing, and robust metaheuristic comparison.
