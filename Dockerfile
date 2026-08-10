# syntax=docker/dockerfile:1.6
# ── AEO Agent — production-ready container image ────────────────────────
# Multi-stage build: small runtime, no build deps in the final image.

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps (only what's strictly required)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better Docker layer caching)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application
COPY . .

# Create the runtime data dirs the app expects
RUN mkdir -p /app/data /app/logs /app/reports

# Run as a non-root user for security
RUN useradd --create-home --uid 1000 aeo \
    && chown -R aeo:aeo /app
USER aeo

EXPOSE 5000

# Health check hits the new /api/health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:5000/api/health || exit 1

CMD ["python", "main.py"]
