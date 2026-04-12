"""
main.py - REST API Service for CI/CD Failure Predictor

Purpose:
    Expose a FastAPI REST API to serve build failure predictions.
    Loads the trained Random Forest model on startup and provides:
      - POST /predict  : accepts build metadata, returns failure probability
      - GET  /health   : health check endpoint (model + API status)
      - GET  /model-info : metadata about the loaded model

Usage:
    uvicorn api.main:app --reload
    OR
    python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""

import json
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime

import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "model", "saved_model.pkl")
METADATA_PATH = os.path.join(BASE_DIR, "model", "training_metadata.json")

# ---------------------------------------------------------------------------
# Global state (populated on startup)
# ---------------------------------------------------------------------------

model_store: dict = {}


# ---------------------------------------------------------------------------
# Lifespan — load model once on startup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML model and metadata on startup; release on shutdown."""
    print("[STARTUP] Starting CI/CD Failure Predictor API...")

    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(
            f"Model file not found at {MODEL_PATH}. "
            "Run 'python model/train.py' first."
        )

    model_store["model"] = joblib.load(MODEL_PATH)
    model_store["loaded_at"] = datetime.now().isoformat()

    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH) as f:
            model_store["metadata"] = json.load(f)
    else:
        model_store["metadata"] = {}

    print(f"[OK] Model loaded: {model_store['metadata'].get('model_name', 'unknown')}")
    print(f"     F1-score     : {model_store['metadata'].get('best_f1_score', 'N/A')}")
    print(f"     Trained at   : {model_store['metadata'].get('trained_at', 'N/A')}")
    print("[READY] API is live.\n")

    yield  # API runs here

    model_store.clear()
    print("[SHUTDOWN] API shutting down.")


# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CI/CD Failure Predictor API",
    description=(
        "A machine learning API that predicts the probability of a CI/CD build "
        "failing based on build metadata such as files changed, test results, "
        "branch type, and time of day."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Allow all origins for local development / CI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response schemas (Pydantic)
# ---------------------------------------------------------------------------


class BuildFeatures(BaseModel):
    """Input schema — all 20 engineered features used by the trained model."""

    # Raw build metrics
    num_files_changed: int = Field(..., ge=1, le=500, example=8,
                                   description="Number of files changed in the commit")
    lines_added: int = Field(..., ge=0, example=120,
                             description="Total lines added")
    lines_deleted: int = Field(..., ge=0, example=30,
                               description="Total lines deleted")

    # Test metrics
    test_count: int = Field(..., ge=0, example=200,
                            description="Total number of tests in the build")
    test_pass_count: int = Field(..., ge=0, example=198,
                                 description="Number of tests that passed")
    test_fail_count: int = Field(..., ge=0, example=2,
                                 description="Number of tests that failed")
    build_duration_seconds: int = Field(..., ge=0, example=240,
                                        description="Build duration in seconds")

    # Temporal features (derived from timestamp)
    hour: int = Field(..., ge=0, le=23, example=14,
                      description="Hour of day the build was triggered (0-23)")
    day_of_week: int = Field(..., ge=0, le=6, example=2,
                             description="Day of week (0=Monday, 6=Sunday)")
    is_late_night: int = Field(..., ge=0, le=1, example=0,
                               description="1 if hour >= 22 or hour <= 5, else 0")
    is_weekend: int = Field(..., ge=0, le=1, example=0,
                            description="1 if Saturday or Sunday, else 0")

    # Derived features
    total_lines_changed: int = Field(..., ge=0, example=150,
                                     description="lines_added + lines_deleted")
    lines_per_file: float = Field(..., ge=0.0, example=18.75,
                                  description="total_lines_changed / num_files_changed")
    test_fail_ratio: float = Field(..., ge=0.0, le=1.0, example=0.01,
                                   description="test_fail_count / test_count")

    # Branch type flags (one-hot, baseline = main/develop)
    branch_is_hotfix: int = Field(..., ge=0, le=1, example=0)
    branch_is_bugfix: int = Field(..., ge=0, le=1, example=0)
    branch_is_feature: int = Field(..., ge=0, le=1, example=1)
    branch_is_release: int = Field(..., ge=0, le=1, example=0)

    # Trigger type flags (one-hot, baseline = pull_request)
    trigger_is_push: int = Field(..., ge=0, le=1, example=0)
    trigger_is_schedule: int = Field(..., ge=0, le=1, example=0)


FEATURE_ORDER = [
    "num_files_changed", "lines_added", "lines_deleted",
    "test_count", "test_pass_count", "test_fail_count",
    "build_duration_seconds",
    "hour", "day_of_week", "is_late_night", "is_weekend",
    "total_lines_changed", "lines_per_file", "test_fail_ratio",
    "branch_is_hotfix", "branch_is_bugfix", "branch_is_feature", "branch_is_release",
    "trigger_is_push", "trigger_is_schedule",
]


class PredictionResponse(BaseModel):
    """Output schema for POST /predict."""

    prediction: int = Field(..., description="Binary outcome: 1 = failure, 0 = success")
    label: str = Field(..., description="Human-readable label: 'failure' or 'success'")
    failure_probability: float = Field(..., description="Probability of build failure (0.0 – 1.0)")
    risk_level: str = Field(..., description="'low' | 'medium' | 'high'")
    model_name: str = Field(..., description="Name of the model used")
    predicted_at: str = Field(..., description="ISO-8601 timestamp of prediction")


class HealthResponse(BaseModel):
    """Output schema for GET /health."""

    status: str
    model_loaded: bool
    model_name: str
    uptime_seconds: float
    timestamp: str


# ---------------------------------------------------------------------------
# Startup time (for uptime calculation)
# ---------------------------------------------------------------------------

_start_time = time.time()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _risk_level(probability: float) -> str:
    """Map failure probability to a human-readable risk tier."""
    if probability < 0.35:
        return "low"
    elif probability < 0.65:
        return "medium"
    return "high"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
def health_check():
    """
    Health check endpoint.

    Returns the API status, whether the model is loaded, and uptime.
    Use this endpoint for Kubernetes liveness/readiness probes.
    """
    return HealthResponse(
        status="ok" if model_store.get("model") is not None else "degraded",
        model_loaded=model_store.get("model") is not None,
        model_name=model_store.get("metadata", {}).get("model_name", "unknown"),
        uptime_seconds=round(time.time() - _start_time, 2),
        timestamp=datetime.now().isoformat(),
    )


@app.get("/model-info", tags=["Monitoring"])
def model_info():
    """
    Return metadata about the currently loaded model.

    Includes: model name, feature list, training date, F1-score, dataset sizes.
    """
    if not model_store.get("metadata"):
        raise HTTPException(status_code=503, detail="Model metadata not available.")
    return {
        "model_name": model_store["metadata"].get("model_name"),
        "best_f1_score": model_store["metadata"].get("best_f1_score"),
        "trained_at": model_store["metadata"].get("trained_at"),
        "train_size": model_store["metadata"].get("train_size"),
        "test_size": model_store["metadata"].get("test_size"),
        "feature_count": len(model_store["metadata"].get("feature_names", [])),
        "feature_names": model_store["metadata"].get("feature_names", []),
        "loaded_at": model_store.get("loaded_at"),
    }


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
def predict(features: BuildFeatures):
    """
    Predict whether a CI/CD build will fail.

    Accepts 20 engineered build features and returns:
    - **prediction**: 0 (success) or 1 (failure)
    - **failure_probability**: model confidence (0.0 – 1.0)
    - **risk_level**: low / medium / high
    - **label**: 'success' or 'failure'

    ### Example high-risk payload
    ```json
    {
      "num_files_changed": 25, "lines_added": 600, "lines_deleted": 200,
      "test_count": 150, "test_pass_count": 130, "test_fail_count": 20,
      "build_duration_seconds": 500, "hour": 23, "day_of_week": 6,
      "is_late_night": 1, "is_weekend": 1, "total_lines_changed": 800,
      "lines_per_file": 32.0, "test_fail_ratio": 0.133,
      "branch_is_hotfix": 1, "branch_is_bugfix": 0, "branch_is_feature": 0,
      "branch_is_release": 0, "trigger_is_push": 1, "trigger_is_schedule": 0
    }
    ```
    """
    model = model_store.get("model")
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Try again shortly.")

    # Build the feature vector in the exact order the model was trained on
    feature_dict = features.model_dump()
    X = [[feature_dict[f] for f in FEATURE_ORDER]]

    prediction = int(model.predict(X)[0])
    probability = float(model.predict_proba(X)[0][1])

    return PredictionResponse(
        prediction=prediction,
        label="failure" if prediction == 1 else "success",
        failure_probability=round(probability, 4),
        risk_level=_risk_level(probability),
        model_name=model_store.get("metadata", {}).get("model_name", "unknown"),
        predicted_at=datetime.now().isoformat(),
    )
