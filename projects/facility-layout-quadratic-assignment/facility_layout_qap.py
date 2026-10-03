from __future__ import annotations

import argparse
import itertools
import json
import math
import random
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class QAPInstance:
    departments: tuple[str, ...]
    locations: tuple[str, ...]
    flow: tuple[tuple[float, ...], ...]
    distance: tuple[tuple[float, ...], ...]
    coordinates: tuple[tuple[float, float], ...] | None = None

    def validate(self) -> None:
        n = len(self.departments)
        if n < 2:
            raise ValueError("QAP needs at least two departments")
        if len(self.locations) != n:
            raise ValueError("departments and locations must have equal cardinality")
        if len(set(self.departments)) != n or len(set(self.locations)) != n:
            raise ValueError("department and location names must be unique")
        if len(self.flow) != n or any(len(row) != n for row in self.flow):
            raise ValueError("flow matrix must be square and match department count")
        if len(self.distance) != n or any(len(row) != n for row in self.distance):
            raise ValueError("distance matrix must be square and match location count")
        if any(value < 0 for row in self.flow for value in row):
            raise ValueError("flow values must be non-negative")
        if any(value < 0 for row in self.distance for value in row):
            raise ValueError("distance values must be non-negative")
        for i in range(n):
            if abs(self.distance[i][i]) > 1e-12:
                raise ValueError("distance diagonal must be zero")
            for j in range(n):
                if abs(self.distance[i][j] - self.distance[j][i]) > 1e-12:
                    raise ValueError("distance matrix must be symmetric")
        if self.coordinates is not None and len(self.coordinates) != n:
            raise ValueError("coordinate count must match location count")


@dataclass(frozen=True)
class LayoutSolution:
    assignment: tuple[int, ...]
    objective: float
    method: str
    evaluated_assignments: int


def manhattan_distance_matrix(
    coordinates: Sequence[tuple[float, float]],
) -> tuple[tuple[float, ...], ...]:
    points = tuple((float(x), float(y)) for x, y in coordinates)
    return tuple(
        tuple(abs(x1 - x2) + abs(y1 - y2) for x2, y2 in points)
        for x1, y1 in points
    )


def _validate_assignment(instance: QAPInstance, assignment: Sequence[int]) -> tuple[int, ...]:
    instance.validate()
    n = len(instance.departments)
    assignment_tuple = tuple(int(value) for value in assignment)
    if len(assignment_tuple) != n:
        raise ValueError("assignment length must equal department count")
    if set(assignment_tuple) != set(range(n)):
        raise ValueError("assignment must be a permutation of all location indices")
    return assignment_tuple


def qap_objective(instance: QAPInstance, assignment: Sequence[int]) -> float:
    mapping = _validate_assignment(instance, assignment)
    total = 0.0
    n = len(mapping)
    for i in range(n):
        li = mapping[i]
        for j in range(n):
            total += instance.flow[i][j] * instance.distance[li][mapping[j]]
    return float(total)


def audit_solution(instance: QAPInstance, solution: LayoutSolution) -> dict[str, float | bool]:
    mapping = _validate_assignment(instance, solution.assignment)
    recomputed = 0.0
    for department_from, location_from in enumerate(mapping):
        for department_to, location_to in enumerate(mapping):
            recomputed += (
                instance.flow[department_from][department_to]
                * instance.distance[location_from][location_to]
            )
    error = abs(float(recomputed) - float(solution.objective))
    return {
        "valid_permutation": True,
        "recomputed_objective": float(recomputed),
        "reported_objective": float(solution.objective),
        "objective_error": float(error),
        "objective_matches": bool(error <= 1e-9),
    }


def greedy_flow_centrality_assignment(instance: QAPInstance) -> tuple[int, ...]:
    instance.validate()
    n = len(instance.departments)
    flow_intensity = [
        sum(instance.flow[i]) + sum(instance.flow[j][i] for j in range(n))
        for i in range(n)
    ]
    distance_centrality = [sum(instance.distance[k]) for k in range(n)]

    departments = sorted(range(n), key=lambda i: (-flow_intensity[i], i))
    locations = sorted(range(n), key=lambda k: (distance_centrality[k], k))

    assignment = [-1] * n
    for department, location in zip(departments, locations):
        assignment[department] = location
    return tuple(assignment)


def pairwise_swap_descent(
    instance: QAPInstance,
    start: Sequence[int],
) -> LayoutSolution:
    current = list(_validate_assignment(instance, start))
    current_cost = qap_objective(instance, current)
    evaluated = 1
    n = len(current)

    while True:
        best_cost = current_cost
        best_swap: tuple[int, int] | None = None
        for i in range(n - 1):
            for j in range(i + 1, n):
                candidate = current.copy()
                candidate[i], candidate[j] = candidate[j], candidate[i]
                cost = qap_objective(instance, candidate)
                evaluated += 1
                if cost < best_cost - 1e-12:
                    best_cost = cost
                    best_swap = (i, j)

        if best_swap is None:
            break

        i, j = best_swap
        current[i], current[j] = current[j], current[i]
        current_cost = best_cost

    return LayoutSolution(
        assignment=tuple(current),
        objective=float(current_cost),
        method="pairwise_swap_descent",
        evaluated_assignments=evaluated,
    )


def multistart_local_search(
    instance: QAPInstance,
    *,
    restarts: int = 50,
    seed: int = 42,
) -> LayoutSolution:
    if restarts <= 0:
        raise ValueError("restarts must be positive")
    instance.validate()
    n = len(instance.departments)
    rng = random.Random(seed)

    starts = [greedy_flow_centrality_assignment(instance)]
    for _ in range(restarts - 1):
        candidate = list(range(n))
        rng.shuffle(candidate)
        starts.append(tuple(candidate))

    best: LayoutSolution | None = None
    total_evaluated = 0
    for start in starts:
        local = pairwise_swap_descent(instance, start)
        total_evaluated += local.evaluated_assignments
        if best is None or local.objective < best.objective - 1e-12:
            best = local

    if best is None:
        raise RuntimeError("local search produced no solution")
    return LayoutSolution(
        assignment=best.assignment,
        objective=best.objective,
        method=f"multistart_2exchange_{restarts}",
        evaluated_assignments=total_evaluated,
    )


def simulated_annealing(
    instance: QAPInstance,
    *,
    start: Sequence[int] | None = None,
    iterations: int = 5000,
    seed: int = 42,
    initial_temperature: float | None = None,
    cooling_rate: float = 0.995,
) -> LayoutSolution:
    """Solve the QAP approximately with 2-swap simulated annealing."""
    instance.validate()
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    if not 0.0 < cooling_rate < 1.0:
        raise ValueError("cooling_rate must be between 0 and 1")

    if start is None:
        current = list(greedy_flow_centrality_assignment(instance))
    else:
        current = list(_validate_assignment(instance, start))

    current_cost = qap_objective(instance, current)
    best = current.copy()
    best_cost = current_cost

    if initial_temperature is None:
        temperature = max(1.0, 0.25 * current_cost)
    else:
        temperature = float(initial_temperature)
        if temperature <= 0.0:
            raise ValueError("initial_temperature must be positive")

    rng = random.Random(seed)
    n = len(current)
    evaluated = 1

    for _ in range(iterations):
        i, j = rng.sample(range(n), 2)
        candidate = current.copy()
        candidate[i], candidate[j] = candidate[j], candidate[i]
        candidate_cost = qap_objective(instance, candidate)
        evaluated += 1

        delta = candidate_cost - current_cost
        if delta <= 0.0 or rng.random() < math.exp(-delta / temperature):
            current = candidate
            current_cost = candidate_cost
            if current_cost < best_cost - 1e-12:
                best = current.copy()
                best_cost = current_cost

        temperature = max(temperature * cooling_rate, 1e-12)

    return LayoutSolution(
        assignment=tuple(best),
        objective=float(best_cost),
        method=f"simulated_annealing_{iterations}",
        evaluated_assignments=evaluated,
    )


def exact_enumeration(
    instance: QAPInstance,
    *,
    max_departments: int = 9,
) -> LayoutSolution:
    instance.validate()
    n = len(instance.departments)
    if n > max_departments:
        raise ValueError(
            f"exact enumeration disabled for n={n}; "
            f"max_departments={max_departments}"
        )

    best_assignment: tuple[int, ...] | None = None
    best_cost = math.inf
    evaluated = 0

    for assignment in itertools.permutations(range(n)):
        cost = qap_objective(instance, assignment)
        evaluated += 1
        if cost < best_cost - 1e-12:
            best_cost = cost
            best_assignment = tuple(assignment)

    if best_assignment is None:
        raise RuntimeError("exact enumeration produced no solution")
    return LayoutSolution(
        assignment=best_assignment,
        objective=float(best_cost),
        method="exact_enumeration",
        evaluated_assignments=evaluated,
    )


def default_facility_layout_instance() -> QAPInstance:
    departments = (
        "Receiving",
        "Machining",
        "Welding",
        "Painting",
        "Assembly",
        "Inspection",
        "Packaging",
        "Shipping",
    )
    locations = tuple(f"B{i + 1}" for i in range(8))
    coordinates = (
        (0.0, 1.0),
        (1.0, 1.0),
        (2.0, 1.0),
        (3.0, 1.0),
        (0.0, 0.0),
        (1.0, 0.0),
        (2.0, 0.0),
        (3.0, 0.0),
    )

    # Directed unit-load movements per planning period.
    flow = (
        (0, 90, 25, 5, 5, 0, 0, 0),
        (8, 0, 75, 10, 35, 5, 0, 0),
        (0, 5, 0, 80, 30, 5, 0, 0),
        (0, 0, 3, 0, 95, 12, 0, 0),
        (0, 8, 4, 6, 0, 85, 25, 0),
        (0, 0, 0, 4, 12, 0, 88, 0),
        (0, 0, 0, 0, 4, 5, 0, 100),
        (12, 0, 0, 0, 0, 0, 3, 0),
    )

    instance = QAPInstance(
        departments=departments,
        locations=locations,
        flow=tuple(tuple(float(value) for value in row) for row in flow),
        distance=manhattan_distance_matrix(coordinates),
        coordinates=coordinates,
    )
    instance.validate()
    return instance


def layout_rows(instance: QAPInstance, solution: LayoutSolution) -> list[dict[str, object]]:
    mapping = _validate_assignment(instance, solution.assignment)
    rows: list[dict[str, object]] = []
    for department_index, location_index in enumerate(mapping):
        row: dict[str, object] = {
            "department": instance.departments[department_index],
            "location": instance.locations[location_index],
        }
        if instance.coordinates is not None:
            x, y = instance.coordinates[location_index]
            row["x"] = x
            row["y"] = y
        rows.append(row)
    return rows


def grid_layout(instance: QAPInstance, solution: LayoutSolution) -> list[list[str]]:
    if instance.coordinates is None:
        raise ValueError("grid layout requires coordinates")
    mapping = _validate_assignment(instance, solution.assignment)
    reverse = {location: department for department, location in enumerate(mapping)}
    xs = sorted({x for x, _ in instance.coordinates})
    ys = sorted({y for _, y in instance.coordinates}, reverse=True)
    location_by_coordinate = {
        coordinate: index for index, coordinate in enumerate(instance.coordinates)
    }

    grid: list[list[str]] = []
    for y in ys:
        row: list[str] = []
        for x in xs:
            location = location_by_coordinate.get((x, y))
            if location is None:
                row.append("-")
            else:
                department = reverse[location]
                row.append(instance.departments[department])
        grid.append(row)
    return grid


def benchmark_demo(
    *,
    restarts: int = 50,
    seed: int = 42,
    sa_iterations: int = 5000,
) -> dict[str, object]:
    instance = default_facility_layout_instance()

    greedy_assignment = greedy_flow_centrality_assignment(instance)
    greedy = LayoutSolution(
        assignment=greedy_assignment,
        objective=qap_objective(instance, greedy_assignment),
        method="greedy_flow_centrality",
        evaluated_assignments=1,
    )
    heuristic = multistart_local_search(
        instance,
        restarts=restarts,
        seed=seed,
    )
    annealing = simulated_annealing(
        instance,
        start=greedy_assignment,
        iterations=sa_iterations,
        seed=seed,
    )
    exact = exact_enumeration(instance)

    for solution in (greedy, heuristic, annealing, exact):
        audit = audit_solution(instance, solution)
        if not audit["objective_matches"]:
            raise RuntimeError(f"objective audit failed for {solution.method}")

    return {
        "problem": {
            "departments": len(instance.departments),
            "locations": len(instance.locations),
            "assignment_space": math.factorial(len(instance.departments)),
            "distance": "Manhattan distance on a 4x2 equal-area bay grid",
            "flow": "directed unit-load movements per planning period",
        },
        "methods": [
            {
                "method": greedy.method,
                "objective": greedy.objective,
                "gap_to_exact_pct": 100.0 * (greedy.objective / exact.objective - 1.0),
                "evaluated_assignments": greedy.evaluated_assignments,
            },
            {
                "method": heuristic.method,
                "objective": heuristic.objective,
                "gap_to_exact_pct": 100.0 * (heuristic.objective / exact.objective - 1.0),
                "evaluated_assignments": heuristic.evaluated_assignments,
            },
            {
                "method": annealing.method,
                "objective": annealing.objective,
                "gap_to_exact_pct": 100.0 * (annealing.objective / exact.objective - 1.0),
                "evaluated_assignments": annealing.evaluated_assignments,
            },
            {
                "method": exact.method,
                "objective": exact.objective,
                "gap_to_exact_pct": 0.0,
                "evaluated_assignments": exact.evaluated_assignments,
            },
        ],
        "exact_layout": layout_rows(instance, exact),
        "exact_grid": grid_layout(instance, exact),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--restarts", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sa-iterations", type=int, default=5000)
    args = parser.parse_args()
    print(
        json.dumps(
            benchmark_demo(
                restarts=args.restarts,
                seed=args.seed,
                sa_iterations=args.sa_iterations,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
