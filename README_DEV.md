# Guide de Développement Local - DPSE

## Configuration MySQL pour le développement

### 1. Installation de MySQL

**Sur Ubuntu/Debian :**
```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
sudo systemctl enable mysql
```

**Sur macOS :**
```bash
brew install mysql
brew services start mysql
```

**Sur Windows :**
Télécharger et installer MySQL depuis https://dev.mysql.com/downloads/mysql/

### 2. Configuration de la base de données

```bash
# Connexion à MySQL
sudo mysql -u root

# Création de la base de données
CREATE DATABASE dpse_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Création de l'utilisateur
CREATE USER 'root'@'localhost' IDENTIFIED BY 'rootpassword';

# Attribution des permissions
GRANT ALL PRIVILEGES ON dpse_dev.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Configuration du projet

Copier le fichier d'environnement :
```bash
cp .env.local .env
```

Le fichier `.env.local` est déjà configuré pour MySQL local :
```
DB_NAME=dpse_dev
DB_USER=root
DB_PASSWORD=rootpassword
DB_HOST=localhost
DB_PORT=3306
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
pip install mysqlclient
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

## Architecture de la base de données MySQL

Le projet utilise MySQL en production et en développement local. Les variables d'environnement sont automatiquement détectées :

- **Production (Docker)** : Variables définies dans docker-compose.prod.yml
- **Développement local** : Variables du fichier `.env.local`

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

1. **MySQL requis** : Le projet ne fonctionne plus avec SQLite
2. **Variables d'environnement** : Vérifier que `.env` est correctement configuré
3. **Permissions MySQL** : L'utilisateur doit avoir les droits sur la base `dpse_dev`
4. **Port MySQL** : Par défaut 3306, à vérifier si personnalisé
