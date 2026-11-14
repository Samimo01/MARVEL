# backend — API REST de l'association caritative

## Rôle

API unique du projet (monolithe modulaire) consommée par les deux frontends :

- **`frontend-public`** (vitrine) → routes publiques `/api/v1/public/...`, sans authentification ;
- **`frontend-admin`** (back-office) → routes protégées `/api/v1/...` (JWT + rôles).

Elle porte la logique métier : dons, reçus numérotés, stock (mouvements tracés), bénéficiaires,
distributions, budget et indicateurs du tableau de bord. La documentation OpenAPI est générée
automatiquement sur `/docs`.

**Stack** : Python 3.12+, FastAPI, SQLAlchemy 2, Alembic, Pydantic, PostgreSQL (Supabase),
pytest, ruff.

## Structure

```text
backend/
├── app/
│   ├── main.py              # Application FastAPI + CORS + routeurs
│   ├── config.py            # Réglages lus depuis les variables d'environnement
│   ├── database.py          # Moteur SQLAlchemy, session, Base, colonnes standard
│   ├── api/                 # health.py, public.py (routes publiques), router.py (agrégation v1)
│   ├── core/                # Briques transverses (sécurité, erreurs…) à venir
│   └── modules/             # Un dossier par domaine métier
│       └── <module>/        # router.py → service.py → repository.py (+ schemas.py, models.py)
├── alembic/                 # Migrations de base de données (versions/)
├── tests/                   # pytest
├── requirements.txt         # Dépendances d'exécution
├── requirements-dev.txt     # + outils de test et de qualité
├── pyproject.toml           # Configuration ruff et pytest
└── .env.example             # Variables d'environnement (sans valeur sensible)
```

Modules : `auth`, `campaigns`, `donations`, `receipts`, `stock`, `beneficiaries`,
`distributions`, `budget`, `volunteers`, `dashboard`.

## Installation

Prérequis : Python 3.12 ou plus récent, et une base PostgreSQL (un projet Supabase convient).

```powershell
cd backend

# 1. Environnement virtuel
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Dépendances (avec les outils de test)
pip install -r requirements-dev.txt

# 3. Configuration (le fichier .env n'est jamais versionné)
Copy-Item .env.example .env
# puis éditer .env : SUPABASE_URL, JWT_SECRET_KEY
```

Sous Linux / macOS : `source .venv/bin/activate` et `cp .env.example .env`.

**Avec Supabase** : dans _Project Settings → Database → Connection string_, copier l'URL et
remplacer le préfixe `postgresql://` par `postgresql+psycopg://` dans `SUPABASE_URL`.

## Lancer l'API

```powershell
uvicorn app.main:app --reload --port 8000
```

- Santé : <http://localhost:8000/health> et <http://localhost:8000/api/v1/health>
- Documentation interactive : <http://localhost:8000/docs>

## Communication avec les frontends

Les origines autorisées (CORS) sont définies par `CORS_ORIGINS` dans `.env` :
par défaut `http://localhost:5173` (frontend-public) et `http://localhost:5174` (frontend-admin).
En production, mettre ici les domaines réels.

## Création de compte

`POST /api/v1/auth/register` crée un compte à partir du prénom, du nom, de l'e-mail,
du mot de passe et du téléphone, puis renvoie un token d'accès JWT de type Bearer.
La clé `JWT_SECRET_KEY` doit contenir au moins 32 octets et être définie dans `.env`
(génération : `python -c "import secrets; print(secrets.token_urlsafe(48))"`).
Aucun rôle n'est attribué à l'inscription ; les rôles sont gérés séparément par un
administrateur. La création ne dépend pas de la configuration d'un service d'e-mail.

## Base de données (Alembic)

```powershell
alembic revision --autogenerate -m "ajoute la table campaigns"   # créer une migration
alembic upgrade head                                              # appliquer les migrations
```

Toute modification de schéma passe par une migration versionnée ; ne jamais modifier une base
partagée à la main. Ne pas écrire deux migrations en parallèle sans coordination.

## Tests et qualité

```powershell
pytest                 # tests
ruff check .           # lint
ruff format .          # formatage
```

## Règles du module (rappel des conventions)

- Aucune logique métier dans les routers : `router` (HTTP) → `service` (métier) → `repository` (base).
- Schémas Pydantic distincts en entrée et en sortie ; on n'expose jamais un modèle de base.
- Montants en `Decimal`, jamais en `float` ; dates en UTC.
- Aucun secret dans le dépôt : seul `.env.example` est versionné.
