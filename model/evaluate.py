"""
evaluate.py - Model Evaluation Module

Purpose:
    Load a trained model and evaluate its performance on test data
    using standard classification metrics: accuracy, precision, recall,
    F1-score, ROC-AUC, confusion matrix, and classification report.

Usage:
    python model/evaluate.py
"""

import os

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "model", "saved_model.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "data", "processed", "features.csv")

TARGET_COLUMN = "failed"
TEST_SIZE = 0.2
RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_model(path: str = MODEL_PATH):
    """Load a saved model from disk."""
    return joblib.load(path)


def load_test_data(
    path: str = FEATURES_PATH,
) -> tuple[pd.DataFrame, pd.Series]:
    """Load features CSV and return the test split (same split as training).

    Uses the same random_state and test_size as train.py to reproduce
    the exact same test set.
    """
    df = pd.read_csv(path)
    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    return X_test, y_test


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def evaluate_model(
    model, X_test: pd.DataFrame, y_test: pd.Series
) -> dict:
    """Compute all classification metrics.

    Returns:
        Dict with accuracy, precision, recall, f1, roc_auc, confusion_matrix.
    """
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    return {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred), 4),
        "recall": round(recall_score(y_test, y_pred), 4),
        "f1_score": round(f1_score(y_test, y_pred), 4),
        "roc_auc": round(roc_auc_score(y_test, y_proba), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "classification_report": classification_report(
            y_test, y_pred, target_names=["success", "failure"]
        ),
    }


def print_metrics(metrics: dict) -> None:
    """Print evaluation metrics in a readable format."""
    print("Metrics:")
    print(f"  Accuracy  : {metrics['accuracy']:.4f}")
    print(f"  Precision : {metrics['precision']:.4f}")
    print(f"  Recall    : {metrics['recall']:.4f}")
    print(f"  F1-Score  : {metrics['f1_score']:.4f}")
    print(f"  ROC-AUC   : {metrics['roc_auc']:.4f}")

    cm = metrics["confusion_matrix"]
    print(f"\nConfusion Matrix:")
    print(f"                Predicted")
    print(f"                Success  Failure")
    print(f"  Actual Success   {cm[0][0]:>4d}     {cm[0][1]:>4d}")
    print(f"  Actual Failure   {cm[1][0]:>4d}     {cm[1][1]:>4d}")

    print(f"\nClassification Report:")
    print(metrics["classification_report"])


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_evaluation(
    model_path: str = MODEL_PATH, data_path: str = FEATURES_PATH
) -> dict:
    """Load model and test data, evaluate, print results.

    Returns:
        Dict of evaluation metrics.
    """
    model = load_model(model_path)
    X_test, y_test = load_test_data(data_path)

    print(f"Model loaded from: {model_path}")
    print(f"Test set: {len(X_test)} rows\n")

    metrics = evaluate_model(model, X_test, y_test)
    print_metrics(metrics)
    return metrics


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("CI/CD Failure Predictor - Model Evaluation")
    print("=" * 60 + "\n")
    run_evaluation()
