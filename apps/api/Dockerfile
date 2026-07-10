# Production image for the FastAPI API and the Arq worker (same image, different command).
# Multi-stage: build wheels in a full image, run on a slim non-root runtime.

# ---- builder ----------------------------------------------------------------
FROM python:3.13-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Build tooling only lives in the builder layer, never in the runtime image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install into an isolated prefix we can copy wholesale into the runtime stage.
COPY requirements.txt ./
RUN pip install --prefix=/install -r requirements.txt

# ---- runtime ----------------------------------------------------------------
FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Run as an unprivileged user.
RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

# Copy the resolved dependencies into /usr/local so they land on Python's sys.path
# (Python's prefix is /usr/local; a bare /install prefix would not be importable).
COPY --from=builder /install /usr/local
COPY . .

USER appuser

EXPOSE 8000

# Container-level liveness (platforms with HTTP checks use /health directly).
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request,sys; \
url=f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health'; \
sys.exit(0 if urllib.request.urlopen(url,timeout=4).status==200 else 1)"

# Default command runs the API. The worker process overrides this (see fly.toml / compose).
# Shell form so ${PORT} is expanded by the platform at runtime.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips="*"
