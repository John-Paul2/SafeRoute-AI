"""
Unit Tests for SafeRoute AI Graph Routing & A* Search
Course Outcome: CO2 (Informed and Uninformed Search), CO1 (Agent Decision Model)

Validates:
- Admissible haversine heuristic calculations
- Custom A* search implementation (priority queue, closed set)
- Comparison against uninformed Dijkstra search (A* expands fewer or equal nodes)
- Shortest-distance baseline routing (lambda = 0)
- High-risk zones GeoJSON extraction
"""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from routing.astar import (
    load_cached_graph,
    haversine_distance,
    find_nearest_node,
    astar_search,
    dijkstra_search,
    shortest_distance_search,
    get_top_high_risk_zones,
    find_safe_and_fastest_routes
)


class TestRoutingAStar(unittest.TestCase):
    """Test suite for CO2 Routing & Search Algorithms."""

    @classmethod
    def setUpClass(cls):
        """Loads cached graph once for all tests."""
        cls.G = load_cached_graph()
        # Pick two distinct nodes in central Austin
        nodes = list(cls.G.nodes)
        cls.start_node = nodes[0]
        # Choose a target node sufficiently distant
        cls.target_node = nodes[min(150, len(nodes) - 1)]

    def test_haversine_distance(self):
        """Tests haversine distance calculation on known coordinates."""
        # Austin Capitol (30.2747, -97.7404) to UT Tower (30.2862, -97.7394) ~ 1.28 km
        dist = haversine_distance(30.2747, -97.7404, 30.2862, -97.7394)
        self.assertGreater(dist, 1100.0)
        self.assertLess(dist, 1450.0)

    def test_astar_finds_valid_route(self):
        """Tests that A* successfully finds a path with coordinates and positive distance."""
        route = astar_search(self.G, self.start_node, self.target_node, safety_lambda=1.5)
        self.assertIsNotNone(route)
        self.assertGreater(len(route["coordinates"]), 0)
        self.assertGreater(route["distance_meters"], 0.0)
        self.assertGreater(route["nodes_expanded"], 0)
        self.assertEqual(route["algorithm"], "A*")
        self.assertIn("geojson", route)
        self.assertEqual(route["geojson"]["type"], "Feature")

    def test_dijkstra_finds_valid_route(self):
        """Tests plain Dijkstra uninformed search."""
        route = dijkstra_search(self.G, self.start_node, self.target_node, safety_lambda=1.5)
        self.assertIsNotNone(route)
        self.assertEqual(route["algorithm"], "Dijkstra")
        self.assertGreater(route["nodes_expanded"], 0)

    def test_astar_search_efficiency_vs_dijkstra(self):
        """
        Validates CO2 search efficiency:
        A* with admissible heuristic should expand fewer (or at most equal) nodes than Dijkstra.
        """
        astar_res = astar_search(self.G, self.start_node, self.target_node, safety_lambda=1.5)
        dijkstra_res = dijkstra_search(self.G, self.start_node, self.target_node, safety_lambda=1.5)

        self.assertLessEqual(
            astar_res["nodes_expanded"],
            dijkstra_res["nodes_expanded"],
            f"A* expanded ({astar_res['nodes_expanded']}) should be <= Dijkstra ({dijkstra_res['nodes_expanded']})"
        )

    def test_shortest_distance_baseline(self):
        """Tests baseline shortest-distance pathfinding (lambda = 0)."""
        route = shortest_distance_search(self.G, self.start_node, self.target_node)
        self.assertIsNotNone(route)
        self.assertGreater(route["distance_meters"], 0.0)

    def test_top_high_risk_zones(self):
        """Tests extraction of top accident-prone road segments."""
        data = get_top_high_risk_zones(self.G, limit=10)
        zones = data["high_risk_zones"]
        self.assertLessEqual(len(zones), 10)
        self.assertGreater(len(zones), 0)

        first_zone = zones[0]
        self.assertIn("id", first_zone)
        self.assertIn("lat", first_zone)
        self.assertIn("lng", first_zone)
        self.assertIn("risk_score", first_zone)
        self.assertIn("severity", first_zone)
        self.assertGreater(first_zone["risk_score"], 0.40)

        # Check GeoJSON
        geojson = data["geojson"]
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertEqual(len(geojson["features"]), len(zones))

    def test_find_safe_and_fastest_routes_facade(self):
        """Tests complete facade returning both safe and fastest routes with comparison."""
        origin = (30.2672, -97.7431)
        dest = (30.2780, -97.7350)
        res = find_safe_and_fastest_routes(
            origin=origin,
            destination=dest,
            conditions={"weather": "Rain", "precipitation": 0.5, "hour": 22},
            safety_lambda=2.0
        )

        self.assertIn("safe_route", res)
        self.assertIn("fastest_route", res)
        self.assertIn("comparison", res)
        self.assertIn("high_risk_zones", res)
        self.assertIn("risk_zones_geojson", res)

        comp = res["comparison"]
        self.assertIn("risk_reduction_percent", comp)
        self.assertIn("fastest_risk", comp)
        self.assertIn("safest_risk", comp)


if __name__ == "__main__":
    unittest.main()
