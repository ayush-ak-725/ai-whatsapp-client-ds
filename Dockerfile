FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps required during build (wheels)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/home/appuser/.cache/huggingface \
    PATH="/home/appuser/.local/bin:$PATH"

WORKDIR /app

# Runtime-only dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install python deps from prebuilt wheels for reproducible, faster builds
COPY --from=builder /wheels /wheels
COPY requirements.txt ./
RUN pip install --no-index --find-links=/wheels -r requirements.txt && \
    rm -rf /wheels

# Optionally pre-download Hugging Face model weights at build time
ARG PRELOAD_HF=0
ARG HF_MODEL_ID=microsoft/DialoGPT-medium
ENV PRELOAD_HF=${PRELOAD_HF}
ENV HF_MODEL_ID=${HF_MODEL_ID}
RUN if [ "$PRELOAD_HF" = "1" ]; then \
      python - <<'PY' \
import os
from transformers import pipeline
model_id = os.getenv('HF_MODEL_ID', 'microsoft/DialoGPT-medium')
pipe = pipeline('text-generation', model=model_id)
pipe('hello', max_length=5)
print('Preloaded Hugging Face model:', model_id)
PY
    fi

# Copy application code
COPY . /app

# Create non-root user and ensure permissions
RUN useradd -m -u 10001 appuser && \
    mkdir -p /app/logs "$HF_HOME" && \
    chown -R appuser:appuser /app "$HF_HOME"

USER appuser

# Expose port
EXPOSE 8000

# Lightweight healthcheck that does not trigger external providers
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD curl -fsS http://127.0.0.1:${PORT:-8000}/api/v1/health || exit 1

# Run the application (configurable workers/port via env)
CMD ["sh","-c","uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${UVICORN_WORKERS:-1} --proxy-headers"]



