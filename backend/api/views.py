"""
SafeRoute AI REST API Views
Course Outcome Mapping:
    - CO1 (Intelligent Agent Models): Agent health, telemetry aggregation, meta configuration
    - CO2 (Informed Search): Risk-weighted A* vs Dijkstra route calculation (POST /api/route/)
    - CO3 (Knowledge Representation): Forward-chaining expert rule evaluation (POST /api/rules/)
    - CO4 (Probabilistic Reasoning): Bayesian Network marginal and causal inference
    - CO5 (Machine Learning Techniques): Calibrated XGBoost accident risk prediction (POST /api/predict/)
"""

from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import networkx as nx

from .serializers import (
    PredictRequestSerializer,
    RouteRequestSerializer,
    RulesRequestSerializer
)

# Core AI & Search modules
from ml.edge_risk import predict_risk, get_model
from bn.infer import marginals, p_severe, normalize_evidence, get_model as get_bn_model
from routing.astar import find_safe_and_fastest_routes, load_cached_graph
from rules.engine import evaluate_rules, get_engine


class HealthCheckView(APIView):
    """
    Health check endpoint (GET /api/health/)
    Reports server status, model readiness, and CO capability mapping.
    """
    def get(self, request):
        models_status = {}
        try:
            get_model()
            models_status["xgboost"] = "loaded"
        except Exception as e:
            models_status["xgboost"] = f"error: {str(e)}"

        try:
            get_bn_model()
            models_status["bayesian_network"] = "loaded"
        except Exception as e:
            models_status["bayesian_network"] = f"error: {str(e)}"

        try:
            load_cached_graph()
            models_status["osm_graph"] = "loaded"
        except Exception as e:
            models_status["osm_graph"] = f"error: {str(e)}"

        try:
            get_engine()
            models_status["rule_engine"] = "loaded"
        except Exception as e:
            models_status["rule_engine"] = f"error: {str(e)}"

        return Response({
            "status": "healthy",
            "project": "SafeRoute AI - Micro Project 14",
            "models_status": models_status,
            "course_outcomes": {
                "CO1": "Goal-Based Utility Agent (PEAS Architecture)",
                "CO2": "Risk-Weighted A* Search & Dijkstra Baseline",
                "CO3": "Forward-Chaining Expert Rule Engine & Underwriting",
                "CO4": "Bayesian Network Probabilistic Inference (pgmpy)",
                "CO5": "Calibrated XGBoost Accident Risk Classifier"
            },
            "timestamp": datetime.utcnow().isoformat()
        }, status=status.HTTP_200_OK)


# Seeded 3 saved demo scenarios for evaluators & viva presentation
SEEDED_DEMO_SCENARIOS = [
    {
        "id": "demo-clear",
        "name": "Scenario 1: Optimal Daylight",
        "badge": "Sunny Afternoon",
        "description": "Dry surface, 10 mi visibility, free-flowing traffic. Minimal risk, nominal route with Tier A baseline.",
        "conditions": {
            "precipitation": 0.0,
            "visibility": 10.0,
            "traffic_density": 25.0,
            "hour": 14,
            "weather_condition": "Clear",
            "safety_lambda": 1.0,
            "temperature": 78.0,
            "humidity": 42.0,
            "wind_speed": 5.0,
        },
    },
    {
        "id": "demo-rain",
        "name": "Scenario 2: Heavy Rainstorm",
        "badge": "Severe Downpour",
        "description": "0.85 in/hr precipitation, 3.5 mi visibility, 65% traffic. Hydroplaning rule fires; A* detours around I-35 hazard.",
        "conditions": {
            "precipitation": 0.85,
            "visibility": 3.5,
            "traffic_density": 65.0,
            "hour": 17,
            "weather_condition": "Rain",
            "safety_lambda": 2.5,
            "temperature": 64.0,
            "humidity": 92.0,
            "wind_speed": 16.0,
        },
    },
    {
        "id": "demo-fog-night",
        "name": "Scenario 3: Dense Fog at Midnight",
        "badge": "Zero-Visibility Night",
        "description": "0.8 mi visibility, nighttime 23:00, 80% congestion. Bayesian net predicts elevated hazard; Tier D underwriting surcharge.",
        "conditions": {
            "precipitation": 0.20,
            "visibility": 0.8,
            "traffic_density": 80.0,
            "hour": 23,
            "weather_condition": "Fog",
            "safety_lambda": 3.8,
            "temperature": 52.0,
            "humidity": 98.0,
            "wind_speed": 4.0,
        },
    },
]


class ScenariosView(APIView):
    """
    Seeded demo scenarios endpoint (GET /api/scenarios/)
    Returns 3 saved pre-configured demo scenarios for one-click testing.
    """
    def get(self, request):
        return Response({"scenarios": SEEDED_DEMO_SCENARIOS}, status=status.HTTP_200_OK)


class MetaView(APIView):
    """
    Metadata endpoint (GET /api/meta/)
    Provides target city bounds (Austin, TX), default slider values, and categorical states.
    """
    def get(self, request):
        meta_data = {
            "city": "Austin",
            "state": "TX",
            "map_center": [30.2672, -97.7431],
            "default_zoom": 13,
            "bounds": {
                "south": 30.15,
                "west": -97.90,
                "north": 30.40,
                "east": -97.60
            },
            "default_sliders": {
                "temperature": 72.0,
                "visibility": 10.0,
                "precipitation": 0.0,
                "humidity": 50.0,
                "wind_speed": 5.0,
                "hour": 14,
                "day_of_week": 2,
                "weather_condition": "Clear",
                "traffic_density": 35.0,
                "safety_lambda": 1.5
            },
            "supported_weather_conditions": [
                "Clear", "Rain", "Fog", "Snow", "Other"
            ],
            "demo_scenarios": SEEDED_DEMO_SCENARIOS
        }
        return Response(meta_data, status=status.HTTP_200_OK)


class PredictView(APIView):
    """
    Predictive risk endpoint (POST /api/predict/)
    Evaluates supervised XGBoost risk (CO5) and exact Bayesian Network marginals (CO4).
    """
    def post(self, request):
        serializer = PredictRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error": "Validation failed",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        conditions = serializer.validated_data

        try:
            # 1. CO5 Supervised XGBoost baseline risk score
            xgb_risk = predict_risk(conditions)

            # 2. CO4 Probabilistic Bayesian Network Inference
            evidence_used = normalize_evidence(conditions)
            bn_marginals = marginals(evidence_used)
            p_sev = p_severe(evidence_used)

            # Qualitative risk level designation
            if xgb_risk < 0.28:
                risk_level = "Low"
            elif xgb_risk < 0.50:
                risk_level = "Moderate"
            elif xgb_risk < 0.70:
                risk_level = "High"
            else:
                risk_level = "Critical"

            # Approximate local feature impact weights
            feature_contributions = {
                "precipitation": round(float(conditions.get("precipitation", 0.0)) * 0.40, 3),
                "visibility": round(max(0.0, (10.0 - float(conditions.get("visibility", 10.0))) * 0.04), 3),
                "traffic_density": round(float(conditions.get("traffic_density", 35.0)) / 100.0 * 0.30, 3),
                "is_night": 0.15 if int(conditions.get("hour", 14)) in (21, 22, 23, 0, 1, 2, 3, 4, 5) else 0.0
            }

            # Format bayesian marginals with lower_case keys expected by React components
            formatted_marginals = {
                "weather": bn_marginals.get("weather", bn_marginals.get("Weather", {})),
                "time_of_day": bn_marginals.get("time_of_day", bn_marginals.get("TimeOfDay", {})),
                "traffic_density": bn_marginals.get("traffic_density", bn_marginals.get("TrafficDensity", {})),
                "road_surface": bn_marginals.get("road_surface", bn_marginals.get("RoadSurface", {})),
                "visibility": bn_marginals.get("visibility", bn_marginals.get("Visibility", {})),
                "accident_risk": bn_marginals.get("accident_risk", bn_marginals.get("Severity", {})),
                **bn_marginals
            }

            return Response({
                # User prompt specification fields:
                "xgb_risk": round(xgb_risk, 4),
                "bn_marginals": formatted_marginals,
                "p_severe": round(p_sev, 4),
                "evidence_used": evidence_used,
                # Frontend client compatibility fields:
                "xgboost_risk": round(xgb_risk, 4),
                "risk_percentage": round(xgb_risk * 100.0, 1),
                "risk_level": risk_level,
                "bayesian_marginals": formatted_marginals,
                "feature_contributions": feature_contributions
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": f"Prediction computation failed: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RouteView(APIView):
    """
    Route pathfinding endpoint (POST /api/route/)
    Executes risk-weighted A* search and compares against fastest route baseline.
    """
    def post(self, request):
        serializer = RouteRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error": "Validation failed",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        origin = tuple(data["origin"])
        destination = tuple(data["destination"])
        conditions = data.get("conditions", {})
        safety_lambda = float(data.get("safety_lambda", 1.5))

        try:
            routes_data = find_safe_and_fastest_routes(
                origin=origin,
                destination=destination,
                conditions=conditions,
                safety_lambda=safety_lambda
            )

            safe_route = routes_data["safe_route"]
            fastest_route = routes_data["fastest_route"]
            comparison = routes_data["comparison"]
            high_risk_zones = routes_data["high_risk_zones"]
            risk_zones_geojson = routes_data["risk_zones_geojson"]

            return Response({
                # User prompt specification:
                "safe_route": safe_route,
                "fastest_route": fastest_route,
                "stats": {
                    "safe": {
                        "distance_miles": safe_route["distance_miles"],
                        "duration_minutes": safe_route["duration_minutes"],
                        "total_risk_score": safe_route["total_risk_score"],
                        "nodes_expanded": safe_route["nodes_expanded"]
                    },
                    "fastest": {
                        "distance_miles": fastest_route["distance_miles"],
                        "duration_minutes": fastest_route["duration_minutes"],
                        "total_risk_score": fastest_route["total_risk_score"],
                        "nodes_expanded": fastest_route["nodes_expanded"]
                    }
                },
                "risk_zones": risk_zones_geojson,
                # Frontend client compatibility fields:
                "comparison": comparison,
                "high_risk_zones": high_risk_zones,
                "risk_zones_geojson": risk_zones_geojson
            }, status=status.HTTP_200_OK)

        except nx.NetworkXNoPath as e:
            return Response({
                "error": f"No navigable road path found: {str(e)}"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": f"Pathfinding computation failed: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RulesView(APIView):
    """
    Expert knowledge base evaluation endpoint (POST /api/rules/)
    Evaluates forward-chaining production rules for traffic advisories and underwriting.
    """
    def post(self, request):
        serializer = RulesRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error": "Validation failed",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        conditions = data.get("conditions", {})
        route_stats = data.get("route_stats", {})
        risk_probability = data.get("risk_probability")

        try:
            # If explicit probability not provided, evaluate live risk
            if risk_probability is None:
                if "risk_probability" in conditions:
                    risk_probability = float(conditions["risk_probability"])
                else:
                    risk_probability = predict_risk(conditions)

            eval_results = evaluate_rules(
                conditions=conditions,
                route_stats=route_stats,
                risk_probability=risk_probability
            )

            return Response({
                "advisories": eval_results["advisories"],
                "underwriting_tier": eval_results["underwriting_tier"],
                "premium_multiplier": eval_results["premium_multiplier"],
                "fired_count": eval_results["fired_count"]
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": f"Rule evaluation failed: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
