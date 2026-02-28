FROM python:3.12-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
RUN groupadd -r mlservice && useradd -r -g mlservice mlservice
COPY --chown=mlservice:mlservice . .
# Create models directory for serialized classifier
RUN mkdir -p app/models/phishing_classifier && chown -R mlservice:mlservice app/models
USER mlservice
EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=10s CMD python -c "import httpx; httpx.get('http://localhost:8001/health').raise_for_status()"
