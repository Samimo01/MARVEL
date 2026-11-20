# Supervision et monitoring — MARVEL

## 1. Objectif

La supervision de MARVEL repose sur les healthchecks Docker et Uptime Kuma. Elle permet de surveiller la disponibilité du backend et des deux interfaces frontend.

## 2. Services supervisés

| Service | Adresse locale | Endpoint de supervision |
|---|---|---|
| Backend | http://localhost:8000 | http://backend:8000/health |
| Frontend public | http://localhost:8080 | http://frontend-public:80/ |
| Frontend admin | http://localhost:8081 | http://frontend-admin:80/ |

Uptime Kuma est accessible sur http://localhost:3001.

## 3. Configuration Uptime Kuma

Trois moniteurs HTTP(s) sont configurés :

- MARVEL Backend
- MARVEL Frontend Public
- MARVEL Frontend Admin

Paramètres :
- Intervalle : 20 secondes
- Tentatives : 3
- Timeout : 10 secondes

Les données sont conservées dans le volume Docker `uptime-kuma-data`.

## 4. Healthchecks Docker

Le backend est contrôlé via `/health`.

Les deux frontends sont contrôlés par une requête HTTP sur leur serveur Nginx.

La configuration est définie dans `infra/docker-compose.yml`.

## 5. Gestion des logs

Les services utilisent le driver `json-file`.

- Taille maximale : 10 MB
- Nombre maximal de fichiers : 3

Pour consulter les logs :

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml logs -f backend
docker compose --env-file infra/.env -f infra/docker-compose.yml logs -f frontend-public
docker compose --env-file infra/.env -f infra/docker-compose.yml logs -f frontend-admin
docker compose --env-file infra/.env -f infra/docker-compose.yml logs -f uptime-kuma
```

## 6. Vérification des services

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml ps
```

## 7. Test de détection d'une panne

Le test de supervision a été réalisé :

1. Arrêt temporaire du backend.
2. Détection de la panne par Uptime Kuma : DOWN.
3. Redémarrage du backend.
4. Retour du moniteur à l'état UP.

Le endpoint `/health` a répondu HTTP 200 après le redémarrage.

## 8. Limites

Les moniteurs vérifient la disponibilité HTTP des services. Le endpoint `/health` ne vérifie pas à lui seul la disponibilité complète de la base de données.

Aucun canal de notification externe n'est déclaré comme configuré à ce stade.