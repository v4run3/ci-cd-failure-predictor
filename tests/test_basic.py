"""
test_basic.py - Full Unit & Integration Test Suite
CI/CD Failure Predictor

Test groups:
  1. Data Generation     — ingestion/fetch_logs.py
  2. Feature Engineering — features/build_features.py
  3. Model Prediction    — model/predict.py
  4. API Endpoints       — api/main.py (FastAPI TestClient)
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.fetch_logs import generate_synthetic_data, generate_commit_hash
from features.build_features import (
    build_features,
    add_temporal_features,
    add_derived_features,
    encode_branch,
    encode_trigger,
    encode_target,
)
from model.predict import predict_single, predict_batch

# ===========================================================================
# 1. DATA GENERATION TESTS
# ===========================================================================


class TestDataGeneration:
    """Tests for ingestion/fetch_logs.py"""

    def test_generates_correct_record_count(self, raw_df):
        assert len(raw_df) == 100

    def test_all_required_columns_present(self, raw_df):
        expected = {
            "build_id", "project_name", "branch", "commit_hash", "author",
            "timestamp", "build_trigger", "num_files_changed", "lines_added",
            "lines_deleted", "test_count", "test_pass_count", "test_fail_count",
            "build_duration_seconds", "log_snippet", "status",
        }
        assert expected.issubset(set(raw_df.columns))

    def test_status_values_are_valid(self, raw_df):
        assert set(raw_df["status"].unique()).issubset({"success", "failure"})

    def test_no_null_values(self, raw_df):
        assert raw_df.isnull().sum().sum() == 0

    def test_build_trigger_values_valid(self, raw_df):
        assert set(raw_df["build_trigger"].unique()).issubset(
            {"push", "pull_request", "schedule"}
        )

    def test_test_pass_plus_fail_equals_total(self, raw_df):
        assert (raw_df["test_pass_count"] + raw_df["test_fail_count"] == raw_df["test_count"]).all()

    def test_failure_rate_is_reasonable(self, raw_df):
        rate = (raw_df["status"] == "failure").mean()
        assert 0.05 <= rate <= 0.70, f"Failure rate {rate:.2%} out of expected range"

    def test_commit_hash_is_40_chars(self):
        h = generate_commit_hash()
        assert len(h) == 40
        assert all(c in "0123456789abcdef" for c in h)

    def test_build_ids_are_unique(self, raw_df):
        assert raw_df["build_id"].nunique() == len(raw_df)

    def test_reproducibility_with_same_seed(self):
        df1 = generate_synthetic_data(num_records=50, seed=42)
        df2 = generate_synthetic_data(num_records=50, seed=42)
        pd.testing.assert_frame_equal(df1, df2)

    def test_different_seeds_give_different_data(self):
        df1 = generate_synthetic_data(num_records=50, seed=1)
        df2 = generate_synthetic_data(num_records=50, seed=2)
        assert not df1["build_id"].equals(df2["build_id"]) or \
               not df1["status"].equals(df2["status"])


# ===========================================================================
# 2. FEATURE ENGINEERING TESTS
# ===========================================================================


class TestFeatureEngineering:
    """Tests for features/build_features.py"""

    def test_output_has_expected_columns(self, features_df):
        expected = [
            "num_files_changed", "lines_added", "lines_deleted",
            "test_count", "test_pass_count", "test_fail_count",
            "build_duration_seconds", "hour", "day_of_week",
            "is_late_night", "is_weekend", "total_lines_changed",
            "lines_per_file", "test_fail_ratio",
            "branch_is_hotfix", "branch_is_bugfix",
            "branch_is_feature", "branch_is_release",
            "trigger_is_push", "trigger_is_schedule", "failed",
        ]
        assert list(features_df.columns) == expected

    def test_all_columns_numeric(self, features_df):
        for col in features_df.columns:
            assert pd.api.types.is_numeric_dtype(features_df[col]), \
                f"Column '{col}' is not numeric"

    def test_no_null_values_in_features(self, features_df):
        assert features_df.isnull().sum().sum() == 0

    def test_binary_columns_only_0_or_1(self, features_df):
        binary_cols = [
            "is_late_night", "is_weekend",
            "branch_is_hotfix", "branch_is_bugfix",
            "branch_is_feature", "branch_is_release",
            "trigger_is_push", "trigger_is_schedule", "failed",
        ]
        for col in binary_cols:
            unique = set(features_df[col].unique())
            assert unique.issubset({0, 1}), f"Column '{col}' has values: {unique}"

    def test_total_lines_changed_is_sum(self, features_df):
        expected = features_df["lines_added"] + features_df["lines_deleted"]
        pd.testing.assert_series_equal(
            features_df["total_lines_changed"], expected,
            check_names=False
        )

    def test_test_fail_ratio_within_bounds(self, features_df):
        assert (features_df["test_fail_ratio"] >= 0).all()
        assert (features_df["test_fail_ratio"] <= 1).all()

    def test_hour_within_bounds(self, features_df):
        assert features_df["hour"].between(0, 23).all()

    def test_day_of_week_within_bounds(self, features_df):
        assert features_df["day_of_week"].between(0, 6).all()

    def test_temporal_features_added(self, raw_csv_path):
        df = pd.read_csv(raw_csv_path)
        df_dropped = df.drop(columns=["build_id", "commit_hash", "author", "log_snippet", "project_name"])
        result = add_temporal_features(df_dropped.copy())
        assert "hour" in result.columns
        assert "day_of_week" in result.columns
        assert "is_late_night" in result.columns
        assert "is_weekend" in result.columns
        assert "timestamp" not in result.columns

    def test_derived_features_added(self, raw_csv_path):
        df = pd.read_csv(raw_csv_path)
        result = add_derived_features(df.copy())
        assert "total_lines_changed" in result.columns
        assert "lines_per_file" in result.columns
        assert "test_fail_ratio" in result.columns

    def test_branch_encoding_drops_original(self, raw_csv_path):
        df = pd.read_csv(raw_csv_path)
        result = encode_branch(df.copy())
        assert "branch" not in result.columns
        for flag in ["branch_is_hotfix", "branch_is_bugfix", "branch_is_feature", "branch_is_release"]:
            assert flag in result.columns

    def test_trigger_encoding_drops_original(self, raw_csv_path):
        df = pd.read_csv(raw_csv_path)
        result = encode_trigger(df.copy())
        assert "build_trigger" not in result.columns
        assert "trigger_is_push" in result.columns
        assert "trigger_is_schedule" in result.columns

    def test_target_encoding_binary(self, raw_csv_path):
        df = pd.read_csv(raw_csv_path)
        result = encode_target(df.copy())
        assert "failed" in result.columns
        assert "status" not in result.columns
        assert set(result["failed"].unique()).issubset({0, 1})

    def test_record_count_preserved(self, raw_df, features_df):
        assert len(features_df) == len(raw_df)


# ===========================================================================
# 3. MODEL PREDICTION TESTS
# ===========================================================================


class TestModelPrediction:
    """Tests for model/predict.py using the session-scoped trained model."""

    def test_model_trains_successfully(self, trained_model):
        model, name = trained_model
        assert model is not None
        assert name in ("RandomForest", "LogisticRegression")

    def test_predict_single_returns_correct_keys(self, trained_model, high_risk_features):
        model, _ = trained_model
        result = predict_single(model, high_risk_features)
        assert set(result.keys()) == {"prediction", "label", "failure_probability"}

    def test_predict_single_prediction_is_binary(self, trained_model, high_risk_features):
        model, _ = trained_model
        result = predict_single(model, high_risk_features)
        assert result["prediction"] in (0, 1)

    def test_predict_single_label_matches_prediction(self, trained_model, high_risk_features):
        model, _ = trained_model
        result = predict_single(model, high_risk_features)
        expected_label = "failure" if result["prediction"] == 1 else "success"
        assert result["label"] == expected_label

    def test_failure_probability_between_0_and_1(self, trained_model, high_risk_features):
        model, _ = trained_model
        result = predict_single(model, high_risk_features)
        assert 0.0 <= result["failure_probability"] <= 1.0

    def test_missing_feature_raises_value_error(self, trained_model, high_risk_features):
        model, _ = trained_model
        incomplete = {k: v for k, v in high_risk_features.items() if k != "hour"}
        with pytest.raises(ValueError, match="Missing features"):
            predict_single(model, incomplete)

    def test_batch_prediction_adds_columns(self, trained_model, features_df):
        model, _ = trained_model
        feature_cols = [c for c in features_df.columns if c != "failed"]
        result = predict_batch(model, features_df[feature_cols])
        assert "prediction" in result.columns
        assert "failure_probability" in result.columns

    def test_batch_prediction_row_count_matches(self, trained_model, features_df):
        model, _ = trained_model
        feature_cols = [c for c in features_df.columns if c != "failed"]
        result = predict_batch(model, features_df[feature_cols])
        assert len(result) == len(features_df)

    def test_high_risk_predicts_failure(self, trained_model, high_risk_features):
        """A hotfix with many failures at 11pm should have high failure probability."""
        model, _ = trained_model
        result = predict_single(model, high_risk_features)
        assert result["failure_probability"] > 0.5, \
            f"Expected high-risk build to have failure_probability > 0.5, got {result['failure_probability']}"

    def test_low_risk_predicts_success(self, trained_model, low_risk_features):
        """A clean daytime feature branch with 0 test failures should predict success."""
        model, _ = trained_model
        result = predict_single(model, low_risk_features)
        assert result["failure_probability"] < 0.5, \
            f"Expected low-risk build to have failure_probability < 0.5, got {result['failure_probability']}"


# ===========================================================================
# 4. API ENDPOINT TESTS
# ===========================================================================


class TestAPIEndpoints:
    """Integration tests for api/main.py using FastAPI's TestClient."""

    # ---- GET /health ----

    def test_health_returns_200(self, api_client):
        resp = api_client.get("/health")
        assert resp.status_code == 200

    def test_health_response_has_required_keys(self, api_client):
        resp = api_client.get("/health")
        body = resp.json()
        for key in ("status", "model_loaded", "model_name", "uptime_seconds", "timestamp"):
            assert key in body, f"Missing key: {key}"

    def test_health_status_is_ok(self, api_client):
        resp = api_client.get("/health")
        assert resp.json()["status"] == "ok"

    def test_health_model_is_loaded(self, api_client):
        resp = api_client.get("/health")
        assert resp.json()["model_loaded"] is True

    def test_health_uptime_is_positive(self, api_client):
        resp = api_client.get("/health")
        assert resp.json()["uptime_seconds"] >= 0

    # ---- GET /model-info ----

    def test_model_info_returns_200(self, api_client):
        resp = api_client.get("/model-info")
        assert resp.status_code == 200

    def test_model_info_has_required_keys(self, api_client):
        resp = api_client.get("/model-info")
        body = resp.json()
        for key in ("model_name", "best_f1_score", "trained_at", "feature_names", "feature_count"):
            assert key in body, f"Missing key: {key}"

    def test_model_info_feature_count_is_20(self, api_client):
        resp = api_client.get("/model-info")
        assert resp.json()["feature_count"] == 20

    # ---- POST /predict ----

    def test_predict_high_risk_returns_200(self, api_client, high_risk_features):
        resp = api_client.post("/predict", json=high_risk_features)
        assert resp.status_code == 200

    def test_predict_response_schema(self, api_client, high_risk_features):
        resp = api_client.post("/predict", json=high_risk_features)
        body = resp.json()
        for key in ("prediction", "label", "failure_probability", "risk_level",
                    "model_name", "predicted_at"):
            assert key in body, f"Missing key: {key}"

    def test_predict_high_risk_label_is_failure(self, api_client, high_risk_features):
        resp = api_client.post("/predict", json=high_risk_features)
        assert resp.json()["label"] == "failure"

    def test_predict_low_risk_label_is_success(self, api_client, low_risk_features):
        resp = api_client.post("/predict", json=low_risk_features)
        assert resp.json()["label"] == "success"

    def test_predict_probability_in_range(self, api_client, high_risk_features):
        resp = api_client.post("/predict", json=high_risk_features)
        prob = resp.json()["failure_probability"]
        assert 0.0 <= prob <= 1.0

    def test_predict_risk_level_valid_values(self, api_client, high_risk_features):
        resp = api_client.post("/predict", json=high_risk_features)
        assert resp.json()["risk_level"] in ("low", "medium", "high")

    def test_predict_high_risk_level_is_high(self, api_client, high_risk_features):
        resp = api_client.post("/predict", json=high_risk_features)
        assert resp.json()["risk_level"] == "high"

    def test_predict_low_risk_level_is_low(self, api_client, low_risk_features):
        resp = api_client.post("/predict", json=low_risk_features)
        assert resp.json()["risk_level"] == "low"

    def test_predict_missing_field_returns_422(self, api_client, high_risk_features):
        """FastAPI should return 422 Unprocessable Entity for missing required fields."""
        incomplete = {k: v for k, v in high_risk_features.items() if k != "hour"}
        resp = api_client.post("/predict", json=incomplete)
        assert resp.status_code == 422

    def test_predict_invalid_hour_returns_422(self, api_client, high_risk_features):
        """hour must be 0-23; value 99 should fail schema validation."""
        bad = {**high_risk_features, "hour": 99}
        resp = api_client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_predict_negative_files_returns_422(self, api_client, high_risk_features):
        """num_files_changed must be >= 1."""
        bad = {**high_risk_features, "num_files_changed": -1}
        resp = api_client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_docs_endpoint_accessible(self, api_client):
        """Swagger UI should be served at /docs."""
        resp = api_client.get("/docs")
        assert resp.status_code == 200
