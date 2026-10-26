"""
SafeRoute AI - Baseline Edge Risk Computation & Live Environmental Risk Scoring
Course Outcome Mapping:
    - CO5 (Machine Learning Techniques): Calibrated XGBoost inference on live environmental states
    - CO2 (Risk-Aware Search Graph Integration): Static baseline edge risk computation on OSMnx road graph

Description:
    Computes a BASELINE static risk score (0–1) for each road edge in an OpenStreetMap graph
    by synthesizing two signals:
    1. Historical accident spatial density from grid-cell aggregations of data/clean.parquet.
    2. Supervised XGBoost model output evaluated under typical baseline conditions.
    
    Also exposes `predict_risk(conditions: dict) -> float` for live environmental risk prediction.
"""

from functools import lru_cache
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import joblib
import networkx as nx
import osmnx as ox

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "clean.parquet"
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "xgb.joblib"
GRAPH_PATH = MODELS_DIR / "graph.graphml"

# Spatial resolution matching prepare_data.py
GRID_RESOLUTION = 0.01  # ~1.1 km cells

# Typical baseline conditions (Clear sunny afternoon, normal urban traffic)
TYPICAL_CONDITIONS = {
    "hour": 14,
    "day_of_week": 2,       # Tuesday
    "is_weekend": 0,
    "is_night": 0,
    "temperature": 72.0,    # Fahrenheit
    "humidity": 50.0,       # %
    "visibility": 10.0,     # miles
    "wind_speed": 5.0,      # mph
    "precipitation": 0.0,   # inches
    "weather_condition": "Clear",
    "junction": 0,
    "traffic_signal": 0,
}

# In-memory cached singletons for sub-second API latency
_MODEL_CACHE = None
_GRAPH_CACHE = None
_GRID_DENSITY_CACHE = None


def get_model():
    """Loads and caches the calibrated XGBoost model pipeline."""
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Trained model not found at {MODEL_PATH}. Run ml/train_xgb.py first.")
        _MODEL_CACHE = joblib.load(MODEL_PATH)
    return _MODEL_CACHE


def predict_risk(conditions: Dict[str, Any]) -> float:
    """
    Exposes live condition risk scoring (CO5).
    Given environmental & traffic conditions dictionary, returns the calibrated
    probability [0.0, 1.0] of a high-severity accident.

    Parameters
    ----------
    conditions : dict
        Keys may include:
        - hour (0-23)
        - day_of_week (0-6)
        - is_weekend (0 or 1)
        - is_night (0 or 1)
        - temperature (deg F)
        - humidity (%)
        - visibility (miles)
        - wind_speed (mph)
        - precipitation (in/hr)
        - weather_condition ('Clear'|'Rain'|'Fog'|'Snow'|'Other')
        - junction (0 or 1)
        - traffic_signal (0 or 1)

    Returns
    -------
    float
        Calibrated accident risk score strictly bounded between 0.0 and 1.0.
    """
    model = get_model()

    # Merge input with typical defaults
    merged = dict(TYPICAL_CONDITIONS)
    for k, v in conditions.items():
        if v is not None:
            merged[k] = v

    # Auto-derive temporal flags if not explicitly provided
    hour = int(merged.get("hour", 14))
    if "is_night" not in conditions or conditions["is_night"] is None:
        merged["is_night"] = 1 if (hour < 6 or hour >= 20) else 0

    if "day_of_week" in conditions and conditions["day_of_week"] is not None:
        dow = int(conditions["day_of_week"])
        if "is_weekend" not in conditions or conditions["is_weekend"] is None:
            merged["is_weekend"] = 1 if dow in (5, 6) else 0

    # Ensure required feature order
    feature_columns = [
        "hour", "day_of_week", "is_weekend", "is_night",
        "temperature", "humidity", "visibility", "wind_speed", "precipitation",
        "weather_condition", "junction", "traffic_signal"
    ]

    row = {col: merged.get(col, TYPICAL_CONDITIONS.get(col, 0)) for col in feature_columns}
    df_input = pd.DataFrame([row])

    # Predict calibrated probability of high_severity (class 1)
    probs = model.predict_proba(df_input)
    risk = float(probs[0, 1])

    # Bound safely to [0.0, 1.0]
    return float(np.clip(risk, 0.0, 1.0))


def compute_grid_density(parquet_path: Path = DATA_PATH) -> Dict[str, float]:
    """
    Computes normalized historical accident spatial density (0.0 to 1.0)
    for each spatial grid cell in the target region.
    Uses log-scaling to prevent extreme outliers from crushing the distribution.
    """
    global _GRID_DENSITY_CACHE
    if _GRID_DENSITY_CACHE is not None:
        return _GRID_DENSITY_CACHE

    if not parquet_path.exists():
        raise FileNotFoundError(f"Historical accident data missing at {parquet_path}")

    df = pd.read_parquet(parquet_path, columns=["grid_cell_id", "high_severity"])
    
    # Severity-weighted accident counts (high severity has 2x weight)
    weighted_counts = df["grid_cell_id"].value_counts() + df[df["high_severity"] == 1]["grid_cell_id"].value_counts()
    weighted_counts = weighted_counts.dropna()

    max_count = weighted_counts.max()
    if max_count == 0 or np.isnan(max_count):
        max_count = 1.0

    # Log-transform density: log(1 + count) / log(1 + max_count)
    log_max = np.log1p(max_count)
    density_map = {
        cell_id: float(np.log1p(count) / log_max)
        for cell_id, count in weighted_counts.items()
    }

    _GRID_DENSITY_CACHE = density_map
    return _GRID_DENSITY_CACHE


def lat_lng_to_grid_id(lat: float, lng: float) -> str:
    """Discretizes coordinates into grid cell identifier."""
    grid_lat = int(lat / GRID_RESOLUTION)
    grid_lng = int(lng / GRID_RESOLUTION)
    return f"cell_{grid_lat}_{grid_lng}"


def compute_edge_baseline_risks(
    G: nx.MultiDiGraph,
    density_map: Optional[Dict[str, float]] = None,
    alpha: float = 0.60
) -> nx.MultiDiGraph:
    """
    Given an OSMnx MultiDiGraph, computes a BASELINE static risk score (0-1) for each edge
    from nearby historical accidents (grid-cell density) and XGBoost model output at
    typical baseline conditions, saving them as edge attributes.

    Parameters
    ----------
    G : nx.MultiDiGraph
        The road network graph.
    density_map : dict, optional
        Grid-cell density lookup table.
    alpha : float, default 0.60
        Weight between historical spatial density (alpha) and model baseline output (1 - alpha).

    Returns
    -------
    G : nx.MultiDiGraph
        Enriched graph with 'risk_score', 'base_risk', and 'accident_density' attributes on every edge.
    """
    if density_map is None:
        density_map = compute_grid_density()

    # Precompute model baseline output under typical conditions
    typical_risk_normal = predict_risk(TYPICAL_CONDITIONS)

    typical_with_junction = dict(TYPICAL_CONDITIONS)
    typical_with_junction["junction"] = 1
    typical_risk_junction = predict_risk(typical_with_junction)

    typical_with_signal = dict(TYPICAL_CONDITIONS)
    typical_with_signal["traffic_signal"] = 1
    typical_risk_signal = predict_risk(typical_with_signal)

    # Process all edges
    edge_count = 0
    for u, v, k, data in G.edges(keys=True, data=True):
        edge_count += 1
        # Extract edge midpoint
        if "geometry" in data and data["geometry"] is not None:
            geom = data["geometry"]
            mid_lat = geom.centroid.y
            mid_lng = geom.centroid.x
        else:
            u_node = G.nodes[u]
            v_node = G.nodes[v]
            mid_lat = (u_node.get("y", 0.0) + v_node.get("y", 0.0)) / 2.0
            mid_lng = (u_node.get("x", 0.0) + v_node.get("x", 0.0)) / 2.0

        # 1. Historical spatial grid density
        cell_id = lat_lng_to_grid_id(mid_lat, mid_lng)
        hist_density = density_map.get(cell_id, 0.0)

        # 2. Road infrastructure features from OSM edge data
        highway_attr = str(data.get("highway", "")).lower()
        has_signal = 1 if "signal" in highway_attr or data.get("traffic_signals", False) else 0
        is_junction = 1 if (G.degree(u) > 2 or G.degree(v) > 2) else 0

        if has_signal:
            model_base = typical_risk_signal
        elif is_junction:
            model_base = typical_risk_junction
        else:
            model_base = typical_risk_normal

        # 3. Combine historical accident density + model baseline
        # Baseline static risk score normalized strictly in [0.0, 1.0]
        combined_risk = alpha * hist_density + (1.0 - alpha) * model_base
        combined_risk = float(np.clip(combined_risk, 0.0, 1.0))

        # Assign as edge attributes
        data["risk_score"] = round(combined_risk, 4)
        data["base_risk"] = round(combined_risk, 4)
        data["accident_density"] = round(hist_density, 4)
        data["mid_lat"] = round(mid_lat, 6)
        data["mid_lng"] = round(mid_lng, 6)

    return G


def load_or_build_graph(
    center_point=(30.2672, -97.7431),
    dist: int = 3500,
    force_rebuild: bool = False
) -> nx.MultiDiGraph:
    """
    Loads cached graph from models/graph.graphml. If missing or force_rebuild=True,
    downloads the OSM graph for the target area, enriches every edge with baseline risk,
    and caches it to disk.
    """
    global _GRAPH_CACHE
    if _GRAPH_CACHE is not None and not force_rebuild:
        return _GRAPH_CACHE

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    if GRAPH_PATH.exists() and not force_rebuild:
        print(f"Loading cached road network graph from {GRAPH_PATH}...")
        G = ox.load_graphml(GRAPH_PATH)
    else:
        print(f"Fetching OpenStreetMap road network for center {center_point} (radius={dist}m)...")
        G = ox.graph_from_point(center_point, dist=dist, network_type="drive")
        print(f"Computing baseline static edge risks across {len(G.edges):,} edges...")
        G = compute_edge_baseline_risks(G)
        print(f"Saving enriched road graph to {GRAPH_PATH}...")
        ox.save_graphml(G, GRAPH_PATH)
        # Also save copy as city_graph.graphml for compatibility
        city_graph_path = MODELS_DIR / "city_graph.graphml"
        ox.save_graphml(G, city_graph_path)

    _GRAPH_CACHE = G
    return _GRAPH_CACHE


def evaluate_edge_risks_summary(G: nx.MultiDiGraph) -> Dict[str, Any]:
    """Generates distribution summary of baseline edge risks."""
    risks = [data.get("risk_score", 0.0) for _, _, _, data in G.edges(keys=True, data=True)]
    risks = np.array(risks)
    summary = {
        "total_edges": len(risks),
        "mean_risk": float(round(np.mean(risks), 4)),
        "std_risk": float(round(np.std(risks), 4)),
        "min_risk": float(round(np.min(risks), 4)),
        "max_risk": float(round(np.max(risks), 4)),
        "p25": float(round(np.percentile(risks, 25), 4)),
        "p50_median": float(round(np.percentile(risks, 50), 4)),
        "p75": float(round(np.percentile(risks, 75), 4)),
        "p95": float(round(np.percentile(risks, 95), 4)),
    }
    return summary


if __name__ == "__main__":
    print("=" * 65)
    print("SafeRoute AI — Edge Risk Computation & Live Predictor (CO5, CO2)")
    print("=" * 65)

    # 1. Test live predict_risk under contrasting conditions
    print("\n[1/3] Testing live condition risk scoring:")
    clear_day = predict_risk({
        "weather_condition": "Clear",
        "precipitation": 0.0,
        "visibility": 10.0,
        "hour": 14,
        "temperature": 75.0,
    })
    print(f"   Clear Sunny Day Risk  : {clear_day * 100:.2f}% (calibrated score: {clear_day:.4f})")

    rainy_night = predict_risk({
        "weather_condition": "Rain",
        "precipitation": 0.85,
        "visibility": 2.0,
        "hour": 22,
        "temperature": 45.0,
        "junction": 1,
    })
    print(f"   Stormy Night Junction : {rainy_night * 100:.2f}% (calibrated score: {rainy_night:.4f})")
    print(f"   Relative Risk Increase: {((rainy_night - clear_day) / clear_day) * 100:+.1f}%")

    # 2. Build or load OSM graph and compute edge baseline risks
    print("\n[2/3] Loading / computing baseline edge risks on OSM graph...")
    G = load_or_build_graph()
    summary = evaluate_edge_risks_summary(G)

    print("\n[3/3] Baseline Edge Risk Summary Statistics:")
    print(f"   Total Network Edges   : {summary['total_edges']:,}")
    print(f"   Mean Baseline Risk    : {summary['mean_risk']:.4f}")
    print(f"   Median (P50) Risk     : {summary['p50_median']:.4f}")
    print(f"   95th Percentile Risk  : {summary['p95']:.4f}")
    print(f"   Risk Range [Min, Max] : [{summary['min_risk']:.4f}, {summary['max_risk']:.4f}]")
    print("=" * 65)
