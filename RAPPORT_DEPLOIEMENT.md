# Rapport de déploiement - DPSE MFB

## Résumé

Ce document retrace toutes les étapes effectuées pour déployer l'application Django DPSE (Direction de la Planification et des Statistiques Economiques) sur le serveur de production.

---

## 1. Configuration GitHub

### Connexion GitHub
```bash
gh auth login
```
- Authentifié en tant que : **Univers10**

### Clone du projet
```bash
gh repo clone cyrille911/site-dpse-mfb /home/deploy/Site-DPSE-MFB
```

---

## 2. Configuration MySQL

### Installation de MySQL
```bash
apt update && apt install -y mysql-server
```

### Configuration de la base de données
- **Hôte** : MySQL Docker (site-dpse-mfb-mysql-1)
- **Base de données** : dpse
- **Utilisateur** : root
- **Mot de passe** : `dpse_password_strong_2024`

### Création de la base
```bash
docker exec -i site-dpse-mfb-mysql-1 mysql -u root -p'dpse_password_strong_2024' -e "DROP DATABASE IF EXISTS dpse; CREATE DATABASE dpse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

---

## 3. Configuration Django

### Variables d'environnement (.env)

```bash
# Configuration MySQL
DB_NAME=dpse
DB_USER=dpse_user
DB_PASSWORD=dpse_password_strong_2024
DB_HOST=site-dpse-mfb-mysql-1
DB_PORT=3306

# Django
DEBUG=False
SECRET_KEY=nppx0GKfObA93t7MwRNAJNBvTVZkabxOZXpsmkgCTFjKrB9oio4bICB_4KUJaVuHjPM

# Domaine
DOMAIN=dpse.aidn.ci
```

### Exécution des migrations
```bash
docker exec site-dpse-mfb-web-1 python manage.py migrate --noinput
```

---

## 4. Import des données SQL

### Fichier source
- Emplacement : `/home/deploy/db_dump.sql`

### Commandes d'import
```bash
# Copie du fichier SQL dans le conteneur
docker cp /home/deploy/db_dump.sql site-dpse-mfb-web-1:/tmp/db_dump.sql

# Import des utilisateurs
docker exec site-dpse-mfb-web-1 python3 -c "
import sqlite3
import pymysql

conn = sqlite3.connect(':memory:')
cursor = conn.cursor()
with open('/tmp/db_dump.sql', 'r') as f:
    sql = f.read()
sql = sql.replace('BEGIN TRANSACTION;', '').replace('COMMIT;', '')
cursor.executescript(sql)

mysql_conn = pymysql.connect(host='site-dpse-mfb-mysql-1', port=3306, user='root', passwd='dpse_password_strong_2024', db='dpse', charset='utf8mb4')
mysql_cursor = mysql_conn.cursor()

# Import des utilisateurs
cursor.execute('SELECT id, password, last_login, is_superuser, first_name, last_name, is_staff, is_active, date_joined, email, username, role, phone_number, photo, program, entity, function, profession, interest FROM users_user')
users = cursor.fetchall()

for u in users:
    profession = u[17] if u[17] else ''
    interest = u[18] if u[18] else ''
    
    sql = '''INSERT INTO users_user 
(id, password, last_login, is_superuser, first_name, last_name, is_staff, is_active, date_joined, email, username, role, phone_number, photo, program, entity, \`function\`, profession, interest) 
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
    mysql_cursor.execute(sql, (u[0], u[1], u[2], u[3], u[4], u[5], u[6], u[7], u[8], u[9], u[10], u[11], u[12], u[13], u[14], u[15], u[16], profession, interest))

mysql_conn.commit()
"
```

### Données importées

| Table | Lignes |
|-------|--------|
| auth_permission | 116 |
| django_migrations | 51 |
| django_content_type | 29 |
| django_admin_log | 12 |
| auth_group | 5 |
| django_session | 5 |
| users_user_groups | 3 |
| users_user | 3 |
| planning_activite | 1 |
| planning_action | 1 |
| planning_effet | 1 |
| planning_planaction | 1 |
| planning_produit | 1 |
| documents_document_mfb | 1 |

---

## 5. Déploiement Docker

### Commandes Docker
```bash
# Arrêt des anciens conteneurs
cd /home/deploy/Site-DPSE-MFB
docker compose -f docker-compose.prod.yml down

# Modification du port nginx (80 -> 8080)
# Dans docker-compose.prod.yml: ports: - "8080:80"

# Démarrage des conteneurs
docker compose -f docker-compose.prod.yml up -d

# Vérification
docker ps
```

### Conteneurs actifs
| Conteneur | Image | Statut |
|-----------|-------|--------|
| site-dpse-mfb-nginx-1 | nginx:alpine | Up |
| site-dpse-mfb-web-1 | site-dpse-mfb | Up |
| site-dpse-mfb-celery-1 | site-dpse-mfb | Up |
| site-dpse-mfb-celery-beat-1 | site-dpse-mfb | Up |
| site-dpse-mfb-redis-1 | redis:7-alpine | Up |
| site-dpse-mfb-mysql-1 | mysql:8.0 | Up |

---

## 6. Configuration Nginx

### Fichier de configuration
**Emplacement** : `/etc/nginx/sites-enabled/dpse`

```nginx
server {
    listen 80;
    server_name dpse.aidn.ci www.dpse.aidn.ci;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dpse.aidn.ci www.dpse.aidn.ci;

    ssl_certificate /etc/letsencrypt/live/dpse.aidn.ci/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dpse.aidn.ci/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;

    location /.well-known/ {
        root /var/www/html;
    }

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/deploy/Site-DPSE-MFB/staticfiles/;
    }

    location /media/ {
        alias /home/deploy/Site-DPSE-MFB/media/;
    }
}
```

### Commandes nginx
```bash
# Recharger la configuration
nginx -s reload
```

---

## 7. Configuration SSL

### Génération du certificat
```bash
# Installation de certbot (si nécessaire)
apt install -y certbot python3-certbot-nginx

# Ajout du support ACME dans nginx
# (voir section location /.well-known/ ci-dessus)

# Génération du certificat
certbot certonly --webroot -w /var/www/html -d dpse.aidn.ci --non-interactive --agree-tos --email admin@aidn.ci
```

### Renouvellement automatique
```bash
# Vérification du timer
systemctl status certbot.timer

# Création du hook de rechargement
echo '#!/bin/bash
nginx -s reload' > /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh

# Test du renouvellement
certbot renew --dry-run
```

---

## 8. Accès

### URLs
- **HTTP** : http://dpse.aidn.ci (redirige vers HTTPS)
- **HTTPS** : https://dpse.aidn.ci
- **Admin** : https://dpse.aidn.ci/admin

### Comptes utilisateurs

| Username | Email | Rôle | Group |
|----------|-------|------|-------|
| cyrilletaha00@gmail.com | cyrilletaha00@gmail.com | Superuser | SuiveurEvaluateur |
| cyrilletaha02@gmail.com | cyrilletaha02@gmail.com | point_focal | PointFocal |
| cyrilletaha03@gmail.com | cyrilleaha03@gmail.com | responsable | Responsable |

**Note** : Les mots de passe sont cryptés au format Django PBKDF2. Pour réinitialiser un mot de passe :
```bash
docker exec site-dpse-mfb-web-1 python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); u = User.objects.get(username='username'); u.set_password('nouveau_mot_de_passe'); u.save()"
```

### Accès base de données
```bash
# Connexion MySQL via Docker
docker exec -it site-dpse-mfb-mysql-1 mysql -u root -p'dpse_password_strong_2024' dpse
```

---

## 9. Commandes utiles

### Gestion des conteneurs
```bash
# Redémarrer l'application
cd /home/deploy/Site-DPSE-MFB
docker compose -f docker-compose.prod.yml restart

# Voir les logs
docker logs site-dpse-mfb-web-1
docker logs site-dpse-mfb-nginx-1
docker logs site-dpse-mfb-celery-1

# Mettre à jour l'application
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

### Gestion Django
```bash
# Créer un superutilisateur
docker exec site-dpse-mfb-web-1 python manage.py createsuperuser

# Appliquer les migrations
docker exec site-dpse-mfb-web-1 python manage.py migrate

# Collecter les fichiers statiques
docker exec site-dpse-mfb-web-1 python manage.py collectstatic --noinput
```

### Gestion SSL
```bash
# Renouveler le certificat manuellement
certbot renew

# Vérifier la date d'expiration
certbot certificates
```

---

## 10. Résumé des chemins importants

| Description | Chemin |
|-------------|--------|
| Projet Django | `/home/deploy/Site-DPSE-MFB` |
| Fichier .env | `/home/deploy/Site-DPSE-MFB/.env` |
| Docker Compose prod | `/home/deploy/Site-DPSE-MFB/docker-compose.prod.yml` |
| Nginx config | `/etc/nginx/sites-enabled/dpse` |
| Certificat SSL | `/etc/letsencrypt/live/dpse.aidn.ci/` |
| Dump SQL | `/home/deploy/db_dump.sql` |

---

## 11. Statut

- [x] GitHub connecté
- [x] Projet cloné
- [x] MySQL configuré
- [x] Base de données créée
- [x] Données importées
- [x] Docker déployé
- [x] Nginx configuré
- [x] SSL activé
- [x] Renouvellement automatique activé

---

*Document généré le 23 février 2026*
