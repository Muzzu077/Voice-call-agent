# ── Voice Agent Platform API ─────────────────────
# Multi-stage build for production-ready FastAPI backend
FROM python:3.12-slim AS base

# System deps for audio processing + postgres
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Dependencies ─────────────────────────────────
FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application ──────────────────────────────────
FROM deps AS app
COPY . .

# Create data directories
RUN mkdir -p /app/data

EXPOSE 8000

# Use uvicorn with auto-reload disabled for production
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
