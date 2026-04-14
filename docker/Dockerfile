# =============================================================================
# Dockerfile — CI/CD Failure Predictor API
# =============================================================================
#
# Purpose:
#   Containerize the FastAPI prediction service so it runs consistently
#   across any environment (local, CI, cloud, Kubernetes).
#
# Build context: project root  (docker build -f docker/Dockerfile .)
#
# Multi-stage build:
#   Stage 1 (builder) — install Python deps into a clean venv
#   Stage 2 (runtime) — copy only what is needed; no build tools in image
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: builder — install dependencies
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

# Prevent .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build essentials (needed by some Python C-extensions)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements first — Docker layer caching means this layer is
# only rebuilt when requirements change, not when source code changes.
COPY requirements.txt .

# Install into an isolated venv inside the builder stage
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: runtime — lean final image
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Put venv on PATH so `python` and `uvicorn` resolve to venv binaries
    PATH="/opt/venv/bin:$PATH" \
    # API host/port — override at runtime with -e PORT=8080
    PORT=8000

# Copy the pre-built venv from the builder stage (no gcc needed at runtime)
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# ---------------------------------------------------------------------------
# Copy application source
# Only the modules the API actually imports are needed at runtime.
# ---------------------------------------------------------------------------
COPY api/          ./api/
COPY model/        ./model/
COPY ingestion/    ./ingestion/
COPY features/     ./features/
COPY data/         ./data/

# ---------------------------------------------------------------------------
# Security: run as a non-root user
# ---------------------------------------------------------------------------
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    chown -R appuser:appgroup /app

USER appuser

# ---------------------------------------------------------------------------
# Health check — Docker / Kubernetes will poll this endpoint
# ---------------------------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c \
    "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" \
    || exit 1

# Expose the API port
EXPOSE ${PORT}

# ---------------------------------------------------------------------------
# Entrypoint — start Uvicorn, binding to all interfaces inside the container
# ---------------------------------------------------------------------------
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
