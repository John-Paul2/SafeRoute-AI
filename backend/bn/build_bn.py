"""
SafeRoute AI - Bayesian Network Construction & CPT Parameter Learning
Course Outcome: CO4 (Probabilistic Reasoning)

Description:
    Constructs a Directed Acyclic Graph (DAG) modeling the causal dependencies
    governing road accident severity under environmental uncertainty.
    
Variables (Discretized):
    - Weather: {Clear, Rain, Fog, Snow}
    - TimeOfDay: {Day, Dusk, Night}
    - TrafficDensity: {Low, Med, High}
    - Visibility: {Good, Poor}
    - RoadSurface: {Dry, Wet, Icy}
    - Severity: {Low, High}

Causal DAG Structure:
    Weather        -> Visibility
    Weather        -> RoadSurface
    TimeOfDay      -> Visibility
    Visibility     -> Severity
    RoadSurface    -> Severity
    TrafficDensity -> Severity

Learning Method:
    Conditional Probability Tables (CPTs) are empirically learned from historical data
    (data/clean.parquet) using BayesianEstimator with BDeu prior (Dirichlet smoothing),
    guaranteeing valid probabilistic distributions without zero-frequency singularities.
    Persisted to models/bn.pkl and plotted to docs/bn_dag.png.
"""

# Ensure torch initializes DLLs first before any OpenMP or graphics runtime on Windows
try:
    import torch
except Exception:
    pass
import os
import sys
import pickle
import time
from pathlib import Path
from typing import Tuple
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from pgmpy.models import BayesianNetwork
from pgmpy.estimators import BayesianEstimator, MaximumLikelihoodEstimator
import joblib

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "clean.parquet"
MODELS_DIR = BASE_DIR / "models"
DOCS_DIR = BASE_DIR.parent / "docs"

# Causal DAG Edges
DAG_EDGES = [
    ("Weather", "Visibility"),
    ("Weather", "RoadSurface"),
    ("TimeOfDay", "Visibility"),
    ("Visibility", "Severity"),
    ("RoadSurface", "Severity"),
    ("TrafficDensity", "Severity")
]


def discretize_accident_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms continuous and categorical tabular features from clean.parquet
    into the 6 discrete variables specified in the causal schema.
    """
    # 1. Weather: {Clear, Rain, Fog, Snow}
    w = df["weather_condition"].fillna("Clear").astype(str).copy()
    w[~w.isin(["Clear", "Rain", "Fog", "Snow"])] = "Clear"

    # 2. TimeOfDay: {Day, Dusk, Night}
    tod = pd.Series("Night", index=df.index)
    tod[(df["hour"] >= 7) & (df["hour"] <= 17)] = "Day"
    tod[(df["hour"] >= 18) & (df["hour"] <= 20)] = "Dusk"

    # 3. TrafficDensity: {Low, Med, High}
    # Derived from temporal congestion patterns: rush hours = High, daytime midday = Med, night = Low
    td = pd.Series("Low", index=df.index)
    is_weekday = (df["is_weekend"] == 0)
    rush_mask = df["hour"].isin([7, 8, 9, 16, 17, 18, 19]) & is_weekday
    midday_mask = df["hour"].isin([10, 11, 12, 13, 14, 15]) | (
        (df["hour"] >= 11) & (df["hour"] <= 18) & (df["is_weekend"] == 1)
    )
    td[midday_mask] = "Med"
    td[rush_mask] = "High"

    # 4. Visibility: {Good, Poor} (Threshold: 5.0 miles)
    vis = pd.Series("Good", index=df.index)
    vis[df["visibility"] < 5.0] = "Poor"

    # 5. RoadSurface: {Dry, Wet, Icy}
    rs = pd.Series("Dry", index=df.index)
    rs[(w == "Rain") | (df["precipitation"] > 0)] = "Wet"
    rs[(w == "Snow") | ((df["temperature"] <= 32) & (df["precipitation"] > 0))] = "Icy"

    # 6. Severity: {Low, High}
    sev = pd.Series("Low", index=df.index)
    sev[df["high_severity"] == 1] = "High"

    discretized = pd.DataFrame({
        "Weather": w,
        "TimeOfDay": tod,
        "TrafficDensity": td,
        "Visibility": vis,
        "RoadSurface": rs,
        "Severity": sev
    })

    return discretized


def plot_dag_structure(save_path: Path):
    """
    Renders an aesthetically structured publication-ready causal DAG plot
    highlighting root, intermediate, and target outcome nodes.
    """
    G = nx.DiGraph()
    G.add_edges_from(DAG_EDGES)

    # Hierarchical coordinates for clean top-down causal flow
    pos = {
        "Weather": (-1.3, 2.0),
        "TimeOfDay": (0.0, 2.0),
        "TrafficDensity": (1.3, 2.0),
        "RoadSurface": (-0.8, 1.0),
        "Visibility": (0.2, 1.0),
        "Severity": (0.0, 0.0),
    }

    fig, ax = plt.subplots(figsize=(9, 7), dpi=300)

    # Color scheme:
    # Exogenous / Root nodes: Teal/Blue
    # Intermediate mechanism nodes: Warm Amber
    # Target / Decision node: Confident Emerald Green
    node_colors = {
        "Weather": "#0284c7",
        "TimeOfDay": "#0284c7",
        "TrafficDensity": "#0284c7",
        "RoadSurface": "#d97706",
        "Visibility": "#d97706",
        "Severity": "#16a34a",
    }
    colors = [node_colors[n] for n in G.nodes()]

    # Draw nodes
    nx.draw_networkx_nodes(
        G, pos,
        node_size=3800,
        node_color=colors,
        edgecolors="#ffffff",
        linewidths=2.5,
        ax=ax
    )

    # Draw edges with smooth curved style
    nx.draw_networkx_edges(
        G, pos,
        arrowstyle="-|>",
        arrowsize=22,
        edge_color="#475569",
        width=2.2,
        connectionstyle="arc3,rad=0.08",
        min_source_margin=25,
        min_target_margin=25,
        ax=ax
    )

    # Draw node labels
    labels = {
        "Weather": "Weather\n{Clear, Rain, Fog, Snow}",
        "TimeOfDay": "TimeOfDay\n{Day, Dusk, Night}",
        "TrafficDensity": "TrafficDensity\n{Low, Med, High}",
        "RoadSurface": "RoadSurface\n{Dry, Wet, Icy}",
        "Visibility": "Visibility\n{Good, Poor}",
        "Severity": "Severity\n{Low, High}",
    }
    nx.draw_networkx_labels(
        G, pos,
        labels=labels,
        font_size=9,
        font_family="sans-serif",
        font_color="#ffffff",
        font_weight="bold",
        ax=ax
    )

    # Title and viva explanation
    ax.set_title("Causal Bayesian Network DAG — Road Accident Severity (CO4)", fontsize=13, fontweight="bold", pad=20)
    plt.figtext(
        0.5, 0.02,
        "Exogenous Factors (Blue)  ->  Environmental Mechanisms (Amber)  ->  Accident Severity (Green)\n"
        "Learned from 96k records via BayesianEstimator (BDeu prior). Supports do(X) causal interventions.",
        ha="center", fontsize=9, color="#64748b"
    )

    ax.axis("off")
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    print(f"   [Saved] Bayesian Network DAG visualization -> {save_path}")


def build_and_train_bn() -> BayesianNetwork:
    """
    Main training function: loads data, discretizes, instantiates DAG,
    learns CPTs with BayesianEstimator (BDeu prior), and saves models.
    """
    print("=" * 65)
    print("SafeRoute AI — Bayesian Network Construction & Learning (CO4)")
    print("=" * 65)

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Parquet dataset missing at {DATA_PATH}. Run prepare_data.py first.")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n[1/4] Discretizing historical accident dataset from {DATA_PATH}...")
    df = pd.read_parquet(DATA_PATH)
    discrete_df = discretize_accident_data(df)
    print(f"   Discretized {len(discrete_df):,} rows into {len(discrete_df.columns)} causal variables:")
    for col in discrete_df.columns:
        counts = dict(discrete_df[col].value_counts())
        print(f"     - {col:<15}: {counts}")

    print(f"\n[2/4] Defining Directed Acyclic Graph (DAG) with {len(DAG_EDGES)} causal edges...")
    model = BayesianNetwork(DAG_EDGES)
    print(f"   Causal dependencies:")
    for src, dst in DAG_EDGES:
        print(f"     {src:<15} ---> {dst}")

    print(f"\n[3/4] Learning Conditional Probability Tables (CPTs) via BayesianEstimator (BDeu prior)...")
    t0 = time.time()
    # BDeu prior with equivalent sample size 10 prevents zero-probability traps for rare events
    model.fit(
        discrete_df,
        estimator=BayesianEstimator,
        prior_type="BDeu",
        equivalent_sample_size=10
    )
    print(f"   Learned CPTs in {time.time() - t0:.2f}s.")
    model.check_model()
    print("   Model structure & CPT validity verified: check_model() passed!")

    # Display learned CPT summaries
    print("\nLearned Target Outcome CPT — P(Severity | RoadSurface, TrafficDensity, Visibility):")
    sev_cpd = model.get_cpds("Severity")
    print(sev_cpd)

    # Persist model
    print(f"\n[4/4] Persisting learned Bayesian Network...")
    pkl_path = MODELS_DIR / "bn.pkl"
    with open(pkl_path, "wb") as f:
        pickle.dump(model, f)
    print(f"   [Saved] Pickle artifact -> {pkl_path}")

    # Also save as joblib for convenience
    joblib_path = MODELS_DIR / "bn.joblib"
    joblib.dump(model, joblib_path)
    print(f"   [Saved] Joblib artifact -> {joblib_path}")

    # Generate DAG visualization plot
    dag_plot_path = DOCS_DIR / "bn_dag.png"
    plot_dag_structure(dag_plot_path)

    print(f"\nBayesian Network build successfully completed!")
    return model


if __name__ == "__main__":
    build_and_train_bn()
