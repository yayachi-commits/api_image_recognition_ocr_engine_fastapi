ARG PYTHON_VERSION=3.10

FROM python:${PYTHON_VERSION}-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    CCACHE_DIR=/tmp/ccache \
    CCACHE_MAXSIZE=1G \
    VIRTUAL_ENV=/opt/venv \
    PATH="/usr/lib/ccache:/opt/venv/bin:${PATH}"

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        ccache \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        libsm6 \
        libxext6 \
        libxrender1 \
    && /usr/sbin/update-ccache-symlinks \
    && mkdir -p "${CCACHE_DIR}" \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv "${VIRTUAL_ENV}"

COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install --upgrade pip setuptools wheel \
    && pip install .

ARG OCR_LANGUAGE=en
ARG PRELOAD_PADDLE_MODELS=true

RUN mkdir -p /root/.paddleocr \
    && if [ "${PRELOAD_PADDLE_MODELS}" = "true" ]; then \
        preload_lang="${OCR_LANGUAGE}"; \
        if [ "${preload_lang}" != "en" ] && [ "${preload_lang}" != "ch" ]; then \
            echo "PPStructure layout models only support en/ch in paddleocr==2.7.0.3; falling back to en for model preload."; \
            preload_lang="en"; \
        fi; \
        python -c "from paddleocr import PPStructure; PPStructure(device='cpu', lang='${preload_lang}', use_doc_orientation_classify=True, use_doc_unwarping=False, use_textline_orientation=False)"; \
    fi


FROM python:${PYTHON_VERSION}-slim AS runtime

LABEL maintainer="OCR Engine Team" \
      org.opencontainers.image.title="image-recognition-ocr-engine" \
      org.opencontainers.image.description="FastAPI OCR Engine with PaddleOCR" \
      org.opencontainers.image.version="1.0.0"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}" \
    HOME=/home/appuser \
    TMPDIR=/tmp \
    XDG_CACHE_HOME=/tmp/.cache \
    MPLCONFIGDIR=/tmp/matplotlib \
    HOST=0.0.0.0 \
    PORT=8000 \
    OCR_DEVICE=cpu \
    OCR_LANGUAGE=en \
    USE_DOC_ORIENTATION_CLASSIFY=true \
    USE_DOC_UNWARPING=false \
    USE_TEXTLINE_ORIENTATION=false \
    PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True \
    OUTPUT_DIR=/app/outputs

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        libsm6 \
        libxext6 \
        libxrender1 \
    && groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --create-home --home-dir /home/appuser --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/outputs /tmp/.cache /tmp/matplotlib \
    && chown -R appuser:app /app/outputs /tmp/.cache /tmp/matplotlib /home/appuser \
    && chmod 755 /app /app/outputs /home/appuser \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder --chown=appuser:app /root/.paddleocr /home/appuser/.paddleocr

RUN find /opt/venv -type d -name "__pycache__" -prune -exec rm -rf {} + \
    && chmod -R a=rX /opt/venv \
    && chmod -R u=rwX,go=rX /home/appuser/.paddleocr

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health', timeout=3).read()" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
