# Dockerfile - Améliorations de Sécurité et Optimisations

## 📋 Résumé des Changements

Ce Dockerfile a été optimisé selon les meilleures pratiques Docker et de sécurité, avec un approche simple et directe.

---

## 🔐 2. Sécurité et Contrôle d'Accès

### Utilisateur Non-Root
```dockerfile
RUN useradd -m -u 1001 -s /sbin/nologin appuser
USER appuser
```

**Avantages**:
- ✅ L'application s'exécute avec des permissions minimales
- ✅ Prévient les escalades de privilèges
- ✅ Si un attaquant compromet l'app, il n'a pas accès root

### Restrictions de Permissions
```dockerfile
# Fichiers d'application: 644 (lecture seule)
find /app -type f -exec chmod 644 {} \;

# Répertoires: 755 (exécution, lecture)
find /app -type d -exec chmod 755 {} \;

# Variables sensibles (.env): 600 (propriétaire uniquement)
chmod 600 /app/.env
```

### Propriété des Fichiers
```dockerfile
COPY --chown=appuser:root app /app/app
```

---

## ⚡ 3. Optimisation avec ccache

### Configuration
```dockerfile
ENV CC="ccache gcc" \
    CXX="ccache g++" \
    CCACHE_DIR=/tmp/ccache \
    CCACHE_MAXSIZE=1G
```

### Bénéfices:
- ✅ Cache des compilations C/C++ (Cython, extensions natives)
- ✅ Réduit le temps de build lors des dépendances mises à jour
- ✅ Pas stocké dans l'image finale (stage builder)

---

## 🐳 4. Bonnes Pratiques Docker

### Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1
```

**Avantages**:
- Docker détecte automatiquement si l'application est en bonne santé
- Redémarrage automatique en cas de problème
- Utile pour l'orchestration (Kubernetes, Swarm)

### Variables d'Environnement
```dockerfile
ENV PYTHONUNBUFFERED=1        # Logs immédiats
ENV PYTHONDONTWRITEBYTECODE=1 # Pas de cache bytecode
```

### Labels Métadonnées
```dockerfile
LABEL maintainer="OCR Engine Team" \
      version="1.0.0" \
      description="FastAPI OCR Engine with PaddleOCR"
```

### Installation Minimaliste
```dockerfile
apt-get install -y --no-install-recommends
apt-get clean && rm -rf /var/lib/apt/lists/*
```

- `--no-install-recommends`: Installe seulement les dépendances obligatoires
- `apt-get clean`: Nettoie le cache apt
- `rm -rf /var/lib/apt/lists/*`: Supprime les listes de paquets

---

## 📊 Comparaison Avant/Après

| Aspect | Avant | Après |
|--------|-------|-------|
| **Utilisateur** | root | appuser (1001) |
| **Permissions .env** | 644 (exposé) | 600 (sécurisé) |
| **Permissions venv** | Par défaut | Restreintes (755/644) |
| **Health check** | Aucun | Configuré |
| **Labels** | Aucun | Complets |
| **ccache** | Non | Oui |
| **PYTHONDONTWRITEBYTECODE** | Non | Oui |

---

## 🚀 Utilisation

### Build avec BuildKit (recommandé)
```bash
DOCKER_BUILDKIT=1 docker build -t ocr-engine:latest .
```

### Exécution
```bash
docker run -d \
  -p 8000:8000 \
  --name ocr-engine \
  ocr-engine:latest
```

### Vérifier la santé
```bash
docker ps
# STATUS: Up X seconds (healthy)
```

---

## 🔍 Vérifications de Sécurité

### Vérifier l'utilisateur
```bash
docker run ocr-engine:latest whoami
# appuser
```

### Vérifier les permissions
```bash
docker run ocr-engine:latest ls -la /app/.env
# -rw------- 1 appuser root 123 date .env
```

### Vérifier l'absence de compilation
```bash
docker run ocr-engine:latest which gcc
# (ne trouve rien - gcc n'est pas installé)
```

---

## 📝 Notes Importantes

1. **Base Image**: `python:3.12-slim` au lieu de `python:3.12-full`
   - Exclut les paquets inutiles (450MB+)

2. **Ca-certificates**: Installé explicitement
   - Nécessaire pour les requêtes HTTPS

3. **PYTHONDONTWRITEBYTECODE=1**: Réduit l'I/O
   - Moins de fichiers `.pyc` créés

4. **Healthcheck**: Nécessite que l'endpoint `/health` existe
   - Assurez-vous que votre app le fournit

---

## 🔗 Ressources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Security](https://docs.docker.com/engine/security/)
- [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [ccache Documentation](https://ccache.dev/)
