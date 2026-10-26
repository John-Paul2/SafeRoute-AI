# SafeRoute AI: Risk-Aware Routing via Causal Inference and Dynamic Pathfinding

Micro Project 14: AI-Based Road Accident Prediction
Industry Focus: Traffic Management, Insurance
Integrated COs: CO3, CO4, CO5 (also covers CO1, CO2)

## Overview

SafeRoute AI integrates machine learning, probabilistic reasoning, rule-based
knowledge representation, and search algorithms into one transportation analytics
platform. It moves beyond static accident-risk classification to dynamic,
causal-driven pathfinding. A goal-based utility agent processes marginal
probabilities under uncertain conditions and recalculates route graphs, modifying
edge weights using real-time localized risk instead of distance alone.

## Course Outcomes Integration

- **CO1 (Intelligent Agent Models):** The system is a Goal-Based Utility Agent with
  a PEAS profile (Performance, Environment, Actuators, Sensors) that balances travel
  efficiency against accident-risk exposure.
- **CO2 (Uninformed and Informed Search):** Risk-aware A* over a road network, with
  Dijkstra and shortest-distance routing as baselines. Edge cost penalizes base
  distance by localized accident risk. The haversine heuristic stays admissible
  because cost >= length.
- **CO3 (Knowledge Representation):** A knowledge base of facts and forward-chaining
  production rules (Python Experta, or an equivalent plain-Python rule engine) that
  turns probabilistic risk into traffic-management advisories and insurance
  underwriting tiers.
- **CO4 (Probabilistic Reasoning):** A Bayesian Network (DAG) built with pgmpy that
  models causal dependencies between weather, time of day, visibility, road surface,
  traffic density, and accident severity. CPTs are learned from data. Supports
  intervention (what-if) queries.
- **CO5 (Machine Learning Techniques):** A supervised XGBoost classifier trained on
  historical tabular traffic data to output calibrated baseline risk scores.

## Datasets and Data Sourcing

- **Historical Traffic Data (CO5):** Kaggle "US Accidents" dataset (geospatial
  coordinates, weather, temporal features, severity). The dataset covers the US only,
  so the project is scoped to ONE US city/area (configurable constant). The data is
  sampled to at most 300k rows.
- **Geospatial Network Graph (CO2):** OpenStreetMap data fetched with OSMnx for the
  same city/area (about 5-10 km, at most 20k nodes), cached as graphml.

## System Architecture and API Schema (Django / Python Backend)

- `POST /api/predict/`: takes current environmental and traffic conditions. Returns
  the XGBoost risk probability and the Bayesian marginal probabilities for causal
  explainability.
- `POST /api/route/`: takes origin and destination coordinates, conditions, and a
  safety-vs-speed parameter (lambda). Runs the risk-weighted A* algorithm. Returns
  the safe route and the fastest route as GeoJSON, with stats and high-risk zones.
- `POST /api/rules/`: takes conditions and route stats. Evaluates them against the
  rule engine. Returns explicit safety advisories (e.g. "Mandate speed reduction due
  to 78% hydroplaning risk"), an underwriting tier, and a premium multiplier.
- `GET /api/health/` and `GET /api/meta/`: health check, map bounds, default slider
  values.

Edge cost: `cost = length * (1 + LAMBDA * edge_risk * env_multiplier)`
- `edge_risk`: static baseline risk per edge (historical accidents + XGBoost).
- `env_multiplier`: live multiplier from current conditions (BN and XGBoost output).

## Step-by-Step Implementation Roadmap

- **Phase 1: Predictive Modeling:** Clean the accident dataset, engineer geospatial
  and temporal features, train and calibrate the XGBoost classifier, and compute
  per-edge baseline risk.
- **Phase 2: Uncertainty Modeling:** Define the DAG, learn the CPTs with pgmpy, and
  support marginal and intervention queries.
- **Phase 3: Knowledge Base and Rules:** Define facts and rules mapping probability
  thresholds to traffic interventions and underwriting tiers.
- **Phase 4: Agent Search Algorithms:** Load the OSMnx graph, apply risk-weighted
  edge costs, and implement A* (plus Dijkstra and shortest-path baselines).
- **Phase 5: Backend API:** Expose the models through the Django REST endpoints above.
- **Phase 6: Interactive Interface (React):** Build the dashboard with Leaflet,
  control sliders, a Bayesian Network view, rule advisories, and route comparison,
  styled per DESIGN.md.

## Presentation and Interactive Demo Flow

The evaluator interacts with a React dashboard containing a map and environmental
control sliders. Changing variables such as precipitation, visibility, or traffic
density triggers asynchronous calls to the Django backend. The UI then:

1. Updates the Bayesian Network nodes with new probabilities.
2. Shows the rule engine's new traffic mandates and underwriting tier.
3. Redraws the A* route as a green path that detours around the dynamically
   generated high-risk zones, compared against the gray fastest route.

A "Demo mode" button plays a scripted scenario (clear, heavy rain, fog at night).