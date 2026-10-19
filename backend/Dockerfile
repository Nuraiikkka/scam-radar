FROM python:3.11-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_DEFAULT_TIMEOUT=120
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements /tmp/requirements
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --retries 10 --extra-index-url https://download.pytorch.org/whl/cpu -r /tmp/requirements/base.txt
ARG REQUIREMENTS=prod.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --retries 10 --extra-index-url https://download.pytorch.org/whl/cpu -r /tmp/requirements/${REQUIREMENTS}

FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    SCAMRADAR_MEDIA_DIR=/data/media \
    SCAMRADAR_LOGS_DIR=/data/logs \
    SCAMRADAR_MODEL_CACHE_DIR=/models/cache \
    HF_HOME=/models/cache/huggingface
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libgl1 libglib2.0-0 curl fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --home /app --shell /usr/sbin/nologin app \
    && mkdir -p /app /data/media /data/logs /models/cache \
    && chown -R app:app /app /data /models
COPY --from=builder /opt/venv /opt/venv
WORKDIR /app
COPY --chown=app:app . /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=120s --retries=5 \
    CMD curl -fsS http://127.0.0.1:8000/api/v1/health || exit 1
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["api"]
