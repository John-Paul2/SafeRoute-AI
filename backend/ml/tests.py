"""
SafeRoute AI - ML Model & Edge Risk Unit Tests
Course Outcome: CO5 (Machine Learning Techniques) & CO2 (Risk-Aware Search Graph Integration)
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR.parent) not in sys.path:
    sys.path.insert(0, str(BASE_DIR.parent))

import unittest
import pandas as pd
import joblib

try:
    from backend.ml.edge_risk import predict_risk, load_or_build_graph, get_model
except ImportError:
    from ml.edge_risk import predict_risk, load_or_build_graph, get_model


class MLAndEdgeRiskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent.parent
        cls.models_dir = cls.base_dir / "models"
        cls.docs_dir = cls.base_dir.parent / "docs"

    def test_clean_parquet_exists_and_valid(self):
        parquet_path = self.base_dir / "data" / "clean.parquet"
        self.assertTrue(parquet_path.exists(), f"clean.parquet missing at {parquet_path}")

        df = pd.read_parquet(parquet_path)
        self.assertLessEqual(len(df), 100_000, "Dataset exceeds 100k sample limit")
        self.assertGreater(len(df), 0, "Dataset is empty")

        # Required engineered features
        required_cols = [
            "high_severity", "hour", "day_of_week", "is_weekend", "is_night",
            "temperature", "visibility", "precipitation", "humidity", "wind_speed",
            "weather_condition", "junction", "traffic_signal", "grid_cell_id"
        ]
        for col in required_cols:
            self.assertIn(col, df.columns, f"Missing required column: {col}")

        self.assertTrue(set(df["high_severity"].unique()).issubset({0, 1}))
        self.assertEqual(df.isnull().sum().sum(), 0, "Null values detected in clean dataset")

    def test_xgb_model_artifacts_exist(self):
        model_path = self.models_dir / "xgb.joblib"
        meta_path = self.models_dir / "xgb_meta.json"
        self.assertTrue(model_path.exists(), "xgb.joblib model artifact missing")
        self.assertTrue(meta_path.exists(), "xgb_meta.json artifact missing")

        # Check documentation plots exist
        for plot_name in [
            "xgb_confusion_matrix.png",
            "xgb_roc_curve.png",
            "xgb_calibration_curve.png",
            "xgb_feature_importance.png"
        ]:
            plot_file = self.docs_dir / plot_name
            self.assertTrue(plot_file.exists(), f"Evaluation plot missing: {plot_name}")

    def test_predict_risk_live_conditions(self):
        # Clear normal conditions
        risk_clear = predict_risk({
            "weather_condition": "Clear",
            "precipitation": 0.0,
            "visibility": 10.0,
            "hour": 14
        })
        self.assertIsInstance(risk_clear, float)
        self.assertGreaterEqual(risk_clear, 0.0)
        self.assertLessEqual(risk_clear, 1.0)

        # Severe adverse conditions
        risk_severe = predict_risk({
            "weather_condition": "Rain",
            "precipitation": 0.9,
            "visibility": 1.5,
            "hour": 22,
            "junction": 1
        })
        self.assertIsInstance(risk_severe, float)
        self.assertGreaterEqual(risk_severe, 0.0)
        self.assertLessEqual(risk_severe, 1.0)

    def test_osm_graph_edge_baseline_risks(self):
        graph_path = self.models_dir / "graph.graphml"
        self.assertTrue(graph_path.exists(), f"OSM graph missing at {graph_path}")

        G = load_or_build_graph()
        self.assertGreater(len(G.nodes), 100, "Graph has too few nodes")
        self.assertLessEqual(len(G.nodes), 20_000, "Graph exceeds 20k node limit")
        self.assertGreater(len(G.edges), 100, "Graph has too few edges")

        # Verify edge baseline risk attributes
        for _, _, _, data in list(G.edges(keys=True, data=True))[:50]:
            self.assertIn("risk_score", data, "Edge missing risk_score attribute")
            self.assertIn("base_risk", data, "Edge missing base_risk attribute")
            self.assertIn("accident_density", data, "Edge missing accident_density attribute")
            score = float(data["risk_score"])
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
