# ── Backend Dockerfile ─────────────────────────────────────
# Multi-stage build: builder installs deps, runtime is minimal
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime Stage ──────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages
COPY --from=builder /install /usr/local

# Non-root user for security
RUN groupadd -r campusshield && useradd -r -g campusshield campusshield
COPY --chown=campusshield:campusshield . .

USER campusshield

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"
