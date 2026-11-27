# MARVEL — Gestion des dons d'une association caritative

**M**ouvement **A**ssociatif pour la **R**edistribution des **V**aleurs et l'**E**ntraide **L**ocale

Mini-projet du module **DevOps**, Université de Béjaïa, Département d'Informatique
Année universitaire 2026 – 2027

> **Statut : développement en cours.** Le socle technique (API, deux frontends, Docker, CI, supervision) est en place ; plusieurs modules métier sont encore à écrire (voir [Avancement](#avancement)).

## Équipe : Avengers

| Membre |
|--------|
| Belaloui Samy Abdelmadjid |
| Boucekkine Anais Saleha |
| Ikhedji Amine |
| Khier Nassim |
| Lachi Kouceila |

## Description du projet

Application destinée à aider une association caritative à collecter des dons (argent et dons en nature), à les répartir entre les bénéficiaires et à rendre des comptes de façon transparente aux donateurs.

### Fonctionnalités visées

- **Vitrine publique** : présentation de l'association, campagnes en cours avec objectif et jauge de progression, actualités
- **Dons financiers** (paiement simulé, aucune donnée bancaire réelle) et **dons en nature** (déclaration, collecte, entrée en stock)
- **Reçus de don** numérotés en PDF
- **Bénéficiaires** et **distributions** (sortie de stock, preuve de remise, détection des doublons)
- **Bénévoles et missions**, événements de collecte
- **Suivi budgétaire** : recettes, dépenses, rapports de transparence, exports CSV / Excel / PDF
- **Tableau de bord** et statistiques

### Rôles

| Rôle | Accès |
|------|-------|
| Donateur / compte sans rôle | Vitrine, dons, historique |
| `Volunteer` | Vitrine, inscription aux missions |
| `Collection_Manager` | Back-office : campagnes, événements, missions, dons en nature |
| `Stock_Manager` | Back-office : stock, réception et collecte des dons en nature |
| `Treasurer` | Back-office : trésorerie, dépenses, exports |
| `Administrator` | Back-office : tout, plus l'attribution des rôles |
| `Beneficiary` | Rôle prévu en base (bénéficiaires) |

Les autorisations sont **toujours vérifiées côté backend** ; les gardes du frontend ne sont qu'un confort d'interface.

## Architecture

La vitrine et le back-office sont **deux applications séparées** pour que la vitrine reste disponible même si le back-office est indisponible. Les deux consomment la même API.

```text
                 UTILISATEUR
                      |
          +-----------+-----------+
          |                       |
     :8080 (Nginx)           :8081 (Nginx)
   frontend-public          frontend-admin
   (vitrine, dons)          (back-office)
          |                       |
          +-----------+-----------+
                      |  /api/ (proxy Nginx)
                  :8000 backend
                   (FastAPI)
                      |
        PostgreSQL + Storage (Supabase)
```

| Service | Technologie | Port Docker | Port dev (Vite) |
|---------|-------------|:-----------:|:---------------:|
| `backend` | FastAPI, Python 3.12 | 8000 | 8000 |
| `frontend-public` | React 19, Vite, Tailwind 4 | 8080 | 5173 |
| `frontend-admin` | React 19, Vite, Tailwind 4 | 8081 | 5174 |
| `uptime-kuma` | Supervision | 3001 (local uniquement) | — |

La base PostgreSQL et le stockage d'images sont fournis par **Supabase** (hors Docker Compose).

## Technologies

| Domaine | Outils |
|---------|--------|
| Backend | FastAPI, SQLAlchemy 2, Alembic, Pydantic, PyJWT, pwdlib (argon2), Pillow (conversion WebP), openpyxl et reportlab (exports) |
| Tests / qualité backend | pytest, ruff |
| Frontend public | React 19, TypeScript, Vite, Tailwind CSS 4, React Router, Vitest + Testing Library, ESLint, Prettier |
| Frontend admin | React 19, TypeScript, Vite, Tailwind CSS 4 (base TailAdmin), Base UI, React Hook Form + Zod, react-i18next (en / fr / ar), Oxlint + ESLint |
| Infrastructure | Docker, Docker Compose, Nginx, Uptime Kuma |
| CI/CD et sécurité | GitHub Actions, Gitleaks, `pip-audit`, `npm audit` |

## Structure du dépôt

```text
.
├── backend/             # API FastAPI (voir backend/README.md)
├── frontend-public/     # Vitrine (voir frontend-public/README.md)
├── frontend-admin/      # Back-office (voir frontend-admin/README.md)
├── infra/               # docker-compose.yml, .env.example (voir infra/README.md)
├── docs/                # Conventions de travail, supervision, vérification des dépendances
├── .github/workflows/   # ci.yml, dependency-checker.yml
└── README.md
```

Le backend est un **monolithe modulaire** : un dossier par domaine dans `backend/app/modules/`, organisé en `router` → `service` → `repository` (+ `schemas`, `models`).

## Installation et lancement

### Avec Docker (recommandé)

Prérequis : Git, Docker Desktop (moteur Linux démarré), accès au projet Supabase.

```powershell
# 1. Configuration (le fichier .env n'est jamais versionné)
Copy-Item infra/.env.example infra/.env
notepad infra/.env      # DATABASE_URL, JWT_SECRET_KEY, ...

# 2. Construction et démarrage
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d --build

# 3. Vérification : les services doivent être « healthy »
docker compose --env-file infra/.env -f infra/docker-compose.yml ps
```

| Service | URL |
|---------|-----|
| Vitrine | <http://localhost:8080> |
| Back-office | <http://localhost:8081> |
| API / Swagger | <http://localhost:8000/docs> |
| Healthcheck | <http://localhost:8000/health> |
| Uptime Kuma | <http://localhost:3001> |

Sous Linux / macOS, remplacer `Copy-Item` par `cp`.

### Variables d'environnement

| Variable | Rôle |
|----------|------|
| `DATABASE_URL` | Connexion PostgreSQL (`postgresql+psycopg://...`) |
| `JWT_SECRET_KEY` | Clé de signature des jetons, **32 octets minimum** |
| `CORS_ORIGINS` | Origines exactes autorisées (schéma, hôte, port) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Durée de vie du jeton (30 jours par défaut en local) |
| `AUTH_COOKIE_SECURE` | `false` en HTTP local, **`true` en HTTPS** |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | Stockage des images (buckets `campaigns`, `natural_donations`, `users`, `treasury_justificatives`) |
| `VITE_API_URL` | URL de l'API pour les frontends (vide = proxy `/api`) |
| `VITE_ADMIN_URL`, `VITE_PUBLIC_URL` | Redirections entre vitrine et back-office selon le rôle |

> Tout ce qui est dans une variable `VITE_*` finit dans le navigateur : **aucun secret** à cet endroit.

### Sans Docker (développement)

Chaque dossier a son propre README détaillé :

```powershell
# Backend
cd backend
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000

# Frontends (Node 22)
cd frontend-public ; npm ci ; npm run dev     # http://localhost:5173
cd frontend-admin  ; npm ci ; npm run dev     # http://localhost:5174
```

Migrations de base de données :

```powershell
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Tests et qualité

```powershell
# Backend
cd backend ; pytest -v ; ruff check .

# Frontend public
cd frontend-public ; npm run lint ; npm test ; npm run build

# Frontend admin
cd frontend-admin ; npm run lint ; npm run build
```

Les tests backend utilisent SQLite en mémoire et simulent Supabase Storage : aucun service externe réel n'est sollicité.

## Démarche DevOps

| Axe | Statut | Détail |
|-----|:------:|--------|
| Dépôt Git, branches, pull requests | Défini | GitHub Flow, Conventional Commits, PR relues : [docs/ConventionsTravail.md](docs/ConventionsTravail.md) |
| Intégration continue | Fait | `.github/workflows/ci.yml` : lint, tests, audit, build des 3 services, Gitleaks, construction des images Docker |
| Conteneurisation | Fait | Un Dockerfile par service, Nginx pour les frontends, utilisateur non-root pour le backend, `docker-compose.yml` |
| Livraison continue et retour arrière | À faire | Publication des images (GHCR) et déploiement automatique non encore en place |
| Configuration et secrets | Fait | `.env` ignoré par Git, `.env.example` fournis, scan de secrets en CI |
| Observabilité | Fait | `/health`, healthchecks Docker, logs `json-file` avec rotation, Uptime Kuma : [docs/monitoring.md](docs/monitoring.md) |
| Sécurité | Partiel | Authentification JWT en cookie `HttpOnly`, rôles, en-têtes de sécurité, `pip-audit` hebdomadaire ([docs/dependency-checker.md](docs/dependency-checker.md)) ; sauvegardes et restauration testée à faire |
| Documentation | Partiel | OpenAPI sur `/docs`, README par dossier ; manuel utilisateur à faire |

## Avancement

### Backend

| Module | État |
|--------|------|
| `auth` | Fait : inscription, connexion, déconnexion avec révocation de jeton, rôles, photo de profil |
| `campaigns` | Fait : campagnes (brouillon, publication, clôture, jauge, image) et événements de collecte |
| `financial_donations` | Fait : création, paiement simulé, statut, historique, listes filtrées ; le reçu PDF est encore un **simulacre** |
| `natural_donations` | Fait : types d'objets, déclaration, validation / refus, collectes, réception, entrée en stock, photos |
| `treasury` | Fait : dépenses avec justificatif, bilans (global, campagne, événement), exports CSV / Excel / PDF |
| `volunteers` | Fait : missions, planning, inscriptions, espace bénévole |
| `receipts`, `stock`, `beneficiaries`, `distributions`, `dashboard` | Squelette (routeurs vides) |

### Frontends

- **Vitrine** : accueil, liste des campagnes, connexion / inscription, redirection automatique des comptes de gestion vers le back-office. Formulaire de don, espace donateur et actualités à faire.
- **Back-office** : garde d'accès par rôle, layout, tableau de bord et profil provisoires. Les écrans de gestion seront branchés module par module.

## Organisation du travail

- Branche principale : `main` (protégée, modifications via pull request relue par un autre membre)
- Branches de travail : `feat/…`, `fix/…`, `docs/…`, `chore/…`, `ci/…`, `test/…`
- Commits au format Conventional Commits (`feat(donations): ajout endpoint de don financier`)
- Suivi des tâches : onglets **Issues** / **Projects** du dépôt

Détails dans [docs/ConventionsTravail.md](docs/ConventionsTravail.md).

## Règles importantes

- Aucun mot de passe, clé ou secret dans le dépôt : utiliser un fichier `.env` (ignoré par Git) et fournir un `.env.example` avec des valeurs factices
- Aucune donnée bancaire réelle : paiement simulé uniquement
- Aucune donnée personnelle réelle dans les jeux de test
- Montants en `Decimal` (jamais en flottant), dates en UTC
- Toute modification de schéma passe par une migration Alembic versionnée

## Documentation

| Document | Contenu |
|----------|---------|
| [backend/README.md](backend/README.md) | API, rôles, migrations, tests |
| [frontend-public/README.md](frontend-public/README.md) | Vitrine, structure, client API |
| [frontend-admin/README.md](frontend-admin/README.md) | Back-office, architecture, i18n |
| [infra/README.md](infra/README.md) | Docker, Supabase, diagnostic |
| [docs/ConventionsTravail.md](docs/ConventionsTravail.md) | Conventions d'équipe |
| [docs/monitoring.md](docs/monitoring.md) | Supervision et healthchecks |
| [docs/dependency-checker.md](docs/dependency-checker.md) | Surveillance des dépendances Python |