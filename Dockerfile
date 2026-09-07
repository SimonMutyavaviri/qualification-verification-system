# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# Multi-stage build. The builder compiles wheels so the runtime image needs no
# compiler toolchain, which keeps the final image small and its attack surface
# narrow.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt


# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FLASK_ENV=production \
    PORT=8080 \
    DATA_DIR=/data

# curl backs the HEALTHCHECK; gosu lets the entrypoint drop from root to the
# unprivileged application user after preparing the mounted data volume.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl gosu \
    && rm -rf /var/lib/apt/lists/*

# The application process runs as this unprivileged user: a compromise in the
# application must not hand the attacker root inside the container.
RUN useradd --create-home --uid 10001 qvs

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

COPY --chown=qvs:qvs app ./app
COPY --chown=qvs:qvs migrations ./migrations
COPY --chown=qvs:qvs wsgi.py ./
COPY docker-entrypoint.sh ./

RUN chmod +x docker-entrypoint.sh \
    && mkdir -p "$DATA_DIR" \
    && chown qvs:qvs "$DATA_DIR"

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/healthz" || exit 1

# The entrypoint starts as root only long enough to take ownership of a freshly
# attached volume, then execs the application as the qvs user.
ENTRYPOINT ["./docker-entrypoint.sh"]

# Two workers with four threads each: enough concurrency for the expected load
# without over-subscribing a small shared-CPU machine.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", \
     "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
