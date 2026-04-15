"""
dvc_metrics.py - DVC Metrics Export

Purpose:
    Run the evaluation pipeline and write the resulting metrics to
    `metrics.json` so DVC can track them across experiments.

Usage:
    python scripts/dvc_metrics.py
"""

import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from model.evaluate import run_evaluation

OUTPUT_PATH = os.path.join(PROJECT_ROOT, "metrics.json")


def export_metrics() -> dict:
    """Run evaluation, serialize key metrics to JSON for DVC."""
    metrics = run_evaluation()

    # Flat, numeric-only payload — easier for DVC diff / experiments
    dvc_metrics = {
        "accuracy": metrics["accuracy"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1_score": metrics["f1_score"],
        "roc_auc": metrics["roc_auc"],
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(dvc_metrics, f, indent=2)

    print(f"\nMetrics written to: {OUTPUT_PATH}")
    return dvc_metrics


if __name__ == "__main__":
    export_metrics()
