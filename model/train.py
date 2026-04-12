"""
train.py - Model Training Module

Purpose:
    Train two classifiers (Random Forest and Logistic Regression) on
    engineered CI/CD build features, compare them on F1-score, and
    save the best model to disk along with training metadata.

Usage:
    python model/train.py
"""

import json
import os
from datetime import datetime

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEATURES_PATH = os.path.join(BASE_DIR, "data", "processed", "features.csv")
MODEL_DIR = os.path.join(BASE_DIR, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "saved_model.pkl")
METADATA_PATH = os.path.join(MODEL_DIR, "training_metadata.json")

TARGET_COLUMN = "failed"
TEST_SIZE = 0.2
RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# Data loading and splitting
# ---------------------------------------------------------------------------


def load_data(path: str = FEATURES_PATH) -> tuple[pd.DataFrame, pd.Series]:
    """Load features CSV and split into feature matrix X and target y.

    Args:
        path: Path to features.csv.

    Returns:
        Tuple of (X, y) where X has 20 feature columns and y is binary target.
    """
    df = pd.read_csv(path)
    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]
    return X, y


def split_data(
    X: pd.DataFrame, y: pd.Series
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Stratified 80/20 train-test split.

    Returns:
        (X_train, X_test, y_train, y_test)
    """
    return train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )


# ---------------------------------------------------------------------------
# Model training
# ---------------------------------------------------------------------------


def train_random_forest(
    X_train: pd.DataFrame, y_train: pd.Series
) -> RandomForestClassifier:
    """Train a Random Forest classifier with balanced class weights."""
    model = RandomForestClassifier(
        n_estimators=100,
        random_state=RANDOM_STATE,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)
    return model


def train_logistic_regression(
    X_train: pd.DataFrame, y_train: pd.Series
) -> Pipeline:
    """Train a Logistic Regression wrapped in a scaling pipeline."""
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(
            random_state=RANDOM_STATE,
            class_weight="balanced",
            max_iter=1000,
        )),
    ])
    pipeline.fit(X_train, y_train)
    return pipeline


# ---------------------------------------------------------------------------
# Model selection and saving
# ---------------------------------------------------------------------------


def select_best_model(
    models: dict, X_test: pd.DataFrame, y_test: pd.Series
) -> tuple[str, object, float]:
    """Compare models on F1-score and return the best one.

    Args:
        models: Dict of {name: trained_model}.
        X_test: Test feature matrix.
        y_test: Test target.

    Returns:
        Tuple of (best_name, best_model, best_f1).
    """
    best_name, best_model, best_f1 = None, None, -1.0

    for name, model in models.items():
        y_pred = model.predict(X_test)
        f1 = f1_score(y_test, y_pred)
        print(f"  {name:30s}  F1={f1:.4f}")
        if f1 > best_f1:
            best_name, best_model, best_f1 = name, model, f1

    return best_name, best_model, best_f1


def save_model(model: object, path: str = MODEL_PATH) -> str:
    """Save trained model to disk with joblib."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    return path


def save_metadata(
    model_name: str,
    feature_names: list[str],
    train_size: int,
    test_size: int,
    f1: float,
    path: str = METADATA_PATH,
) -> str:
    """Save training metadata as JSON for reproducibility."""
    metadata = {
        "model_name": model_name,
        "feature_names": feature_names,
        "train_size": train_size,
        "test_size": test_size,
        "best_f1_score": round(f1, 4),
        "test_split_ratio": TEST_SIZE,
        "random_state": RANDOM_STATE,
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(path, "w") as f:
        json.dump(metadata, f, indent=2)
    return path


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def train_pipeline(
    data_path: str = FEATURES_PATH,
    model_path: str = MODEL_PATH,
    metadata_path: str = METADATA_PATH,
) -> tuple[object, str]:
    """Full training pipeline: load -> split -> train -> compare -> save.

    Args:
        data_path: Path to features.csv.
        model_path: Where to save the trained model .pkl.
        metadata_path: Where to save training_metadata.json.

    Returns:
        Tuple of (best_model, best_model_name).
    """
    # Load and split
    X, y = load_data(data_path)
    X_train, X_test, y_train, y_test = split_data(X, y)

    print(f"Train set: {len(X_train)} rows | Test set: {len(X_test)} rows")
    print(f"Features: {len(X.columns)} | Target: '{TARGET_COLUMN}'\n")

    # Train both models
    print("Training models...")
    rf = train_random_forest(X_train, y_train)
    lr = train_logistic_regression(X_train, y_train)

    # Compare and select best
    models = {
        "RandomForest": rf,
        "LogisticRegression": lr,
    }
    print("\nModel comparison (F1-score on test set):")
    best_name, best_model, best_f1 = select_best_model(models, X_test, y_test)

    # Save
    saved_model_path = save_model(best_model, path=model_path)
    meta_path = save_metadata(
        model_name=best_name,
        feature_names=list(X.columns),
        train_size=len(X_train),
        test_size=len(X_test),
        f1=best_f1,
        path=metadata_path,
    )

    print(f"\nBest model: {best_name} (F1={best_f1:.4f})")
    print(f"Model saved  -> {saved_model_path}")
    print(f"Metadata saved -> {meta_path}")

    return best_model, best_name


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("CI/CD Failure Predictor - Model Training")
    print("=" * 60 + "\n")
    train_pipeline()
