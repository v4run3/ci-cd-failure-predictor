"""
build_features.py - Feature Engineering Module

Purpose:
    Transform raw CI/CD build logs into a clean, all-numeric feature set
    suitable for ML model training. Reads from data/raw/build_logs.csv
    and outputs to data/processed/features.csv.

Usage:
    python features/build_features.py
"""

import os

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RAW_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "raw", "build_logs.csv",
)
OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "processed", "features.csv",
)

COLUMNS_TO_DROP = ["build_id", "commit_hash", "author", "log_snippet", "project_name"]

# ---------------------------------------------------------------------------
# Feature engineering functions
# ---------------------------------------------------------------------------


def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract time-based features from the timestamp column.

    Creates: hour, day_of_week, is_late_night, is_weekend.
    Drops the original timestamp column.
    """
    ts = pd.to_datetime(df["timestamp"])
    df["hour"] = ts.dt.hour
    df["day_of_week"] = ts.dt.dayofweek
    df["is_late_night"] = ((df["hour"] >= 22) | (df["hour"] <= 5)).astype(int)
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df = df.drop(columns=["timestamp"])
    return df


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute ratio and aggregate features from raw numeric columns.

    Creates: total_lines_changed, lines_per_file, test_fail_ratio.
    """
    df["total_lines_changed"] = df["lines_added"] + df["lines_deleted"]
    df["lines_per_file"] = (
        df["total_lines_changed"] / df["num_files_changed"]
    ).round(2)
    df["test_fail_ratio"] = (df["test_fail_count"] / df["test_count"]).round(4)
    return df


def encode_branch(df: pd.DataFrame) -> pd.DataFrame:
    """One-hot encode branch type into binary flags.

    Creates: branch_is_hotfix, branch_is_bugfix, branch_is_feature, branch_is_release.
    Baseline (all zeros) = main or develop branches.
    Drops the original branch column.
    """
    branch_prefix = df["branch"].str.split("/").str[0]
    for prefix in ["hotfix", "bugfix", "feature", "release"]:
        df[f"branch_is_{prefix}"] = (branch_prefix == prefix).astype(int)
    df = df.drop(columns=["branch"])
    return df


def encode_trigger(df: pd.DataFrame) -> pd.DataFrame:
    """One-hot encode build trigger into binary flags.

    Creates: trigger_is_push, trigger_is_schedule.
    Baseline (all zeros) = pull_request.
    Drops the original build_trigger column.
    """
    df["trigger_is_push"] = (df["build_trigger"] == "push").astype(int)
    df["trigger_is_schedule"] = (df["build_trigger"] == "schedule").astype(int)
    df = df.drop(columns=["build_trigger"])
    return df


def encode_target(df: pd.DataFrame) -> pd.DataFrame:
    """Convert status to binary target column.

    Creates: failed (1 = failure, 0 = success).
    Drops the original status column.
    """
    df["failed"] = (df["status"] == "failure").astype(int)
    df = df.drop(columns=["status"])
    return df


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def build_features(input_path: str = RAW_DATA_PATH) -> pd.DataFrame:
    """Load raw CSV, apply all feature transforms, return clean numeric DataFrame.

    Pipeline: load -> drop useless columns -> temporal -> derived -> encode -> target.

    Args:
        input_path: Path to raw build_logs.csv.

    Returns:
        DataFrame with all-numeric columns and binary target 'failed'.
    """
    df = pd.read_csv(input_path)
    df = df.drop(columns=COLUMNS_TO_DROP)
    df = add_temporal_features(df)
    df = add_derived_features(df)
    df = encode_branch(df)
    df = encode_trigger(df)
    df = encode_target(df)
    return df


def save_features(df: pd.DataFrame, output_path: str = OUTPUT_PATH) -> str:
    """Save features DataFrame to CSV.

    Args:
        df: Processed features DataFrame.
        output_path: Full path to output CSV file.

    Returns:
        The path where the file was saved.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Building features from raw CI/CD log data...")
    df = build_features()
    path = save_features(df)

    print(f"Saved {len(df)} records with {len(df.columns)} features -> {path}")
    print(f"\nTarget distribution:")
    print(df["failed"].value_counts().to_string())
    print(f"\nFailure rate: {df['failed'].mean():.1%}")
    print(f"\nFeature columns ({len(df.columns)}):")
    print(list(df.columns))
    print(f"\nSample record:")
    print(df.iloc[0].to_string())
