# Dockerfile - Sécurité et Optimisations

## Résumé

Le `Dockerfile` utilise maintenant un build multistage pour séparer clairement :

- le stage `builder`, qui installe les dépendances Python et peut précharger les modèles PaddleOCR
- le stage `runtime`, qui ne contient que ce qui est nécessaire pour exécuter FastAPI + PaddleOCR

## Points de sécurité

### Utilisateur non-root
L'image finale tourne avec `appuser` (`UID 10001`) au lieu de `root`.

### Surface d'attaque réduite
Le stage runtime ne contient pas les outils de compilation utilisés pendant le build.

### Root filesystem compatible lecture seule
Le runtime est prévu pour fonctionner avec :

- le code et l'environnement Python en lecture seule
- les fichiers temporaires dans `/tmp`
- les résultats OCR dans `/app/outputs`

### Capacités Linux minimales
Le `docker-compose.yml` retire toutes les capabilities et active `no-new-privileges`.

## Points de performance

### Multistage
Les dépendances de build restent dans le stage builder, ce qui allège l'image finale.

### Préchargement des modèles PaddleOCR
Le build peut instancier `PPStructure` avec :

- `OCR_LANGUAGE=fr`
- `PRELOAD_PADDLE_MODELS=true`

Cela permet d'embarquer les modèles dans l'image et d'éviter un téléchargement au premier démarrage.

### Réutilisation de la pipeline OCR
Côté application, la pipeline `PPStructure` est désormais mise en cache côté FastAPI au lieu d'être recréée à chaque requête.

## Variables importantes

```dockerfile
ENV OCR_DEVICE=cpu
ENV OUTPUT_DIR=/app/outputs
ENV XDG_CACHE_HOME=/tmp/.cache
ENV MPLCONFIGDIR=/tmp/matplotlib
```

Ces variables aident à garder le conteneur compatible avec un rootfs en lecture seule tout en évitant des écritures dans le home utilisateur pour les caches temporaires.

## Build recommandé

```bash
docker build \
  --build-arg OCR_LANGUAGE=fr \
  --build-arg PRELOAD_PADDLE_MODELS=true \
  -t ocr-engine:latest .
```

## Note importante

Si vous changez `OCR_LANGUAGE` au runtime, reconstruisez aussi l'image avec le même `--build-arg OCR_LANGUAGE=...`. Sinon, PaddleOCR pourra chercher de nouveaux modèles qui ne seront pas présents dans l'image.
