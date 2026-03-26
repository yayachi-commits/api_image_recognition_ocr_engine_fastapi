# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.10

FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

ARG PRELOAD_PADDLE_MODELS=true
ARG PRELOAD_OCR_LANGUAGE=fr

ENV DEBIAN_FRONTEND=noninteractive \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:/usr/lib/ccache:$PATH \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True \
    XDG_CACHE_HOME=/tmp/.cache \
    MPLCONFIGDIR=/tmp/matplotlib \
    CCACHE_DIR=/tmp/ccache

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ccache \
        ca-certificates \
        libgomp1 \
        libsm6 \
        libxext6 \
        libglib2.0-0 \
        libgl1 \
    && update-ccache-symlinks \
    && python -m venv "${VIRTUAL_ENV}" \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install .

RUN mkdir -p /root/.paddleocr \
    && if [ "${PRELOAD_PADDLE_MODELS}" = "true" ]; then \
        python -c "from paddleocr import PPStructure; lang='${PRELOAD_OCR_LANGUAGE}'.lower(); lang = lang if lang in {'en', 'ch'} else 'en'; PPStructure(device='cpu', lang=lang, use_doc_orientation_classify=True, use_doc_unwarping=False, use_textline_orientation=False)"; \
    fi


FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ARG APP_UID=1000
ARG APP_GID=1000

ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:/usr/lib/ccache:$PATH \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True \
    HOME=/home/appuser \
    XDG_CACHE_HOME=/tmp/.cache \
    MPLCONFIGDIR=/tmp/matplotlib \
    OCR_DEVICE=cpu \
    OCR_LANGUAGE=fr \
    OUTPUT_DIR=outputs

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ccache \
        ca-certificates \
        libgomp1 \
        libsm6 \
        libxext6 \
        libglib2.0-0 \
        libgl1 \
    && groupadd --gid "${APP_GID}" appuser \
    && useradd --uid "${APP_UID}" --gid "${APP_GID}" --create-home --home-dir /home/appuser --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/outputs /tmp/.cache /tmp/matplotlib /home/appuser/.paddleocr \
    && chown -R appuser:appuser /app /tmp/.cache /tmp/matplotlib /home/appuser \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder --chown=appuser:appuser /root/.paddleocr /home/appuser/.paddleocr

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
