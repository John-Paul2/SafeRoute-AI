"""
SafeRoute AI - Bayesian Network Inference & Causal Counterfactual Engine
Course Outcome: CO4 (Probabilistic Reasoning)

Description:
    Provides exact inference and causal intervention capabilities over the learned
    Bayesian Network DAG. Implements:
    1. marginals(evidence: dict) -> dict of all node marginal distributions
    2. p_severe(evidence: dict) -> float (high accident severity probability)
    3. counterfactual_query(intervention: dict, evidence: dict) -> dict
       evaluating Pearl's causal do-calculus interventions (e.g. do(RoadSurface=Dry))
"""

import os
import sys

# On Windows, add torch/lib directory so DLLs (c10.dll, etc.) initialize properly
if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
    try:
        import site
        search_dirs = list(site.getsitepackages()) if hasattr(site, "getsitepackages") else []
        search_dirs.extend(sys.path)
        for sp in search_dirs:
            t_lib = os.path.join(sp, "torch", "lib")
            if os.path.isdir(t_lib):
                os.add_dll_directory(t_lib)
                break
    except Exception:
        pass

# Ensure torch loads first to avoid Windows OpenMP conflict if present
try:
    import torch
except Exception:
    pass
import pickle
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

from pgmpy.models import BayesianNetwork
from pgmpy.inference import VariableElimination, CausalInference

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
BN_PKL_PATH = MODELS_DIR / "bn.pkl"
BN_JOBLIB_PATH = MODELS_DIR / "bn.joblib"

# Discrete Domain Specifications
NODE_STATES = {
    "Weather": ["Clear", "Rain", "Fog", "Snow"],
    "TimeOfDay": ["Day", "Dusk", "Night"],
    "TrafficDensity": ["Low", "Med", "High"],
    "Visibility": ["Good", "Poor"],
    "RoadSurface": ["Dry", "Wet", "Icy"],
    "Severity": ["Low", "High"]
}

# Alias map for tolerant key normalization
KEY_ALIASES = {
    "weather": "Weather",
    "weather_condition": "Weather",
    "timeofday": "TimeOfDay",
    "time_of_day": "TimeOfDay",
    "tod": "TimeOfDay",
    "trafficdensity": "TrafficDensity",
    "traffic_density": "TrafficDensity",
    "visibility": "Visibility",
    "roadsurface": "RoadSurface",
    "road_surface": "RoadSurface",
    "severity": "Severity",
    "high_severity": "Severity"
}

# In-memory singletons for sub-millisecond query performance
_BN_MODEL = None
_VAR_ELIM = None
_CAUSAL_INFER = None


def get_model() -> BayesianNetwork:
    """Loads and caches the BayesianNetwork model."""
    global _BN_MODEL, _VAR_ELIM, _CAUSAL_INFER
    if _BN_MODEL is None:
        if BN_PKL_PATH.exists():
            with open(BN_PKL_PATH, "rb") as f:
                _BN_MODEL = pickle.load(f)
        elif BN_JOBLIB_PATH.exists():
            import joblib
            _BN_MODEL = joblib.load(BN_JOBLIB_PATH)
        else:
            raise FileNotFoundError(
                f"Bayesian Network artifact not found at {BN_PKL_PATH}. Run bn/build_bn.py first."
            )
        _VAR_ELIM = VariableElimination(_BN_MODEL)
        _CAUSAL_INFER = CausalInference(_BN_MODEL)
    return _BN_MODEL


def get_inference_engine() -> VariableElimination:
    """Returns cached VariableElimination inference engine."""
    get_model()
    return _VAR_ELIM


def get_causal_engine() -> CausalInference:
    """Returns cached CausalInference engine."""
    get_model()
    return _CAUSAL_INFER


def normalize_evidence(evidence: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """
    Normalizes evidence dictionary keys and values into valid DAG discrete states.
    Supports both raw sensor values (e.g., visibility=3.5, hour=22) and discrete strings.
    """
    if not evidence:
        return {}

    clean_ev = {}
    for raw_k, raw_v in evidence.items():
        if raw_v is None:
            continue
        k_lower = str(raw_k).lower().strip()
        canonical_k = KEY_ALIASES.get(k_lower, raw_k)

        if canonical_k not in NODE_STATES:
            # Check continuous mapping helpers
            if k_lower in ("hour", "start_time"):
                hour = int(raw_v)
                if 7 <= hour <= 17:
                    clean_ev["TimeOfDay"] = "Day"
                elif 18 <= hour <= 20:
                    clean_ev["TimeOfDay"] = "Dusk"
                else:
                    clean_ev["TimeOfDay"] = "Night"
            elif k_lower in ("precipitation", "precip"):
                p = float(raw_v)
                if p > 0:
                    clean_ev["RoadSurface"] = "Wet"
            continue

        # Handle discrete values or numeric thresholds
        valid_states = NODE_STATES[canonical_k]

        # Numerical conversion if supplied as numbers
        if isinstance(raw_v, (int, float)):
            if canonical_k == "Visibility":
                val = "Poor" if float(raw_v) < 5.0 else "Good"
            elif canonical_k == "TrafficDensity":
                val = "High" if raw_v >= 70 else ("Med" if raw_v >= 35 else "Low")
            elif canonical_k == "Severity":
                val = "High" if raw_v >= 1 else "Low"
            else:
                val = str(raw_v)
        else:
            val = str(raw_v).strip().capitalize()
            # Special case title casing
            if canonical_k == "TimeOfDay":
                val_upper = val.upper()
                if "DAY" in val_upper:
                    val = "Day"
                elif "DUSK" in val_upper:
                    val = "Dusk"
                elif "NIGHT" in val_upper:
                    val = "Night"
            elif canonical_k == "TrafficDensity":
                val_upper = val.upper()
                if "HIGH" in val_upper:
                    val = "High"
                elif "MED" in val_upper:
                    val = "Med"
                elif "LOW" in val_upper:
                    val = "Low"

        if val in valid_states:
            clean_ev[canonical_k] = val

    return clean_ev


def marginals(evidence: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, float]]:
    """
    Computes marginal probability distributions for ALL nodes in the Bayesian Network
    conditioned on the given evidence using Variable Elimination.

    Parameters
    ----------
    evidence : dict, optional
        Observed evidence (e.g. {'Weather': 'Rain', 'TimeOfDay': 'Night'}).

    Returns
    -------
    dict
        Dictionary mapping node names to {state: probability} distributions.
    """
    engine = get_inference_engine()
    clean_ev = normalize_evidence(evidence)

    results = {}
    for node, valid_states in NODE_STATES.items():
        if node in clean_ev:
            # Node is directly observed
            obs_state = clean_ev[node]
            results[node] = {s: (1.0 if s == obs_state else 0.0) for s in valid_states}
        else:
            # Query marginal distribution
            factor = engine.query(variables=[node], evidence=clean_ev, show_progress=False)
            dist = {}
            for state in valid_states:
                try:
                    prob = float(factor.get_value(**{node: state}))
                except Exception:
                    prob = 0.0
                dist[state] = round(prob, 4)
            # Normalize to guarantee exact sum = 1.0
            tot = sum(dist.values())
            if tot > 0:
                dist = {s: round(p / tot, 4) for s, p in dist.items()}
            results[node] = dist

    # Add snake_case aliases to match frontend BayesianMarginals schema
    results["weather"] = results["Weather"]
    results["time_of_day"] = results["TimeOfDay"]
    results["traffic_density"] = results["TrafficDensity"]
    results["visibility"] = results["Visibility"]
    results["road_surface"] = results["RoadSurface"]
    results["severity"] = results["Severity"]
    results["accident_risk"] = results["Severity"]

    return results


def p_severe(evidence: Optional[Dict[str, Any]] = None) -> float:
    """
    Computes P(Severity = High | evidence).
    Exposes high severity accident probability as a float in [0.0, 1.0].
    """
    m = marginals(evidence)
    return float(m["Severity"].get("High", 0.0))


def counterfactual_query(
    intervention: Dict[str, Any],
    evidence: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Performs Pearl's causal intervention query:
        P(Severity | do(intervention), evidence)
    
    Evaluates what-if policy scenarios (e.g., "What if RoadSurface were forced Dry?").
    Graphically, the do(X=x) operator severs all incoming causal edges to X (mutilated graph),
    allowing true counterfactual risk reduction analysis.

    Parameters
    ----------
    intervention : dict
        Forced causal intervention (e.g. {'RoadSurface': 'Dry'}).
    evidence : dict, optional
        Pre-existing observational context (e.g. {'Weather': 'Rain'}).

    Returns
    -------
    dict
        Summary with baseline observational risk, counterfactual interventional risk,
        absolute risk delta, and percentage reduction.
    """
    causal_engine = get_causal_engine()
    clean_intervention = normalize_evidence(intervention)
    clean_evidence = normalize_evidence(evidence)

    # Remove any intervention variables from evidence to prevent contradiction
    for k in clean_intervention:
        clean_evidence.pop(k, None)

    # 1. Observational baseline risk
    baseline_risk = p_severe(clean_evidence)

    # 2. Causal intervention query via pgmpy CausalInference do-query
    try:
        factor = causal_engine.query(
            variables=["Severity"],
            do=clean_intervention,
            evidence=clean_evidence if clean_evidence else None
        )
        post_p_high = float(factor.get_value(Severity="High"))
        post_p_low = float(factor.get_value(Severity="Low"))
    except Exception:
        # Fallback to mutilated network query
        model = get_model()
        mutilated = model.do(list(clean_intervention.keys()))
        infer = VariableElimination(mutilated)
        joint_ev = dict(clean_evidence)
        joint_ev.update(clean_intervention)
        factor = infer.query(variables=["Severity"], evidence=joint_ev, show_progress=False)
        post_p_high = float(factor.get_value(Severity="High"))
        post_p_low = float(factor.get_value(Severity="Low"))

    post_p_high = float(np.clip(post_p_high, 0.0, 1.0))
    post_p_low = float(np.clip(post_p_low, 0.0, 1.0))

    risk_delta = post_p_high - baseline_risk
    reduction_pct = (
        ((baseline_risk - post_p_high) / baseline_risk) * 100.0 if baseline_risk > 0 else 0.0
    )

    return {
        "intervention": clean_intervention,
        "evidence": clean_evidence,
        "baseline_p_severe": round(baseline_risk, 4),
        "interventional_p_severe": round(post_p_high, 4),
        "risk_delta": round(risk_delta, 4),
        "risk_reduction_pct": round(reduction_pct, 2),
        "distribution": {
            "Low": round(post_p_low, 4),
            "High": round(post_p_high, 4)
        }
    }


if __name__ == "__main__":
    print("=" * 65)
    print("SafeRoute AI — Bayesian Network Inference & Causal Engine (CO4)")
    print("=" * 65)

    # 1. Unconditional Marginals
    print("\n[1/3] Unconditional Prior Marginal Probabilities:")
    priors = marginals()
    for node in ["Weather", "TimeOfDay", "TrafficDensity", "Visibility", "RoadSurface", "Severity"]:
        print(f"   {node:<15}: {priors[node]}")

    # 2. Evidence Query (Rainy Night at High Traffic)
    print("\n[2/3] Conditional Inference — Hazardous Conditions (Weather=Rain, TimeOfDay=Night, Traffic=High):")
    haz_evidence = {"Weather": "Rain", "TimeOfDay": "Night", "TrafficDensity": "High"}
    haz_marginals = marginals(haz_evidence)
    p_haz = p_severe(haz_evidence)
    print(f"   Visibility Marginal : {haz_marginals['Visibility']}")
    print(f"   RoadSurface Marginal: {haz_marginals['RoadSurface']}")
    print(f"   P(Severity = High)  : {p_haz * 100:.2f}% (Baseline Prior: {priors['Severity']['High'] * 100:.2f}%)")

    # 3. Pearl Causal Intervention Query (do(RoadSurface = Dry))
    print("\n[3/3] Pearl Causal Intervention Query — what if RoadSurface were forced Dry?:")
    cf_result = counterfactual_query(
        intervention={"RoadSurface": "Dry"},
        evidence={"Weather": "Rain", "TimeOfDay": "Night"}
    )
    print(f"   Context (Evidence)           : {cf_result['evidence']}")
    print(f"   Intervention Policy          : do({cf_result['intervention']})")
    print(f"   Baseline Risk P(Severe|Rain) : {cf_result['baseline_p_severe'] * 100:.2f}%")
    print(f"   Interventional Risk P(Severe): {cf_result['interventional_p_severe'] * 100:.2f}%")
    print(f"   Causal Risk Reduction        : {cf_result['risk_reduction_pct']:.1f}%")
    print("=" * 65)
