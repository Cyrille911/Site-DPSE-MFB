#!/bin/bash

# Script de déploiement pour VPS
# Usage: ./deploy.sh

set -e

echo "=== Déploiement Site-DPSE-MFB ==="

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo "Docker n'est pas installé. Installation..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Vérifier que Docker Compose est disponible
if ! docker compose version &> /dev/null; then
    echo "Docker Compose n'est pas disponible."
    exit 1
fi

# Vérifier le fichier .env
if [ ! -f .env ]; then
    echo "ERREUR: Fichier .env manquant!"
    echo "Copiez .env.example vers .env et configurez vos variables."
    exit 1
fi

# Arrêter les conteneurs existants
echo "Arrêt des conteneurs existants..."
docker compose down || true

# Construire et démarrer
echo "Construction et démarrage des services..."
docker compose --env-file .env up -d --build

# Attendre que la base de données soit prête
echo "Attente de la disponibilité des services..."
sleep 10

# Exécuter les migrations
echo "Exécution des migrations Django..."
docker compose exec -T web python manage.py migrate --noinput

# Collecter les fichiers statiques
echo "Collecte des fichiers statiques..."
docker compose exec -T web python manage.py collectstatic --noinput

echo ""
echo "=== Déploiement terminé ==="
echo "L'application est accessible sur http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "Commandes utiles:"
echo "  - Voir les logs: docker compose logs -f"
echo "  - Arrêter: docker compose down"
echo "  - Créer un superuser: docker compose exec web python manage.py createsuperuser"
