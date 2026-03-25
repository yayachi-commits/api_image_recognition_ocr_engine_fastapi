# ============================================================================
# OCR Engine - Dockerfile sécurisé
# ============================================================================
FROM python:3.12-slim

# Labels métadonnées
LABEL maintainer="OCR Engine Team" \
      version="1.0.0" \
      description="FastAPI OCR Engine with PaddleOCR"

# Installation des dépendances avec ccache
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libsm6 \
    libxext6 \
    libglib2.0-0 \
    libgl1 \
    ccache \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configuration de ccache pour les compilations C/C++
ENV CC="ccache gcc" \
    CXX="ccache g++" \
    CCACHE_DIR=/tmp/ccache \
    CCACHE_MAXSIZE=1G

# Créer répertoire ccache
RUN mkdir -p /tmp/ccache && chmod 755 /tmp/ccache

# Variables d'environnement Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True

WORKDIR /app

# Copier requirements et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Créer utilisateur non-root
RUN useradd -m -u 1001 -s /sbin/nologin appuser

# Créer répertoires avec permissions correctes
RUN mkdir -p /app/outputs && \
    chmod 755 /app && \
    chmod 755 /app/outputs && \
    chown -R appuser:root /app

# Copier l'application
COPY --chown=appuser:root app /app/app
COPY --chown=appuser:root .env.example /app/.env

# Restreindre les permissions sur l'application
RUN find /app/app -type f -exec chmod 644 {} \; && \
    find /app/app -type d -exec chmod 755 {} \; && \
    chmod 600 /app/.env

# Basculer vers utilisateur non-root
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
