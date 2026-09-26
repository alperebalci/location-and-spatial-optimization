import math
import unittest

from facility_layout_qap import (
    LayoutSolution,
    QAPInstance,
    audit_solution,
    benchmark_demo,
    default_facility_layout_instance,
    exact_enumeration,
    greedy_flow_centrality_assignment,
    manhattan_distance_matrix,
    multistart_local_search,
    qap_objective,
)


class FacilityLayoutQAPTests(unittest.TestCase):
    def test_hand_checkable_three_department_objective(self):
        instance = QAPInstance(
            departments=("A", "B", "C"),
            locations=("L1", "L2", "L3"),
            flow=(
                (0.0, 5.0, 0.0),
                (1.0, 0.0, 4.0),
                (0.0, 2.0, 0.0),
            ),
            distance=(
                (0.0, 1.0, 2.0),
                (1.0, 0.0, 1.0),
                (2.0, 1.0, 0.0),
            ),
        )
        # A->L1, B->L2, C->L3:
        # 5*1 + 1*1 + 4*1 + 2*1 = 12.
        self.assertAlmostEqual(qap_objective(instance, (0, 1, 2)), 12.0)

    def test_exact_enumerator_checks_every_permutation(self):
        instance = QAPInstance(
            departments=("A", "B", "C", "D"),
            locations=("L1", "L2", "L3", "L4"),
            flow=(
                (0.0, 8.0, 1.0, 0.0),
                (2.0, 0.0, 7.0, 1.0),
                (0.0, 1.0, 0.0, 9.0),
                (3.0, 0.0, 1.0, 0.0),
            ),
            distance=manhattan_distance_matrix(
                ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0))
            ),
        )
        result = exact_enumeration(instance)
        self.assertEqual(result.evaluated_assignments, math.factorial(4))
        self.assertTrue(audit_solution(instance, result)["objective_matches"])

    def test_multistart_never_worsens_greedy_start(self):
        instance = default_facility_layout_instance()
        greedy_assignment = greedy_flow_centrality_assignment(instance)
        greedy_cost = qap_objective(instance, greedy_assignment)
        result = multistart_local_search(instance, restarts=8, seed=9)
        self.assertLessEqual(result.objective, greedy_cost + 1e-9)

    def test_invalid_duplicate_location_assignment_is_rejected(self):
        instance = default_facility_layout_instance()
        with self.assertRaises(ValueError):
            qap_objective(instance, (0, 0, 1, 2, 3, 4, 5, 6))

    def test_audit_detects_wrong_reported_objective(self):
        instance = default_facility_layout_instance()
        assignment = tuple(range(8))
        true_cost = qap_objective(instance, assignment)
        fake = LayoutSolution(
            assignment=assignment,
            objective=true_cost + 10.0,
            method="fake",
            evaluated_assignments=1,
        )
        audit = audit_solution(instance, fake)
        self.assertFalse(audit["objective_matches"])
        self.assertAlmostEqual(audit["objective_error"], 10.0)

    def test_demo_exact_solution_and_heuristic_gaps_are_valid(self):
        result = benchmark_demo(restarts=6, seed=5)
        self.assertEqual(result["problem"]["assignment_space"], math.factorial(8))
        methods = {row["method"]: row for row in result["methods"]}
        exact = methods["exact_enumeration"]
        self.assertEqual(exact["gap_to_exact_pct"], 0.0)
        for row in result["methods"]:
            self.assertGreaterEqual(row["gap_to_exact_pct"], -1e-10)


if __name__ == "__main__":
    unittest.main()
