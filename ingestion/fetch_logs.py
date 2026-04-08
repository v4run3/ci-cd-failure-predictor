"""
fetch_logs.py - CI/CD Log Ingestion Module

Purpose:
    Generate synthetic CI/CD build log data that simulates real pipeline
    output from providers like GitHub Actions, Jenkins, and GitLab CI.
    Produces 1000 build records with realistic failure correlations
    and saves them to data/raw/build_logs.csv.

Usage:
    python ingestion/fetch_logs.py
"""

import random
import hashlib
import os
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

NUM_RECORDS = 1000
RANDOM_SEED = 42
OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw"
)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "build_logs.csv")

PROJECT_NAMES = [
    "frontend-app", "backend-api", "auth-service",
    "payment-gateway", "notification-service", "data-pipeline",
    "mobile-app", "infra-config", "ml-pipeline", "docs-site",
]

BRANCHES = [
    "main", "develop", "feature/login", "feature/checkout",
    "feature/dashboard", "bugfix/auth-error", "bugfix/null-pointer",
    "hotfix/security-patch", "release/v1.2", "release/v2.0",
]

BUILD_TRIGGERS = ["push", "pull_request", "schedule"]
TRIGGER_WEIGHTS = [0.6, 0.3, 0.1]

SUCCESS_SNIPPETS = [
    "All {test_count} tests passed. Build completed successfully.",
    "Compilation successful. Deploying to staging environment.",
    "Linting passed. All checks green. Ready to merge.",
    "Docker image built and pushed to registry. Tag: latest.",
    "Unit tests: {pass_count} passed. Integration tests: OK.",
]

FAILURE_SNIPPETS = [
    "FAILED: {fail_count} test(s) failed. See details above.",
    "ERROR: Build failed at step 'compile'. Exit code 1.",
    "FATAL: Out of memory during test execution. Killed.",
    "ERROR: Dependency resolution failed. Conflicting versions.",
    "FAILED: Linting errors in 3 files. ESLint exit code 1.",
    "ERROR: Docker build failed. Layer 5/8: package not found.",
    "TIMEOUT: Build exceeded maximum duration of 3600s.",
]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def generate_commit_hash() -> str:
    """Generate a realistic 40-character hex SHA-1 commit hash."""
    random_bytes = random.getrandbits(160).to_bytes(20, byteorder="big")
    return hashlib.sha1(random_bytes).hexdigest()


def generate_log_snippet(status: str, test_count: int,
                         pass_count: int, fail_count: int) -> str:
    """Return a realistic CI/CD log snippet correlated with build status."""
    if status == "success":
        template = random.choice(SUCCESS_SNIPPETS)
    else:
        template = random.choice(FAILURE_SNIPPETS)

    return template.format(
        test_count=test_count,
        pass_count=pass_count,
        fail_count=fail_count,
    )


# ---------------------------------------------------------------------------
# Core record generator
# ---------------------------------------------------------------------------


def generate_build_record(build_id: str, fake: Faker,
                          base_date: datetime) -> dict:
    """Generate a single synthetic CI/CD build record.

    Failure probability is computed from the record's own attributes so that
    the resulting dataset contains learnable correlations for ML training.
    """
    # -- Basic metadata --
    project_name = random.choice(PROJECT_NAMES)
    branch = random.choice(BRANCHES)
    commit_hash = generate_commit_hash()
    author = fake.name()
    build_trigger = random.choices(BUILD_TRIGGERS, weights=TRIGGER_WEIGHTS, k=1)[0]

    # -- Timestamp spread over ~90 days --
    day_offset = random.randint(0, 90)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    timestamp = base_date + timedelta(
        days=day_offset, hours=hour, minutes=minute, seconds=second
    )

    # -- Code change metrics --
    num_files_changed = max(1, min(50, int(random.gauss(8, 7))))
    lines_added = num_files_changed * random.randint(5, 50)
    lines_deleted = num_files_changed * random.randint(0, 30)

    # -- Test metrics (test_fail_count set after status decision) --
    test_count = random.randint(20, 500)

    # -- Failure probability (learnable correlations) --
    failure_prob = 0.15  # base rate

    if num_files_changed > 20:
        failure_prob += 0.15
    elif num_files_changed > 10:
        failure_prob += 0.08

    if "hotfix" in branch:
        failure_prob += 0.10
    elif "bugfix" in branch:
        failure_prob += 0.05

    if hour >= 22 or hour <= 5:
        failure_prob += 0.12

    if build_trigger == "schedule":
        failure_prob -= 0.08

    if lines_added + lines_deleted > 1000:
        failure_prob += 0.10

    failure_prob = max(0.05, min(0.85, failure_prob))

    # -- Determine status --
    status = "failure" if random.random() < failure_prob else "success"

    # -- Test failures (correlated with status) --
    if status == "failure":
        test_fail_count = random.randint(1, max(1, test_count // 5))
    else:
        test_fail_count = 0
    test_pass_count = test_count - test_fail_count

    # -- Build duration --
    build_duration_seconds = random.randint(30, 600)
    if status == "failure":
        roll = random.random()
        if roll < 0.4:
            build_duration_seconds += random.randint(100, 300)  # timeout
        elif roll < 0.7:
            build_duration_seconds = random.randint(10, 60)     # fast fail

    # -- Log snippet --
    log_snippet = generate_log_snippet(
        status, test_count, test_pass_count, test_fail_count
    )

    return {
        "build_id": build_id,
        "project_name": project_name,
        "branch": branch,
        "commit_hash": commit_hash,
        "author": author,
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "build_trigger": build_trigger,
        "num_files_changed": num_files_changed,
        "lines_added": lines_added,
        "lines_deleted": lines_deleted,
        "test_count": test_count,
        "test_pass_count": test_pass_count,
        "test_fail_count": test_fail_count,
        "build_duration_seconds": build_duration_seconds,
        "log_snippet": log_snippet,
        "status": status,
    }


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def generate_synthetic_data(num_records: int = NUM_RECORDS,
                            seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Generate synthetic CI/CD build log records.

    Args:
        num_records: Number of build records to generate.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with synthetic build log data sorted by timestamp.
    """
    random.seed(seed)
    Faker.seed(seed)
    fake = Faker()

    base_date = datetime(2024, 1, 1)
    records = []

    for i in range(1, num_records + 1):
        build_id = f"BUILD-{i:04d}"
        record = generate_build_record(build_id, fake, base_date)
        records.append(record)

    df = pd.DataFrame(records)
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def save_to_csv(df: pd.DataFrame, output_path: str = OUTPUT_FILE) -> str:
    """Save DataFrame to CSV file.

    Args:
        df: DataFrame to save.
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
    print("Generating synthetic CI/CD build log data...")
    df = generate_synthetic_data()
    path = save_to_csv(df)

    print(f"Generated {len(df)} records -> {path}")
    print(f"\nStatus distribution:")
    print(df["status"].value_counts().to_string())
    print(f"\nFailure rate: {(df['status'] == 'failure').mean():.1%}")
    print(f"\nSample record:")
    print(df.iloc[0].to_string())
    print(f"\nColumn dtypes:")
    print(df.dtypes.to_string())
