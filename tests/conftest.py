"""
conftest.py - Shared pytest fixtures for CI/CD Failure Predictor tests.

Provides reusable fixtures for:
  - Sample raw build data
  - Processed feature DataFrames
  - Trained model
  - FastAPI TestClient
"""

import os
import sys

import joblib
import pandas as pd
import pytest
from fastapi.testclient import TestClient

# Make project root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.fetch_logs import generate_synthetic_data
from features.build_features import build_features, save_features
from model.train import train_pipeline
from api.main import app


# ---------------------------------------------------------------------------
# Data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def raw_df(tmp_path_factory):
    """Generate a small synthetic raw log DataFrame (100 records)."""
    return generate_synthetic_data(num_records=100, seed=0)


@pytest.fixture(scope="session")
def raw_csv_path(raw_df, tmp_path_factory):
    """Save raw data to a temp CSV and return the path."""
    tmp = tmp_path_factory.mktemp("data")
    path = str(tmp / "build_logs.csv")
    raw_df.to_csv(path, index=False)
    return path


@pytest.fixture(scope="session")
def features_df(raw_csv_path):
    """Run the full feature engineering pipeline on raw data."""
    return build_features(input_path=raw_csv_path)


@pytest.fixture(scope="session")
def features_csv_path(features_df, tmp_path_factory):
    """Save features to a temp CSV and return the path."""
    tmp = tmp_path_factory.mktemp("processed")
    path = str(tmp / "features.csv")
    features_df.to_csv(path, index=False)
    return path


# ---------------------------------------------------------------------------
# Model fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def trained_model(features_csv_path, tmp_path_factory):
    """Train a model on the temp features CSV — returns (model, name)."""
    tmp = tmp_path_factory.mktemp("model")
    model_path = str(tmp / "test_model.pkl")
    meta_path = str(tmp / "test_metadata.json")
    model, name = train_pipeline(
        data_path=features_csv_path,
        model_path=model_path,
        metadata_path=meta_path,
    )
    return model, name


# ---------------------------------------------------------------------------
# API fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def api_client():
    """Return a FastAPI TestClient — model must exist on disk."""
    with TestClient(app) as client:
        yield client


# ---------------------------------------------------------------------------
# Shared sample feature dict
# ---------------------------------------------------------------------------

@pytest.fixture
def high_risk_features():
    return {
        "num_files_changed": 25, "lines_added": 600, "lines_deleted": 200,
        "test_count": 150, "test_pass_count": 130, "test_fail_count": 20,
        "build_duration_seconds": 500, "hour": 23, "day_of_week": 6,
        "is_late_night": 1, "is_weekend": 1, "total_lines_changed": 800,
        "lines_per_file": 32.0, "test_fail_ratio": 0.133,
        "branch_is_hotfix": 1, "branch_is_bugfix": 0,
        "branch_is_feature": 0, "branch_is_release": 0,
        "trigger_is_push": 1, "trigger_is_schedule": 0,
    }


@pytest.fixture
def low_risk_features():
    return {
        "num_files_changed": 3, "lines_added": 45, "lines_deleted": 10,
        "test_count": 200, "test_pass_count": 200, "test_fail_count": 0,
        "build_duration_seconds": 120, "hour": 14, "day_of_week": 2,
        "is_late_night": 0, "is_weekend": 0, "total_lines_changed": 55,
        "lines_per_file": 18.33, "test_fail_ratio": 0.0,
        "branch_is_hotfix": 0, "branch_is_bugfix": 0,
        "branch_is_feature": 1, "branch_is_release": 0,
        "trigger_is_push": 0, "trigger_is_schedule": 0,
    }
