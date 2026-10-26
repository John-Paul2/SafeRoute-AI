"""
Generates the comprehensive evaluation notebook for SafeRoute AI report.
Course Outcomes: CO4, CO5, CO2
"""

import json
from pathlib import Path

cells = []

def add_md(text):
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.strip().split("\n")]
    })

def add_code(code):
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in code.strip().split("\n")]
    })

add_md("""# SafeRoute AI — Machine Learning & Causal Bayesian Network Evaluation
## Micro Project 14: AI-Based Road Accident Prediction (Traffic Management / Insurance)

### Course Outcome (CO) Mapping:
- **CO5 (Machine Learning Techniques):** Supervised XGBoost classifier with class imbalance mitigation (`scale_pos_weight`), probability calibration via Platt Sigmoid (`CalibratedClassifierCV`), evaluation on ROC-AUC, Precision/Recall, Brier score, and feature importance attribution.
- **CO4 (Probabilistic Reasoning):** Causal Directed Acyclic Graph (DAG) with 6 discretized variables, empirical CPT parameter estimation with `BayesianEstimator` (BDeu prior), marginal probabilistic inference, and Pearl causal counterfactual interventions ($do(\\cdot)$ calculus).
- **CO2 (Search & Graph Integration):** Baseline static risk score computation for OpenStreetMap edges combining spatial grid accident density and typical-condition model scoring.
""")

add_code("""import os
import sys
from pathlib import Path

# Adjust workspace root path
ROOT_DIR = Path.cwd().resolve().parent if Path.cwd().name == "notebooks" else Path.cwd().resolve()
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(ROOT_DIR))

# Ensure torch initializes first for Windows OpenMP compatibility
try:
    import torch
except ImportError:
    pass

import pandas as pd
import numpy as np
import joblib
import json
import matplotlib.pyplot as plt
import networkx as nx

print(f"SafeRoute AI Root Directory: {ROOT_DIR}")
""")

add_md("""## 1. Tabular Historical Accident Dataset (CO5)
We load the engineered historical accident dataset from `backend/data/clean.parquet` filtered to the target urban area (Austin, TX).
""")

add_code("""data_path = BACKEND_DIR / "data" / "clean.parquet"
df = pd.read_parquet(data_path)

print(f"Total Cleaned Records: {len(df):,}")
print(f"Features: {list(df.columns)}")

# Class balance check
balance = df["high_severity"].value_counts()
pct = df["high_severity"].value_counts(normalize=True) * 100
print(f"Class 0 (Low Severity 1-2) : {balance[0]:,} ({pct[0]:.2f}%)")
print(f"Class 1 (High Severity 3-4): {balance[1]:,} ({pct[1]:.2f}%)")

df[["hour", "weather_condition", "visibility", "temperature", "precipitation", "junction", "traffic_signal", "high_severity"]].head(10)
""")

add_md("""## 2. Supervised XGBoost Model Evaluation & Calibration (CO5)
The calibrated gradient boosted tree was trained using stratified 80/20 train/test splitting and calibrated using `CalibratedClassifierCV(method='sigmoid', cv=3)`.
""")

add_code("""meta_path = BACKEND_DIR / "models" / "xgb_meta.json"
with open(meta_path) as f:
    meta = json.load(f)

print("=" * 55)
print("XGBOOST CLASSIFIER EVALUATION REPORT")
print("=" * 55)
print(f"Model Name            : {meta['model_name']}")
print(f"Training Samples      : {meta['n_train']:,}")
print(f"Holdout Test Samples  : {meta['n_test']:,}")
print(f"Class Imbalance Weight: {meta['scale_pos_weight']}")
print(f"Optimal Decision Cut  : {meta['optimal_threshold']}")
print("-" * 55)
for k, v in meta["metrics"].items():
    print(f"{k:<22}: {v}")
print("-" * 55)
print(f"Confusion Matrix (at optimal cutoff {meta['optimal_threshold']}):")
cm = meta["confusion_matrix"]
print(f"  TN: {cm['tn']:,} | FP: {cm['fp']:,}")
print(f"  FN: {cm['fn']:,} | TP: {cm['tp']:,}")
print("=" * 55)
""")

add_md("""### Top Feature Importances
Let us inspect the split and gain contributions of the environmental and infrastructural features.
""")

add_code("""top_features = pd.DataFrame(meta["top_features"])
top_features.head(10)
""")

add_md("""### Evaluation Artifact Plots
The 4 generated diagnostic plots from `docs/`:
1. **Confusion Matrix**: True vs Predicted distributions
2. **ROC Curve**: Discrimination performance across all thresholds (AUC = 0.707)
3. **Calibration Reliability Diagram**: Comparison of raw uncalibrated vs Platt-calibrated probabilities
4. **Feature Importances**: Relative contributions to risk prediction
""")

add_code("""from IPython.display import Image, display

docs_dir = ROOT_DIR / "docs"
for plot_file in ["xgb_roc_curve.png", "xgb_calibration_curve.png", "xgb_confusion_matrix.png", "xgb_feature_importance.png"]:
    p = docs_dir / plot_file
    if p.exists():
        print(f"--- {plot_file} ---")
        display(Image(filename=str(p)))
""")

add_md("""## 3. Causal Bayesian Network Modeling (CO4)
We evaluate the 6-variable causal Directed Acyclic Graph (DAG) learned via pgmpy's `BayesianEstimator` with BDeu prior.
""")

add_code("""from backend.bn.infer import get_model, marginals, p_severe, counterfactual_query

bn_model = get_model()
print(f"Bayesian Network Nodes: {list(bn_model.nodes())}")
print(f"Bayesian Network Edges: {list(bn_model.edges())}")
print(f"Model Integrity Verified: {bn_model.check_model()}")

# Display DAG visualization
dag_img = docs_dir / "bn_dag.png"
if dag_img.exists():
    display(Image(filename=str(dag_img)))
""")

add_md("""### Learned Conditional Probability Table (CPT) for Target Severity
The CPT for `Severity` conditioned on `RoadSurface`, `TrafficDensity`, and `Visibility`:
""")

add_code("""cpd_severity = bn_model.get_cpds("Severity")
print(cpd_severity)
""")

add_md("""## 4. Probabilistic Inference & Pearl Causal Interventions (CO4)
### A. Unconditional Prior Marginals
""")

add_code("""priors = marginals()
for var in ["Weather", "TimeOfDay", "TrafficDensity", "Visibility", "RoadSurface", "Severity"]:
    print(f"{var:<15}: {priors[var]}")
""")

add_md("""### B. Conditional Evidence Query — Hazardous Weather Scenario
Observing **Weather = Rain**, **TimeOfDay = Night**, **TrafficDensity = High**:
""")

add_code("""haz_ev = {"Weather": "Rain", "TimeOfDay": "Night", "TrafficDensity": "High"}
haz_marginals = marginals(haz_ev)
p_severe_haz = p_severe(haz_ev)

print(f"Given Evidence: {haz_ev}")
print(f"Inferred Visibility Distribution : {haz_marginals['Visibility']}")
print(f"Inferred RoadSurface Distribution: {haz_marginals['RoadSurface']}")
print(f"Posterior P(Severity = High)     : {p_severe_haz * 100:.2f}% (Prior: {priors['Severity']['High'] * 100:.2f}%)")
""")

add_md("""### C. Pearl Causal Counterfactual / Intervention Query ($do(\\cdot)$)
We query: *"What if RoadSurface were actively mitigated and forced Dry through municipal drainage/de-icing?"*
$$P(\\text{Severity} \\mid do(\\text{RoadSurface} = \\text{Dry}), \\text{Weather} = \\text{Rain}, \\text{TimeOfDay} = \\text{Night})$$
""")

add_code("""intervention_res = counterfactual_query(
    intervention={"RoadSurface": "Dry"},
    evidence={"Weather": "Rain", "TimeOfDay": "Night"}
)

print(f"Pre-Intervention Observed Risk : {intervention_res['baseline_p_severe'] * 100:.2f}%")
print(f"Post-Intervention Causal Risk  : {intervention_res['interventional_p_severe'] * 100:.2f}%")
print(f"Causal Risk Reduction          : {intervention_res['risk_reduction_pct']:.2f}%")
print(f"Interventional Distribution    : {intervention_res['distribution']}")
""")

add_md("""## 5. Road Network Static Baseline Risk Integration (CO2)
We inspect the OpenStreetMap road network graph (`backend/models/graph.graphml`) where every edge has been pre-computed with static baseline accident risk.
""")

add_code("""from backend.ml.edge_risk import load_or_build_graph, evaluate_edge_risks_summary

G = load_or_build_graph()
summary = evaluate_edge_risks_summary(G)

print("=" * 55)
print("ROAD NETWORK BASELINE RISK METRICS")
print("=" * 55)
for k, v in summary.items():
    print(f"{k:<22}: {v}")
print("=" * 55)
""")

add_md("""## 6. Conclusion and Viva Takeaways
1. **CO5 (Machine Learning):** Successfully tackled 9.8:1 severe accident class imbalance using `scale_pos_weight` and calibrated probabilities via Platt scaling to produce reliable continuous risk estimates with Brier score 0.0786 and ROC-AUC 0.7073.
2. **CO4 (Probabilistic Reasoning):** Causal DAG structure encodes causal relationships between weather, temporal factors, surface mechanisms, and crash severity. Supports bidirectional belief updating and Pearl level-2 causal interventions ($do(\\cdot)$ queries).
3. **CO2 (Search Preparation):** Synthesized spatial accident density with baseline model inference to annotate 9,074 road edges with baseline risk scores [0.128, 0.728] for risk-aware A* pathfinding.
""")

nb = {
    "cells": cells,
    "metadata": {
        "language_info": {
            "name": "python",
            "version": "3.11.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 5
}

out_path = Path(__file__).resolve().parent / "01_ml_and_bn_evaluation.ipynb"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2)

print(f"Successfully generated notebook at: {out_path} ({len(cells)} cells)")
