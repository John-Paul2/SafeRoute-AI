"""
SafeRoute AI - Supervised Accident Severity Prediction Pipeline
Course Outcome: CO5 (Machine Learning Techniques)

Description:
    Trains an XGBoost gradient boosted tree classifier on historical accident data
    (data/clean.parquet) to predict the probability of high-severity accidents (Severity >= 3).
    
Key Methodologies:
    1. Stratified train/test splitting (80/20) preserving severe accident proportion.
    2. Class imbalance mitigation using scale_pos_weight = (N_negative / N_positive).
    3. Probability calibration using CalibratedClassifierCV (Platt scaling / Sigmoid) so that
       predicted probabilities reliably reflect true accident risk scores [0.0, 1.0].
    4. Comprehensive metric reporting: Accuracy, Precision, Recall, F1, ROC-AUC, Brier Score.
    5. Artifact generation:
       - docs/xgb_confusion_matrix.png
       - docs/xgb_roc_curve.png
       - docs/xgb_feature_importance.png
       - docs/xgb_calibration_curve.png
       - models/xgb.joblib (persisted calibrated pipeline for live API queries)
"""

import os
import sys
import time
import json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless server execution
import matplotlib.pyplot as plt

from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
    confusion_matrix,
    brier_score_loss,
    classification_report
)

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "clean.parquet"
MODELS_DIR = BASE_DIR / "models"
DOCS_DIR = BASE_DIR.parent / "docs"

# Feature configuration
FEATURE_COLUMNS = [
    "hour", "day_of_week", "is_weekend", "is_night",
    "temperature", "humidity", "visibility", "wind_speed", "precipitation",
    "weather_condition", "junction", "traffic_signal"
]

CATEGORICAL_FEATURES = ["weather_condition"]
WEATHER_CATEGORIES = ["Clear", "Rain", "Fog", "Snow", "Other"]
NUMERICAL_FEATURES = [col for col in FEATURE_COLUMNS if col not in CATEGORICAL_FEATURES]
TARGET_COLUMN = "high_severity"


def build_preprocessor() -> ColumnTransformer:
    """Builds a scikit-learn ColumnTransformer for categorical and continuous features."""
    return ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(
                    categories=[WEATHER_CATEGORIES],
                    handle_unknown="ignore",
                    sparse_output=False
                ),
                CATEGORICAL_FEATURES,
            ),
            ("num", "passthrough", NUMERICAL_FEATURES),
        ],
        remainder="drop",
    )


def plot_confusion_matrix(cm: np.ndarray, save_path: Path):
    """Plots and saves an annotated confusion matrix heatmap."""
    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
    cax = ax.matshow(cm, cmap="Blues", alpha=0.85)
    fig.colorbar(cax, shrink=0.8)

    labels = ["Low Severity (1-2)", "High Severity (3-4)"]
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(labels, fontsize=10, fontweight="bold")
    ax.set_yticklabels(labels, fontsize=10, fontweight="bold")
    ax.set_xlabel("Predicted Label", fontsize=11, labelpad=10)
    ax.set_ylabel("True Label", fontsize=11, labelpad=10)
    ax.set_title("Confusion Matrix — Calibrated XGBoost", fontsize=12, fontweight="bold", pad=15)

    total = np.sum(cm)
    for i in range(2):
        for j in range(2):
            count = cm[i, j]
            pct = count / total * 100
            color = "white" if count > (cm.max() / 2) else "black"
            ax.text(
                j, i, f"{count:,}\n({pct:.1f}%)",
                ha="center", va="center", color=color, fontsize=11, fontweight="bold"
            )

    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    print(f"   [Saved] Confusion matrix plot -> {save_path}")


def plot_roc_curve(y_true: np.ndarray, y_prob: np.ndarray, auc_score: float, optimal_thresh: float, save_path: Path):
    """Plots and saves the Receiver Operating Characteristic (ROC) curve with optimal threshold marked."""
    fpr, tpr, thresholds = roc_curve(y_true, y_prob)
    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)

    ax.plot(fpr, tpr, color="#197e25", lw=2.5, label=f"XGBoost ROC (AUC = {auc_score:.3f})")
    ax.plot([0, 1], [0, 1], color="#a7a9ac", lw=1.5, linestyle="--", label="Random Baseline (AUC = 0.500)")

    # Mark optimal threshold (Youden's J statistic)
    j_scores = tpr - fpr
    best_idx = np.argmax(j_scores)
    ax.scatter(fpr[best_idx], tpr[best_idx], marker="o", color="#ce1736", s=80, zorder=5,
               label=f"Optimal Decision Cutoff ({optimal_thresh:.3f})")

    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
    ax.set_ylabel("True Positive Rate (Recall / Sensitivity)", fontsize=11)
    ax.set_title("ROC Curve — Severe Accident Classifier", fontsize=12, fontweight="bold")
    ax.legend(loc="lower right", frameon=True, fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    print(f"   [Saved] ROC curve plot -> {save_path}")


def plot_calibration_curve(y_true: np.ndarray, uncal_prob: np.ndarray, cal_prob: np.ndarray, save_path: Path):
    """Plots reliability diagrams (calibration curve) before and after probability calibration."""
    prob_true_uncal, prob_pred_uncal = calibration_curve(y_true, uncal_prob, n_bins=10, strategy="uniform")
    prob_true_cal, prob_pred_cal = calibration_curve(y_true, cal_prob, n_bins=10, strategy="uniform")

    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
    ax.plot([0, 1], [0, 1], "k--", lw=1.5, label="Perfectly Calibrated")
    ax.plot(prob_pred_uncal, prob_true_uncal, "s-", color="#ce1736", lw=1.8, label="Raw XGBoost (Uncalibrated)")
    ax.plot(prob_pred_cal, prob_true_cal, "o-", color="#197e25", lw=2.2, label="Calibrated (Platt Sigmoid)")

    ax.set_xlabel("Mean Predicted Risk Probability", fontsize=11)
    ax.set_ylabel("Empirical Fraction of High Severity", fontsize=11)
    ax.set_title("Reliability Curve — Risk Score Calibration", fontsize=12, fontweight="bold")
    ax.legend(loc="upper left", frameon=True, fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    print(f"   [Saved] Calibration curve plot -> {save_path}")


def plot_feature_importance(importances: np.ndarray, feature_names: list, save_path: Path):
    """Plots and saves normalized feature importances with descriptive names."""
    # Clean up feature names for presentation
    clean_names = []
    for f in feature_names:
        clean = (
            f.replace("cat__weather_condition_", "Weather: ")
            .replace("num__", "")
            .replace("_", " ")
            .title()
        )
        clean_names.append(clean)

    # Sort in ascending order for horizontal bar chart
    idx = np.argsort(importances)
    sorted_importances = importances[idx]
    sorted_names = [clean_names[i] for i in idx]

    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    bars = ax.barh(sorted_names, sorted_importances, color="#30a83c", edgecolor="#197e25", alpha=0.85)

    # Annotate bar values
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.003, bar.get_y() + bar.get_height() / 2, f"{w * 100:.1f}%",
                va="center", ha="left", fontsize=9, color="#222222")

    ax.set_xlabel("Relative Feature Importance (Gain / Split Contribution)", fontsize=11)
    ax.set_title("XGBoost Feature Importances (CO5)", fontsize=12, fontweight="bold")
    ax.set_xlim([0, max(sorted_importances) * 1.15])
    ax.grid(axis="x", linestyle=":", alpha=0.6)

    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    print(f"   [Saved] Feature importance plot -> {save_path}")


def train_and_evaluate():
    """Main execution function to train, calibrate, evaluate, and save XGBoost model."""
    print("=" * 65)
    print("SafeRoute AI — XGBoost Accident Severity Model Training (CO5)")
    print("=" * 65)

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Clean parquet dataset not found at {DATA_PATH}. Run prepare_data.py first.")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n[1/5] Loading cleaned dataset from {DATA_PATH}...")
    df = pd.read_parquet(DATA_PATH)
    print(f"   Loaded {len(df):,} records with columns: {list(df.columns)}")

    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()

    # Stratified Train/Test split
    print(f"\n[2/5] Stratified Train/Test Split (80% train, 20% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"   Train set size : {len(X_train):,} rows ({y_train.sum():,} positive high severity)")
    print(f"   Test set size  : {len(X_test):,} rows ({y_test.sum():,} positive high severity)")

    # Class imbalance handling
    n_neg = len(y_train) - y_train.sum()
    n_pos = y_train.sum()
    scale_pos_weight = n_neg / max(n_pos, 1)
    print(f"   Class balance  : Negative={n_neg:,}, Positive={n_pos:,}")
    print(f"   Imbalance ratio (scale_pos_weight): {scale_pos_weight:.2f}")

    # Build preprocessing and base XGBoost model
    preprocessor = build_preprocessor()
    base_xgb = XGBClassifier(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.08,
        scale_pos_weight=scale_pos_weight,
        subsample=0.85,
        colsample_bytree=0.85,
        eval_metric="logloss",
        random_state=42,
        tree_method="hist",
        n_jobs=-1
    )

    # 1. Fit base pipeline to extract uncalibrated probabilities & feature importances
    print(f"\n[3/5] Fitting base XGBoost pipeline...")
    t0 = time.time()
    base_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("xgb", base_xgb)
    ])
    base_pipeline.fit(X_train, y_train)
    t_base = time.time() - t0
    print(f"   Base model trained in {t_base:.2f}s.")

    # Extract feature importances
    fitted_xgb = base_pipeline.named_steps["xgb"]
    fitted_prep = base_pipeline.named_steps["preprocessor"]
    transformed_feature_names = fitted_prep.get_feature_names_out()
    feature_importances = fitted_xgb.feature_importances_

    # 2. Probability Calibration with 3-fold cross validation
    print(f"\n[4/5] Calibrating probabilities via CalibratedClassifierCV (Sigmoid / Platt)...")
    t0 = time.time()
    calibrated_clf = CalibratedClassifierCV(
        estimator=base_pipeline,
        method="sigmoid",
        cv=3
    )
    calibrated_clf.fit(X_train, y_train)
    t_cal = time.time() - t0
    print(f"   Calibrated classifier fitted in {t_cal:.2f}s.")

    # 3. Evaluation on Test Split
    print(f"\n[5/5] Evaluating calibrated predictions on holdout test set...")
    uncal_probs = base_pipeline.predict_proba(X_test)[:, 1]
    cal_probs = calibrated_clf.predict_proba(X_test)[:, 1]

    # Find optimal threshold using Youden's J statistic on training set
    train_cal_probs = calibrated_clf.predict_proba(X_train)[:, 1]
    train_fpr, train_tpr, train_thresholds = roc_curve(y_train, train_cal_probs)
    youden_idx = np.argmax(train_tpr - train_fpr)
    optimal_threshold = float(train_thresholds[youden_idx])
    print(f"   Calculated optimal decision threshold (Youden's J): {optimal_threshold:.4f}")

    # Binary predictions using optimal threshold aligned with empirical base rate
    y_pred_opt = (cal_probs >= optimal_threshold).astype(int)
    y_pred_default = (cal_probs >= 0.50).astype(int)

    acc = accuracy_score(y_test, y_pred_opt)
    prec = precision_score(y_test, y_pred_opt, zero_division=0)
    rec = recall_score(y_test, y_pred_opt, zero_division=0)
    f1 = f1_score(y_test, y_pred_opt, zero_division=0)
    auc = roc_auc_score(y_test, cal_probs)
    brier_uncal = brier_score_loss(y_test, uncal_probs)
    brier_cal = brier_score_loss(y_test, cal_probs)
    cm = confusion_matrix(y_test, y_pred_opt)

    print("\n" + "=" * 55)
    print("EVALUATION METRICS SUMMARY (Holdout Test Set)")
    print("=" * 55)
    print(f"Optimal Threshold: {optimal_threshold:.4f} (Calibrated for ~9.2% positive base rate)")
    print(f"Accuracy         : {acc * 100:.2f}%")
    print(f"Precision        : {prec * 100:.2f}%")
    print(f"Recall           : {rec * 100:.2f}%")
    print(f"F1-Score         : {f1:.4f}")
    print(f"ROC-AUC Score    : {auc:.4f}")
    print(f"Brier Score (Raw): {brier_uncal:.4f}")
    print(f"Brier Score (Cal): {brier_cal:.4f}  (Lower is better calibration)")
    print(f"Confusion Matrix (at optimal cutoff {optimal_threshold:.3f}):")
    print(f"   TN: {cm[0,0]:>6,} | FP: {cm[0,1]:>6,}")
    print(f"   FN: {cm[1,0]:>6,} | TP: {cm[1,1]:>6,}")
    print("=" * 55)

    print("\nClassification Detailed Report (Balanced Risk Threshold):")
    print(classification_report(y_test, y_pred_opt, target_names=["Low Severity", "High Severity"]))

    # Save artifact plots to docs/
    print("\nGenerating and saving publication-ready plots...")
    plot_confusion_matrix(cm, DOCS_DIR / "xgb_confusion_matrix.png")
    plot_roc_curve(y_test.values, cal_probs, auc, optimal_threshold, DOCS_DIR / "xgb_roc_curve.png")
    plot_calibration_curve(y_test.values, uncal_probs, cal_probs, DOCS_DIR / "xgb_calibration_curve.png")
    plot_feature_importance(feature_importances, transformed_feature_names, DOCS_DIR / "xgb_feature_importance.png")

    # Persist trained model artifact
    model_save_path = MODELS_DIR / "xgb.joblib"
    print(f"\nPersisting calibrated model artifact to {model_save_path}...")
    joblib.dump(calibrated_clf, model_save_path)

    # Also save training summary metadata for API meta endpoints and reports
    meta_payload = {
        "model_name": "Calibrated XGBoost Classifier",
        "course_outcome": "CO5 (Machine Learning Techniques)",
        "features": FEATURE_COLUMNS,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "scale_pos_weight": float(round(scale_pos_weight, 3)),
        "optimal_threshold": float(round(optimal_threshold, 4)),
        "metrics": {
            "accuracy": float(round(acc, 4)),
            "precision": float(round(prec, 4)),
            "recall": float(round(rec, 4)),
            "f1_score": float(round(f1, 4)),
            "roc_auc": float(round(auc, 4)),
            "brier_score_raw": float(round(brier_uncal, 4)),
            "brier_score_calibrated": float(round(brier_cal, 4)),
        },
        "confusion_matrix": {
            "tn": int(cm[0, 0]),
            "fp": int(cm[0, 1]),
            "fn": int(cm[1, 0]),
            "tp": int(cm[1, 1]),
        },
        "top_features": sorted(
            [
                {"feature": str(name), "importance": float(round(imp, 4))}
                for name, imp in zip(transformed_feature_names, feature_importances)
            ],
            key=lambda x: x["importance"],
            reverse=True,
        ),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    meta_path = MODELS_DIR / "xgb_meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta_payload, f, indent=2)
    print(f"   [Saved] Model metadata -> {meta_path}")
    print(f"   Model training and evaluation successfully completed!")


if __name__ == "__main__":
    train_and_evaluate()
