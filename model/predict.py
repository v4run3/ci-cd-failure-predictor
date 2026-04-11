"""
predict.py - Model Prediction Module

Purpose:
    Load a trained model and generate predictions on new CI/CD build
    data. Supports single-record and batch prediction, returning both
    binary predictions and failure probabilities.

Usage:
    python model/predict.py
"""

import os

import joblib
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "model", "saved_model.pkl")

FEATURE_NAMES = [
    "num_files_changed", "lines_added", "lines_deleted",
    "test_count", "test_pass_count", "test_fail_count",
    "build_duration_seconds",
    "hour", "day_of_week", "is_late_night", "is_weekend",
    "total_lines_changed", "lines_per_file", "test_fail_ratio",
    "branch_is_hotfix", "branch_is_bugfix", "branch_is_feature",
    "branch_is_release",
    "trigger_is_push", "trigger_is_schedule",
]

# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------


def load_model(path: str = MODEL_PATH):
    """Load a saved model from disk."""
    return joblib.load(path)


# ---------------------------------------------------------------------------
# Prediction functions
# ---------------------------------------------------------------------------


def predict_single(model, features: dict) -> dict:
    """Predict failure for a single build record.

    Args:
        model: Trained sklearn model.
        features: Dict with all 20 feature values.

    Returns:
        Dict with 'prediction' (0/1) and 'failure_probability' (0.0-1.0).
    """
    missing = set(FEATURE_NAMES) - set(features.keys())
    if missing:
        raise ValueError(f"Missing features: {missing}")

    df = pd.DataFrame([features])[FEATURE_NAMES]
    prediction = int(model.predict(df)[0])
    probability = float(model.predict_proba(df)[0][1])

    return {
        "prediction": prediction,
        "label": "failure" if prediction == 1 else "success",
        "failure_probability": round(probability, 4),
    }


def predict_batch(model, df: pd.DataFrame) -> pd.DataFrame:
    """Predict failures for a batch of build records.

    Args:
        model: Trained sklearn model.
        df: DataFrame with all 20 feature columns.

    Returns:
        Copy of input DataFrame with 'prediction' and 'failure_probability' appended.
    """
    missing = set(FEATURE_NAMES) - set(df.columns)
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")

    result = df.copy()
    X = df[FEATURE_NAMES]
    result["prediction"] = model.predict(X)
    result["failure_probability"] = model.predict_proba(X)[:, 1].round(4)
    return result


# ---------------------------------------------------------------------------
# Entry point — demo with a sample record
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("CI/CD Failure Predictor - Prediction Demo")
    print("=" * 60 + "\n")

    model = load_model()
    print(f"Model loaded from: {MODEL_PATH}\n")

    # High-risk build: hotfix branch, late night, many files changed
    high_risk = {
        "num_files_changed": 25,
        "lines_added": 600,
        "lines_deleted": 200,
        "test_count": 150,
        "test_pass_count": 140,
        "test_fail_count": 10,
        "build_duration_seconds": 450,
        "hour": 23,
        "day_of_week": 6,
        "is_late_night": 1,
        "is_weekend": 1,
        "total_lines_changed": 800,
        "lines_per_file": 32.0,
        "test_fail_ratio": 0.0667,
        "branch_is_hotfix": 1,
        "branch_is_bugfix": 0,
        "branch_is_feature": 0,
        "branch_is_release": 0,
        "trigger_is_push": 1,
        "trigger_is_schedule": 0,
    }

    # Low-risk build: feature branch, daytime, few files
    low_risk = {
        "num_files_changed": 3,
        "lines_added": 45,
        "lines_deleted": 10,
        "test_count": 200,
        "test_pass_count": 200,
        "test_fail_count": 0,
        "build_duration_seconds": 120,
        "hour": 14,
        "day_of_week": 2,
        "is_late_night": 0,
        "is_weekend": 0,
        "total_lines_changed": 55,
        "lines_per_file": 18.33,
        "test_fail_ratio": 0.0,
        "branch_is_hotfix": 0,
        "branch_is_bugfix": 0,
        "branch_is_feature": 1,
        "branch_is_release": 0,
        "trigger_is_push": 0,
        "trigger_is_schedule": 0,
    }

    print("--- High-risk build (hotfix, late night, many files) ---")
    result = predict_single(model, high_risk)
    print(f"  Prediction : {result['label']}")
    print(f"  Probability: {result['failure_probability']:.1%}\n")

    print("--- Low-risk build (feature branch, daytime, few files) ---")
    result = predict_single(model, low_risk)
    print(f"  Prediction : {result['label']}")
    print(f"  Probability: {result['failure_probability']:.1%}")
