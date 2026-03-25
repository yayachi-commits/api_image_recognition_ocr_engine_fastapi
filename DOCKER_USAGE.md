# Guide d'Utilisation Docker

## Démarrage rapide

### Préparer le dossier de sortie
```bash
mkdir -p outputs
```

### Build et lancement avec Docker Compose
```bash
docker compose up --build
```

### Build et lancement avec Docker uniquement
```bash
docker build \
  --build-arg OCR_LANGUAGE=fr \
  --build-arg PRELOAD_PADDLE_MODELS=true \
  -t ocr-engine:latest .

docker run -d \
  -p 8000:8000 \
  --name ocr-engine \
  -e OCR_DEVICE=cpu \
  -e OCR_LANGUAGE=fr \
  -e OUTPUT_DIR=/app/outputs \
  -v "$(pwd)/outputs:/app/outputs" \
  ocr-engine:latest
```

Le build précharge les modèles PaddleOCR pour que le conteneur puisse démarrer avec un système de fichiers racine en lecture seule.

## Vérifications

### Vérifier l'utilisateur
```bash
docker compose exec ocr-engine whoami
```

### Vérifier le healthcheck
```bash
docker compose ps
curl http://localhost:8000/health
```

### Tester l'API OCR
```bash
curl -X POST http://localhost:8000/api/v1/ocr/process \
  -F "file=@/path/to/image.jpg"
```

## Configuration

### Variables d'environnement utiles
```yaml
environment:
  OCR_DEVICE: cpu
  OCR_LANGUAGE: fr
  OUTPUT_DIR: /app/outputs
  PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK: "True"
  XDG_CACHE_HOME: /tmp/.cache
  MPLCONFIGDIR: /tmp/matplotlib
```

Si vous changez `OCR_LANGUAGE`, reconstruisez l'image avec le même `--build-arg OCR_LANGUAGE=...` afin d'embarquer les bons modèles PaddleOCR dans l'image.

## Sécurité appliquée

- Utilisateur non-root dans l'image finale
- Image multistage pour garder les outils de build hors du runtime
- Root filesystem en lecture seule dans `docker-compose.yml`
- Toutes les capabilities Linux supprimées
- `no-new-privileges` activé
- Cache et fichiers temporaires déplacés dans `/tmp`

## Dépannage

### Voir les logs
```bash
docker compose logs -f ocr-engine
```

### Ouvrir un shell dans le conteneur
```bash
docker compose exec ocr-engine /bin/sh
```

### Reconstruire sans préchargement des modèles
```bash
docker build \
  --build-arg OCR_LANGUAGE=fr \
  --build-arg PRELOAD_PADDLE_MODELS=false \
  -t ocr-engine:latest .
```

Dans ce mode, si les modèles ne sont pas déjà présents dans l'image, PaddleOCR tentera de les récupérer au runtime.
