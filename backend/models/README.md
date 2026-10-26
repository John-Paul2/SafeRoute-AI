# Pre-trained & Cached Artifacts (CO2, CO4, CO5)

Per AGENTS.md Rule 3:
"Pre-train and cache everything (models/*.joblib, bn.pkl, graph.graphml). API calls must respond in <1.5s."

Artifacts stored here:
- `xgboost_accident_risk.joblib` (CO5 - Calibrated XGBoost risk classifier)
- `scaler_preprocessor.joblib` (CO5 - Feature encoders and scalers)
- `bayesian_network.joblib` or `bn.pkl` (CO4 - Learned CPTs & DAG for causal reasoning)
- `city_graph.graphml` (CO2 - OSMnx road network graph for pathfinding)
