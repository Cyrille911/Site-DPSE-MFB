# Guide de Développement Local - DPSE

## Base de données PostgreSQL (développement)

Le plus simple est d'utiliser Docker : le service `db` du `docker-compose.yml`
démarre PostgreSQL 16 avec les identifiants du `.env`.

```bash
cp .env.local .env     # puis renseigner DB_PASSWORD, SECRET_KEY, EMAIL_*
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Le site est accessible sur http://localhost:8001 ; PostgreSQL est exposé sur
le port hôte 5433 (`psql -h localhost -p 5433 -U dpse_user dpse_dev`).

### Sans Docker (PostgreSQL installé en local)

```sql
CREATE USER dpse_user WITH PASSWORD 'motdepasse';
CREATE DATABASE dpse_dev OWNER dpse_user;
```

Dans `.env`, mettre `DB_HOST=localhost` et `DB_PORT=5432`.

### Variables du fichier `.env`

```
DB_NAME=dpse_dev
DB_USER=dpse_user
DB_PASSWORD=...
DB_HOST=db          # localhost sans Docker
DB_PORT=5432
```

### 4. Installation des dépendances Python

```bash
# Création de l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows

# Installation des dépendances
pip install -r requirements.txt
```

### 5. Migration de la base de données

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Création du superutilisateur

```bash
python manage.py createsuperuser
```

### 7. Lancement du serveur de développement

```bash
python manage.py runserver
```

Le site sera accessible sur http://127.0.0.1:8000

## Déploiement en Production

Le projet utilise `docker-compose.prod.yml` pour la production :

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

## Base de données en production

PostgreSQL 16 (service `db` de `docker-compose.prod.yml`), données dans le
volume `postgres_data`. Les variables `DB_*` viennent du `.env` du serveur.

Sauvegarde / restauration :
```bash
docker compose -f docker-compose.prod.yml exec db pg_dump -U $DB_USER $DB_NAME > backup.sql
docker compose -f docker-compose.prod.yml exec -T db psql -U $DB_USER $DB_NAME < backup.sql
```

## Optimisation Responsives

Le site inclut des optimisations pour tous les écrans :

- **Mobile (< 576px)** : Texte compact, layout simplifié
- **Tablette (576px - 768px)** : Adaptation intermédiaire  
- **Desktop (> 768px)** : Layout complet

Les classes Bootstrap sont utilisées pour une responsivité optimale :
- `d-none d-md-block` : Caché sur mobile, visible sur tablette+
- `d-block d-md-none` : Visible sur mobile, caché sur tablette+
- `col-sm-12 col-md-6 col-lg-3` : Grid responsive

## Points d'attention

1. **PostgreSQL requis** : le projet ne fonctionne ni avec SQLite ni avec MySQL
2. **Variables d'environnement** : vérifier que `.env` est correctement configuré
3. **Après modification du `.env`** : `docker compose up -d --force-recreate` (un simple `restart` ne relit pas les variables)
