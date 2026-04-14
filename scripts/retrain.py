"""
retrain.py - Model Retraining Script

Purpose:
    Orchestrate the full retraining pipeline: generate fresh data,
    engineer features, retrain the model, evaluate, and replace
    the serving artifact only if the new model is better.

Usage:
    python scripts/retrain.py
"""

import json
import os
import shutil
import sys
import time

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so imports work from any directory
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from ingestion.fetch_logs import generate_synthetic_data, save_to_csv
from features.build_features import build_features, save_features
from model.train import train_pipeline, MODEL_PATH, METADATA_PATH
from model.evaluate import run_evaluation

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BACKUP_MODEL_PATH = MODEL_PATH + ".bak"
BACKUP_METADATA_PATH = METADATA_PATH + ".bak"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_old_f1() -> float:
    """Read the F1 score from the current training_metadata.json."""
    if not os.path.exists(METADATA_PATH):
        return 0.0
    with open(METADATA_PATH, "r") as f:
        metadata = json.load(f)
    return metadata.get("best_f1_score", 0.0)


def backup_current_model() -> bool:
    """Copy current model and metadata to .bak files. Returns True if backup was made."""
    if not os.path.exists(MODEL_PATH):
        print("  No existing model found — skipping backup.")
        return False
    shutil.copy2(MODEL_PATH, BACKUP_MODEL_PATH)
    if os.path.exists(METADATA_PATH):
        shutil.copy2(METADATA_PATH, BACKUP_METADATA_PATH)
    print("  Backed up current model to .bak files.")
    return True


def restore_backup() -> None:
    """Restore model from .bak files."""
    if os.path.exists(BACKUP_MODEL_PATH):
        shutil.copy2(BACKUP_MODEL_PATH, MODEL_PATH)
    if os.path.exists(BACKUP_METADATA_PATH):
        shutil.copy2(BACKUP_METADATA_PATH, METADATA_PATH)
    print("  Restored previous model from backup.")


def cleanup_backups() -> None:
    """Remove .bak files after a successful retrain."""
    for path in [BACKUP_MODEL_PATH, BACKUP_METADATA_PATH]:
        if os.path.exists(path):
            os.remove(path)


# ---------------------------------------------------------------------------
# Main retraining pipeline
# ---------------------------------------------------------------------------


def retrain() -> None:
    """Run the full retraining pipeline with safe rollback."""

    # ---- Step 1: Back up current model ----
    print("\n[Step 1/5] Backing up current model...")
    old_f1 = load_old_f1()
    had_backup = backup_current_model()
    print(f"  Previous model F1: {old_f1:.4f}")

    # ---- Step 2: Generate fresh data with a new seed ----
    print("\n[Step 2/5] Generating fresh training data...")
    new_seed = int(time.time()) % 100_000
    df_raw = generate_synthetic_data(num_records=1000, seed=new_seed)
    raw_path = save_to_csv(df_raw)
    print(f"  Seed: {new_seed}")
    print(f"  Records: {len(df_raw)}")
    print(f"  Saved to: {raw_path}")

    # ---- Step 3: Engineer features ----
    print("\n[Step 3/5] Engineering features...")
    df_features = build_features()
    features_path = save_features(df_features)
    print(f"  Features: {len(df_features.columns)} columns, {len(df_features)} rows")
    print(f"  Saved to: {features_path}")

    # ---- Step 4: Train new model ----
    print("\n[Step 4/5] Training new model...")
    new_model, model_name = train_pipeline()

    # ---- Step 5: Evaluate and compare ----
    print("\n[Step 5/5] Evaluating new model...")
    metrics = run_evaluation()
    new_f1 = metrics["f1_score"]

    # ---- Decision: keep or rollback ----
    print("\n" + "=" * 60)
    print("RETRAINING SUMMARY")
    print("=" * 60)
    print(f"  Previous F1 : {old_f1:.4f}")
    print(f"  New F1       : {new_f1:.4f}")
    print(f"  Model type   : {model_name}")

    if new_f1 >= old_f1:
        print(f"\n  Result: Model UPDATED (new F1 >= old F1)")
        cleanup_backups()
    elif had_backup:
        print(f"\n  Result: KEEPING PREVIOUS model (new F1 < old F1)")
        restore_backup()
        cleanup_backups()
    else:
        print(f"\n  Result: Keeping new model (no previous model to restore)")

    print("\nRetraining complete.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("CI/CD Failure Predictor - Model Retraining")
    print("=" * 60)
    retrain()
