# syntax=docker/dockerfile:1.7

# ── Builder ──────────────────────────────────────────────

FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# ── Runtime ──────────────────────────────────────────────

FROM python:3.12-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi8 \
    shared-mime-info \
    fonts-dejavu-core \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r finops \
    && useradd -r -g finops -u 10001 finops

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages \
    /usr/local/lib/python3.12/site-packages

COPY --from=builder /usr/local/bin /usr/local/bin

COPY app ./app
COPY pyproject.toml README.md ./

RUN mkdir -p /app/data/reports \
    && chown -R finops:finops /app

USER finops

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    REPORT_OUTPUT_DIR=/app/data/reports

EXPOSE 8000

HEALTHCHECK --interval=30s \
    --timeout=5s \
    --start-period=15s \
    --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]