"""
SafeRoute AI REST API Tests
Course Outcome Mapping:
    - CO1 (Intelligent Agent Models): Agent health and metadata verification
    - CO2 (Informed Search): /api/route/ risk-weighted A* endpoint validation
    - CO3 (Knowledge Representation): /api/rules/ expert rule endpoint validation
    - CO4 (Probabilistic Reasoning) & CO5 (Machine Learning): /api/predict/ risk inference validation
"""

import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


class SafeRouteAPITests(TestCase):
    """Integration test suite covering all SafeRoute AI REST API endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_health_check(self):
        """GET /api/health/ returns status 200 and healthy flag."""
        url = reverse('api-health')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("course_outcomes", data)
        self.assertIn("CO1", data["course_outcomes"])
        self.assertIn("CO2", data["course_outcomes"])
        self.assertIn("CO3", data["course_outcomes"])
        self.assertIn("CO4", data["course_outcomes"])
        self.assertIn("CO5", data["course_outcomes"])

    def test_meta_endpoint(self):
        """GET /api/meta/ returns Austin map bounds and default sliders."""
        url = reverse('api-meta')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["city"], "Austin")
        self.assertEqual(data["state"], "TX")
        self.assertIn("bounds", data)
        self.assertIn("default_sliders", data)
        self.assertIn("supported_weather_conditions", data)

    def test_predict_endpoint_success(self):
        """POST /api/predict/ returns calibrated XGBoost risk and Bayesian marginals."""
        url = reverse('api-predict')
        payload = {
            "weather": "Rain",
            "precipitation": 0.5,
            "visibility": 3.0,
            "traffic_density": 70,
            "hour": 21,
            "temperature": 55.0
        }
        response = self.client.post(url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Prompt specified fields
        self.assertIn("xgb_risk", data)
        self.assertIn("bn_marginals", data)
        self.assertIn("p_severe", data)
        self.assertIn("evidence_used", data)

        self.assertGreaterEqual(data["xgb_risk"], 0.0)
        self.assertLessEqual(data["xgb_risk"], 1.0)
        self.assertGreaterEqual(data["p_severe"], 0.0)
        self.assertLessEqual(data["p_severe"], 1.0)

        # Frontend compatibility fields
        self.assertIn("risk_level", data)
        self.assertIn("bayesian_marginals", data)

    def test_predict_endpoint_validation_error(self):
        """POST /api/predict/ returns 400 on invalid input parameters."""
        url = reverse('api-predict')
        payload = {
            "hour": 35,  # Invalid hour > 23
            "traffic_density": 250  # Invalid density > 100
        }
        response = self.client.post(url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("details", data)

    def test_route_endpoint_success(self):
        """POST /api/route/ returns safe and fastest routes with GeoJSON and comparison."""
        url = reverse('api-route')
        payload = {
            "origin": [30.2672, -97.7431],
            "destination": [30.2780, -97.7350],
            "conditions": {
                "weather": "Rain",
                "precipitation": 0.4,
                "hour": 22
            },
            "safety_lambda": 1.5
        }
        response = self.client.post(url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Prompt specified fields
        self.assertIn("safe_route", data)
        self.assertIn("fastest_route", data)
        self.assertIn("stats", data)
        self.assertIn("risk_zones", data)

        # GeoJSON LineString validation
        safe = data["safe_route"]
        self.assertIn("geojson", safe)
        self.assertEqual(safe["geojson"]["type"], "Feature")
        self.assertEqual(safe["geojson"]["geometry"]["type"], "LineString")

        # Stats validation
        self.assertIn("safe", data["stats"])
        self.assertIn("fastest", data["stats"])
        self.assertGreater(data["stats"]["safe"]["distance_miles"], 0.0)

    def test_route_endpoint_identical_coords_error(self):
        """POST /api/route/ returns 400 when origin and destination are identical."""
        url = reverse('api-route')
        payload = {
            "origin": [30.2672, -97.7431],
            "destination": [30.2672, -97.7431],  # Identical
            "safety_lambda": 1.5
        }
        response = self.client.post(url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn("error", data)

    def test_rules_endpoint_success(self):
        """POST /api/rules/ returns advisories, underwriting tier, and premium multiplier."""
        url = reverse('api-rules')
        payload = {
            "conditions": {
                "weather": "Rain",
                "road_surface": "Wet",
                "precipitation": 0.5,
                "risk_probability": 0.72
            },
            "route_stats": {
                "route_length_km": 18.0
            }
        }
        response = self.client.post(url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Prompt specified fields
        self.assertIn("advisories", data)
        self.assertIn("underwriting_tier", data)
        self.assertIn("premium_multiplier", data)

        self.assertGreater(len(data["advisories"]), 0)
        first_adv = data["advisories"][0]
        self.assertIn("id", first_adv)
        self.assertIn("severity", first_adv)
        self.assertIn("message", first_adv)
        self.assertIn("facts", first_adv)

        tier = data["underwriting_tier"]
        self.assertIn("tier", tier)
        self.assertIn("premium_multiplier", tier)
        self.assertGreaterEqual(data["premium_multiplier"], 0.95)
