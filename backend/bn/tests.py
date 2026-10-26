"""
SafeRoute AI - Bayesian Network Unit Tests
Course Outcome: CO4 (Probabilistic Reasoning)

Description:
    Tests causal DAG topology, CPT validity, marginal inference consistency,
    extreme condition behavior, and Pearl causal do-query interventions.
"""

# Ensure torch loads first to avoid Windows DLL clash
try:
    import torch
except Exception:
    pass
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR.parent) not in sys.path:
    sys.path.insert(0, str(BASE_DIR.parent))

try:
    from backend.bn.infer import (
        get_model,
        marginals,
        p_severe,
        counterfactual_query,
        normalize_evidence,
        NODE_STATES
    )
except ImportError:
    from bn.infer import (
        get_model,
        marginals,
        p_severe,
        counterfactual_query,
        normalize_evidence,
        NODE_STATES
    )


class BayesianNetworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Loads cached Bayesian Network model once for test suite."""
        cls.model = get_model()

    def test_dag_structure_and_nodes(self):
        """Verifies all 6 required discrete variables exist in the DAG."""
        expected_nodes = {"Weather", "TimeOfDay", "TrafficDensity", "Visibility", "RoadSurface", "Severity"}
        self.assertEqual(set(self.model.nodes()), expected_nodes)

        # Verify exact 6 causal edges
        expected_edges = {
            ("Weather", "Visibility"),
            ("Weather", "RoadSurface"),
            ("TimeOfDay", "Visibility"),
            ("Visibility", "Severity"),
            ("RoadSurface", "Severity"),
            ("TrafficDensity", "Severity")
        }
        self.assertEqual(set(self.model.edges()), expected_edges)
        self.assertTrue(self.model.check_model())

    def test_unconditional_marginals_sum_to_one(self):
        """Verifies that unconditional marginal probabilities sum to 1.0 across all states."""
        priors = marginals()
        for node, states in NODE_STATES.items():
            self.assertIn(node, priors)
            prob_sum = sum(priors[node].values())
            self.assertAlmostEqual(prob_sum, 1.0, places=3,
                                   msg=f"Marginals for {node} do not sum to 1.0 (got {prob_sum})")

    def test_evidenced_node_is_deterministic(self):
        """Verifies that observing evidence fixes the node probability to 1.0."""
        ev = {"Weather": "Rain", "Visibility": "Poor"}
        res = marginals(ev)

        self.assertEqual(res["Weather"]["Rain"], 1.0)
        self.assertEqual(res["Weather"]["Clear"], 0.0)
        self.assertEqual(res["Visibility"]["Poor"], 1.0)
        self.assertEqual(res["Visibility"]["Good"], 0.0)

    def test_p_severe_bounds(self):
        """Verifies p_severe returns float strictly between 0.0 and 1.0."""
        p_base = p_severe()
        self.assertIsInstance(p_base, float)
        self.assertGreaterEqual(p_base, 0.0)
        self.assertLessEqual(p_base, 1.0)

    def test_causal_counterfactual_query(self):
        """Verifies counterfactual intervention returns expected structure and valid probabilities."""
        res = counterfactual_query(
            intervention={"RoadSurface": "Dry"},
            evidence={"Weather": "Rain", "TimeOfDay": "Night"}
        )
        self.assertIn("baseline_p_severe", res)
        self.assertIn("interventional_p_severe", res)
        self.assertIn("risk_reduction_pct", res)
        self.assertIn("distribution", res)

        self.assertGreaterEqual(res["interventional_p_severe"], 0.0)
        self.assertLessEqual(res["interventional_p_severe"], 1.0)
        dist_sum = sum(res["distribution"].values())
        self.assertAlmostEqual(dist_sum, 1.0, places=3)

    def test_normalize_evidence_tolerance(self):
        """Verifies input normalization handles lowercase keys and numerical slider values."""
        raw = {
            "weather": "rain",
            "hour": 23,
            "visibility": 2.5,
            "traffic_density": 85
        }
        cleaned = normalize_evidence(raw)
        self.assertEqual(cleaned.get("Weather"), "Rain")
        self.assertEqual(cleaned.get("TimeOfDay"), "Night")
        self.assertEqual(cleaned.get("Visibility"), "Poor")
        self.assertEqual(cleaned.get("TrafficDensity"), "High")


if __name__ == "__main__":
    unittest.main()
