# Guide d'Utilisation Docker

## 🚀 Démarrage Rapide

### Prérequis
```bash
# Créer l'environnement virtuel venv
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Build et Lancement

#### Avec Docker Compose (recommandé)
```bash
docker-compose up --build
```

#### Avec Docker uniquement
```bash
# Build
docker build -t ocr-engine:latest .

# Lancer
docker run -d \
  -p 8000:8000 \
  --name ocr-engine \
  --healthcheck-interval=30s \
  -v $(pwd)/outputs:/app/outputs \
  ocr-engine:latest
```

---

## 🔒 Vérifications de Sécurité

### 1️⃣ Vérifier l'utilisateur (non-root)
```bash
docker-compose exec ocr-engine whoami
# Output: appuser
```

### 2️⃣ Vérifier les permissions .env
```bash
docker-compose exec ocr-engine ls -la /app/.env
# Output: -rw------- 1 appuser root ... .env
```

### 3️⃣ Vérifier que root n'existe pas
```bash
docker-compose exec ocr-engine id root 2>&1 || echo "✓ Pas de compte root accessible"
```

### 4️⃣ Vérifier le health check
```bash
docker-compose ps
# STATUS: Up X seconds (healthy)
```

---

## 📊 Inspection de l'Image

### Vérifier les labels
```bash
docker inspect ocr-engine:latest | grep -A 20 "Labels"
```

### Vérifier la taille
```bash
docker images ocr-engine:latest
```

### Voir la structure interne
```bash
docker run --rm ocr-engine:latest ls -la /app
docker run --rm ocr-engine:latest ps aux
```

---

## 📁 Structure des Volumes

```
outputs/
├── image_1/
│   ├── image_1.json       # Résultats JSON
│   ├── image_1.txt        # Texte extrait
│   ├── image_1_*.jpg      # Visualisations
│   └── .temp/             # Fichiers temporaires
└── image_2/
    └── ...
```

Le dossier `outputs/` est automatiquement créé et partagé entre le conteneur et l'hôte.

---

## 🧹 Nettoyage

### Arrêter les services
```bash
docker-compose down
```

### Supprimer l'image
```bash
docker rmi ocr-engine:latest
```

### Nettoyer tout (conteneurs + images + volumes)
```bash
docker-compose down -v
docker system prune -a
```

---

## 🐛 Dépannage

### Logs en temps réel
```bash
docker-compose logs -f ocr-engine
```

### Accès au shell
```bash
docker-compose exec ocr-engine /bin/sh
```

### Vérifier le système de fichiers
```bash
docker run --rm -it ocr-engine:latest /bin/sh
```

### Tester l'API
```bash
curl http://localhost:8000/health
```

### Tester avec un fichier
```bash
curl -X POST http://localhost:8000/process \
  -F "file=@/path/to/image.jpg"
```

---

## ⚙️ Configuration Avancée

### Variables d'environnement
Modifier `.env.example` ou passer via docker-compose:

```yaml
environment:
  - PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True
  - MY_CUSTOM_VAR=value
```

### Limiter les ressources
```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 2G
```

### Montages personnalisés
```yaml
volumes:
  - ./outputs:/app/outputs:rw
  - ./models:/app/models:ro  # Lecture seule
```

---

## 🔐 Sécurité - Points Clés

✅ **Utilisateur non-root**: `appuser` (UID 1001)
✅ **Permissions .env**: `600` (propriétaire uniquement)
✅ **Permissions app**: `755` dossiers, `644` fichiers
✅ **Health check**: Automatique
✅ **Pas de nouvelles permissions**: `no-new-privileges:true`
✅ **Pas de capacités Linux**: `cap_drop: ALL`
✅ **Système de fichiers read-only**: Sauf `/app/outputs` et `/tmp`
✅ **ccache**: Optimise les compilations C/C++

---

## 📈 Performance

### Avec ccache
- **1ère build**: Compilation complète (~10-15 min selon CPU)
- **2e build**: Cache utilisé (~2-3 min)
- **3e+ build**: Cache optimal (~30 sec avec changements mineurs)

### Taille de l'image
- Environ 1.5-2GB (dépend du cache local)
- Peu d'outils inutiles grâce à `--no-install-recommends`

---

## 🔗 Ressources Utiles

- [Documentation Docker](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
