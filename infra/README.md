# MARVEL — Documentation DevOps

## 1. Présentation

MARVEL est une plateforme de gestion des dons pour une association caritative.

Ce document présente l'infrastructure Docker du projet, la configuration des services, leur lancement et les procédures de diagnostic.

L'objectif est de permettre à chaque membre de l'équipe de démarrer l'environnement de développement de manière reproductible.

## 2. Architecture technique

L'application repose sur trois services conteneurisés :

| Service | Technologie | Port local | Rôle |
|---|---|---:|---|
| Backend | FastAPI / Python 3.12 | 8000 | API REST |
| Frontend public | React / Vite / Nginx | 8080 | Interface publique |
| Frontend admin | React / Vite / Nginx | 8081 | Interface d'administration |
| Base de données | PostgreSQL Supabase | Externe | Persistance des données |

### Architecture des communications

- Le frontend public communique avec le backend via Nginx.
- Le frontend admin communique avec le backend via Nginx.
- Le backend se connecte à PostgreSQL hébergé sur Supabase.
- Les trois conteneurs communiquent sur le réseau Docker `marvel-network`.
- La base de données n'est pas hébergée dans Docker Compose : elle est fournie par Supabase.

### Schéma simplifié

```text
              UTILISATEUR
                   |
          +--------+--------+
          |                 |
     Port 8080         Port 8081
          |                 |
   FRONTEND PUBLIC    FRONTEND ADMIN
       (Nginx)            (Nginx)
          |                 |
          +--------+--------+
                   |
             Port 8000
                   |
              BACKEND
              (FastAPI)
                   |
             Port 6543
                   |
          SUPABASE POSTGRESQL
```

## 3. Prérequis

Avant de lancer le projet, installer :

- Git : gestion du code source.
- Docker Desktop : exécution des conteneurs.
- Docker Compose : orchestration des services.
- Un accès au projet Supabase : récupération des informations de connexion.

Vérifier les installations :

```powershell
git --version
docker --version
docker compose version
```

Docker Desktop doit être démarré avec le moteur Linux disponible.

## 4. Configuration des variables d'environnement

La configuration sensible est stockée dans `infra/.env`.

Le fichier `infra/.env.example` fournit un modèle de configuration sans mot de passe réel.

### 4.1 Créer le fichier local

Depuis la racine du dépôt :

```powershell
Copy-Item infra/.env.example infra/.env
notepad infra/.env
```

### 4.2 Configurer Supabase

Renseigner les informations de connexion du Shared Pooler Supabase :

```dotenv
DATABASE_URL=postgresql+psycopg://postgres.PROJECT_REF:URL_ENCODED_PASSWORD@aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require
```

Remplacer :

- `PROJECT_REF` par l'identifiant du projet Supabase.
- `URL_ENCODED_PASSWORD` par le mot de passe PostgreSQL encodé pour une URL.

Le port `6543` correspond au Transaction Pooler utilisé dans la configuration actuelle.

Attention : les caractères spéciaux du mot de passe doivent être encodés dans l'URL.

### 4.3 Configurer la clé JWT

```dotenv
JWT_SECRET_KEY=CHANGE_ME
```

Remplacer cette valeur par une clé secrète aléatoire et suffisamment longue.

Ne jamais utiliser une clé de production dans un dépôt public.

### 4.4 URL de l'API frontend

```dotenv
VITE_API_URL=
```

La valeur peut rester vide dans la configuration actuelle : les requêtes `/api/` passent par le proxy Nginx.

### 4.5 Sécurité

Le fichier `infra/.env` contient des informations sensibles.

- Ne jamais le committer.
- Ne jamais transmettre son contenu dans un message public.
- Ne jamais publier les identifiants Supabase.
- Utiliser `.env.example` pour partager la structure de configuration.

Vérifier que le fichier est ignoré par Git :

```powershell
git check-ignore infra/.env
```

## 5. Construction et démarrage

Toutes les commandes suivantes sont exécutées depuis la racine du projet MARVEL.

### 5.1 Vérifier la configuration Compose

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml config -q
```

Cette commande valide la configuration sans afficher l'ensemble des variables.

### 5.2 Construire et démarrer les services

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d --build
```

### 5.3 Vérifier l'état des conteneurs

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml ps
```

Les trois services doivent atteindre l'état `healthy`.

## 6. Accès aux services

| Service | URL |
|---|---|
| Backend FastAPI | http://localhost:8000 |
| Documentation Swagger | http://localhost:8000/docs |
| Frontend public | http://localhost:8080 |
| Frontend admin | http://localhost:8081 |
| Healthcheck backend | http://localhost:8000/health |

### Vérifier les réponses HTTP

```powershell
Invoke-WebRequest http://localhost:8000/health -UseBasicParsing
Invoke-WebRequest http://localhost:8080 -UseBasicParsing
Invoke-WebRequest http://localhost:8081 -UseBasicParsing
```

### Tester le proxy Nginx

```powershell
Invoke-WebRequest http://localhost:8000/api/v1/public/campaigns -UseBasicParsing
Invoke-WebRequest http://localhost:8080/api/v1/public/campaigns -UseBasicParsing
Invoke-WebRequest http://localhost:8081/api/v1/public/campaigns -UseBasicParsing
```

Les trois requêtes doivent retourner HTTP 200.

La route publique des campagnes retourne actuellement une liste vide (`[]`) tant que son implémentation métier n'est pas terminée.

## 7. Commandes Docker utiles

### Afficher les conteneurs

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml ps
```

### Consulter les logs

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml logs
```

### Logs du backend

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml logs -f backend
```

### Logs du frontend public

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml logs -f frontend-public
```

### Logs du frontend admin

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml logs -f frontend-admin
```

### Redémarrer tous les services

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml restart
```

### Arrêter les services

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml stop
```

### Arrêter et supprimer les conteneurs

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml down
```

Cette commande ne supprime pas la base de données Supabase.

## 8. Vérification de la connexion Supabase

La connexion PostgreSQL peut être testée depuis le conteneur backend :

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml exec backend python -c "from sqlalchemy import text; from app.database import engine; connection=engine.connect(); print('Connexion Supabase OK'); print('SELECT 1 =',connection.execute(text('SELECT 1')).scalar()); connection.close()"
```

Résultat attendu :

```text
Connexion Supabase OK
SELECT 1 = 1
```

Le backend utilise Psycopg avec `prepare_threshold=None` pour désactiver les requêtes préparées automatiques incompatibles avec le mode Transaction Pooler utilisé.

## 9. Résolution des problèmes fréquents

### Docker Desktop ne démarre pas

Vérifier que Docker Desktop est lancé et que le moteur Linux est opérationnel.

```powershell
docker info
```

### Variable DATABASE_URL manquante

Vérifier que `infra/.env` existe et contient une URL PostgreSQL valide.

### Erreur de connexion Supabase

Vérifier :

- Le mot de passe PostgreSQL.
- L'identifiant du projet.
- L'adresse du pooler.
- Le port `6543`.
- L'encodage des caractères spéciaux.
- L'accès réseau à Supabase.

### Frontend inaccessible

Vérifier l'état des conteneurs et les logs Nginx :

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml ps
docker compose --env-file infra/.env -f infra/docker-compose.yml logs frontend-public frontend-admin
```

### Erreur 502 sur une requête API

Vérifier que le backend est opérationnel et que les frontends utilisent le réseau Docker `marvel-network`.

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml logs backend
```

## 10. Bonnes pratiques de collaboration

- Ne jamais committer les fichiers `.env`.
- Conserver `.env.example` à jour lorsque de nouvelles variables sont ajoutées.
- Tester localement les changements Docker avant de les pousser.
- Utiliser une branche Git dédiée pour chaque fonctionnalité.
- Documenter les nouvelles procédures DevOps.
- Vérifier les healthchecks après chaque reconstruction.
- Ne pas publier les secrets dans les logs ou les captures d'écran.

---

**Projet MARVEL — Documentation DevOps**

*Document évolutif : à mettre à jour au fur et à mesure de l'avancement du développement et de l'infrastructure.*