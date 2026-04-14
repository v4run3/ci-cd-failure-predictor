# CI/CD Workflows

The GitHub Actions workflows have been created. Note that GitHub requires workflow files to live strictly in `.github/workflows/` at the root of the repository, therefore the files have been placed there rather than directly inside this `ci-cd/` directory.

## Workflows Added

1. **`.github/workflows/test.yml`**: Triggers on push or PR to `main`. It initializes the environment, generates the dataset, trains the model, and runs `pytest` on the test suite.
2. **`.github/workflows/docker.yml`**: Triggers on push to `main`. It automatically generates the model, builds the Docker container, and publishes it directly to Docker Hub using your configured `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` action secrets.
3. **`.github/workflows/retrain.yml`**: Set up on a schedule (Runs weekly at midnight on Sunday). This will execute `scripts/retrain.py` to simulate automatic model retraining.

## Local Testing
If you ever want to test these workflows locally before pushing, consider using a tool like [act](https://github.com/nektos/act).
