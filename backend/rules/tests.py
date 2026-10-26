"""
Unit Tests for SafeRoute AI Expert Rule Engine
Course Outcome: CO3 (Knowledge Representation and Reasoning)

Validates:
- Every production rule (R01 through R12) fires under its designated conditions
- Dynamic probability percentage formatting in advisory messages
- Triggering facts capture for explainability traces
- Actuarial underwriting tier classification and premium multipliers (R13 through R16)
"""

import unittest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rules.engine import KnowledgeEngine, Fact, evaluate_rules, RuleDefinition


class TestRuleEngine(unittest.TestCase):
    """Test suite for CO3 Expert Rule Engine."""

    def setUp(self):
        self.engine = KnowledgeEngine()

    def test_r01_hydroplaning_fires(self):
        """R01: Hydroplaning rule fires on Wet/Rain surface with high risk."""
        res = evaluate_rules(
            conditions={"weather": "Rain", "road_surface": "Wet", "precipitation": 0.3},
            risk_probability=0.72
        )
        fired_ids = [a["id"] for a in res["advisories"]]
        self.assertIn("R01_HYDROPLANING", fired_ids)
        r01 = next(a for a in res["advisories"] if a["id"] == "R01_HYDROPLANING")
        self.assertEqual(r01["severity"], "critical")
        self.assertIn("72.0%", r01["message"])
        self.assertIn("road_surface", r01["facts"])
        self.assertEqual(r01["facts"]["road_surface"], "Wet")

    def test_r02_dense_fog_fires(self):
        """R02: Dense fog advisory fires when visibility < 2.0 mi."""
        res = evaluate_rules(
            conditions={"weather": "Fog", "visibility": 1.2},
            risk_probability=0.45
        )
        fired_ids = [a["id"] for a in res["advisories"]]
        self.assertIn("R02_DENSE_FOG", fired_ids)
        r02 = next(a for a in res["advisories"] if a["id"] == "R02_DENSE_FOG")
        self.assertEqual(r02["severity"], "warning")
        self.assertIn("visibility", r02["facts"])
        self.assertEqual(r02["facts"]["visibility"], 1.2)
        self.assertIn("45.0%", r02["message"])

    def test_r03_black_ice_fires(self):
        """R03: Black ice advisory fires on Icy surface."""
        res = evaluate_rules(
            conditions={"road_surface": "Icy", "weather": "Snow"},
            risk_probability=0.55
        )
        fired_ids = [a["id"] for a in res["advisories"]]
        self.assertIn("R03_BLACK_ICE", fired_ids)
        r03 = next(a for a in res["advisories"] if a["id"] == "R03_BLACK_ICE")
        self.assertEqual(r03["severity"], "critical")
        self.assertIn("55.0%", r03["message"])

    def test_r04_lane_closure_diversion_fires(self):
        """R04: Lane closure and heavy vehicle diversion fires under extreme traffic + high risk."""
        res = evaluate_rules(
            conditions={"traffic_density": 85},
            risk_probability=0.78
        )
        fired_ids = [a["id"] for a in res["advisories"]]
        self.assertIn("R04_LANE_CLOSURE_DIVERSION", fired_ids)
        r04 = next(a for a in res["advisories"] if a["id"] == "R04_LANE_CLOSURE_DIVERSION")
        self.assertEqual(r04["severity"], "critical")
        self.assertIn("78.0%", r04["message"])
        self.assertEqual(r04["facts"]["traffic_density"], 85)

    def test_r05_night_hazard_fires(self):
        """R05: Night hazard fires during night hours with reduced visibility or risk."""
        res = evaluate_rules(
            conditions={"time_of_day": "Night", "visibility": 4.0},
            risk_probability=0.42
        )
        fired_ids = [a["id"] for a in res["advisories"]]
        self.assertIn("R05_NIGHT_HAZARD", fired_ids)
        r05 = next(a for a in res["advisories"] if a["id"] == "R05_NIGHT_HAZARD")
        self.assertEqual(r05["severity"], "warning")
        self.assertEqual(r05["facts"]["time_of_day"], "Night")

    def test_r06_high_congestion_gridlock_fires(self):
        """R06: High congestion warning fires under high density and risk."""
        res = evaluate_rules(
            conditions={"traffic_density": 90},
            risk_probability=0.48
        )
        fired_ids = [a["id"] for a in res["advisories"]]
        self.assertIn("R06_HIGH_CONGESTION_GRIDLOCK", fired_ids)
        r06 = next(a for a in res["advisories"] if a["id"] == "R06_HIGH_CONGESTION_GRIDLOCK")
        self.assertEqual(r06["severity"], "warning")

    def test_r07_severe_storm_fires(self):
        """R07: Torrential precipitation / storm alert fires."""
        res = evaluate_rules(
            conditions={"weather": "Rain", "precipitation": 0.85},
            risk_probability=0.68
        )
        fired_ids = [a["id"] for a in res["advisories"]]
        self.assertIn("R07_SEVERE_STORM", fired_ids)
        r07 = next(a for a in res["advisories"] if a["id"] == "R07_SEVERE_STORM")
        self.assertEqual(r07["severity"], "critical")
        self.assertIn("0.85", r07["message"])

    def test_r08_long_route_fatigue_fires(self):
        """R08: Long route fatigue advisory fires on routes >= 15 km at night."""
        res = evaluate_rules(
            conditions={"time_of_day": "Night"},
            route_stats={"route_length_km": 28.5},
            risk_probability=0.35
        )
        fired_ids = [a["id"] for a in res["advisories"]]
        self.assertIn("R08_LONG_ROUTE_FATIGUE", fired_ids)
        r08 = next(a for a in res["advisories"] if a["id"] == "R08_LONG_ROUTE_FATIGUE")
        self.assertEqual(r08["severity"], "info")
        self.assertIn("28.5", r08["message"])

    def test_r09_compound_hazard_fires(self):
        """R09: Compound multi-hazard triggers when weather, night, and traffic coincide."""
        res = evaluate_rules(
            conditions={
                "weather": "Rain",
                "time_of_day": "Night",
                "traffic_density": 75,
                "precipitation": 0.4
            },
            risk_probability=0.65
        )
        fired_ids = [a["id"] for a in res["advisories"]]
        self.assertIn("R09_COMPOUND_HAZARD", fired_ids)
        r09 = next(a for a in res["advisories"] if a["id"] == "R09_COMPOUND_HAZARD")
        self.assertEqual(r09["severity"], "critical")
        self.assertIn("65.0%", r09["message"])

    def test_r10_dusk_glare_fires(self):
        """R10: Dusk twilight caution fires."""
        res = evaluate_rules(
            conditions={"time_of_day": "Dusk"},
            risk_probability=0.36
        )
        fired_ids = [a["id"] for a in res["advisories"]]
        self.assertIn("R10_DUSK_GLARE_CAUTION", fired_ids)
        r10 = next(a for a in res["advisories"] if a["id"] == "R10_DUSK_GLARE_CAUTION")
        self.assertEqual(r10["severity"], "info")

    def test_r11_urban_pedestrian_conflict_fires(self):
        """R11: Urban intersection conflict point fires."""
        res = evaluate_rules(
            conditions={"visibility": 3.0, "traffic_density": 70},
            risk_probability=0.52
        )
        fired_ids = [a["id"] for a in res["advisories"]]
        self.assertIn("R11_URBAN_PEDESTRIAN_CONFLICT", fired_ids)

    def test_r12_optimal_conditions_fires(self):
        """R12: Optimal conditions advisory fires on clear daytime with low risk."""
        res = evaluate_rules(
            conditions={"weather": "Clear", "road_surface": "Dry", "time_of_day": "Day"},
            risk_probability=0.15
        )
        fired_ids = [a["id"] for a in res["advisories"]]
        self.assertIn("R12_OPTIMAL_CONDITIONS", fired_ids)
        r12 = next(a for a in res["advisories"] if a["id"] == "R12_OPTIMAL_CONDITIONS")
        self.assertEqual(r12["severity"], "info")

    def test_underwriting_tier_a_low(self):
        """Underwriting Tier A (Low Risk, multiplier 0.95x)."""
        res = evaluate_rules(
            conditions={"road_surface": "Dry"},
            risk_probability=0.18
        )
        tier = res["underwriting_tier"]
        self.assertEqual(tier["tier"], "Tier A")
        self.assertEqual(tier["premium_multiplier"], 0.95)
        self.assertEqual(res["premium_multiplier"], 0.95)

    def test_underwriting_tier_b_standard(self):
        """Underwriting Tier B (Standard Risk, multiplier 1.15x)."""
        res = evaluate_rules(
            conditions={},
            risk_probability=0.35
        )
        tier = res["underwriting_tier"]
        self.assertEqual(tier["tier"], "Tier B")
        self.assertEqual(tier["premium_multiplier"], 1.15)

    def test_underwriting_tier_c_high(self):
        """Underwriting Tier C (High Risk, multiplier 1.45x)."""
        res = evaluate_rules(
            conditions={},
            risk_probability=0.58
        )
        tier = res["underwriting_tier"]
        self.assertEqual(tier["tier"], "Tier C")
        self.assertEqual(tier["premium_multiplier"], 1.45)

    def test_underwriting_tier_d_refer(self):
        """Underwriting Tier D (Refer to underwriter, multiplier 2.10x)."""
        res = evaluate_rules(
            conditions={},
            risk_probability=0.82
        )
        tier = res["underwriting_tier"]
        self.assertEqual(tier["tier"], "Tier D")
        self.assertEqual(tier["premium_multiplier"], 2.10)
        self.assertIn("Refer", tier["name"])


if __name__ == "__main__":
    unittest.main()
