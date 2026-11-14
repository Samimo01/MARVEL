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
# puis éditer .env : DATABASE_URL, JWT_SECRET_KEY
```

Sous Linux / macOS : `source .venv/bin/activate` et `cp .env.example .env`.

**Avec Supabase** : dans _Project Settings → Database → Connection string_, copier l'URL et
remplacer le préfixe `postgresql://` par `postgresql+psycopg://` dans `DATABASE_URL`.

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
Aucun rôle n'est attribué à l'inscription. Un administrateur peut consulter les rôles
disponibles avec `GET /api/v1/admin/roles`, voir les affectations d'un utilisateur avec
`GET /api/v1/admin/users/{id_user}/roles` et modifier une affectation avec
`POST /api/v1/admin/users/{id_user}/roles/{role_name}`, en envoyant
`{"assignment_type":"assigned"}` ou `{"assignment_type":"revoked"}`. Ces routes exigent
un JWT d'administrateur. Le dernier administrateur actif ne peut pas se révoquer.
La création ne dépend pas de la configuration d'un service d'e-mail.
La création, la modification, la publication, la clôture et la suppression d'une campagne
requièrent un rôle actif `Collection_Manager` ou `Administrator` dans `role_assignments`.
Le catalogue public des campagnes reste accessible sans ces rôles.

Le premier administrateur doit être initialisé hors API, avec une opération SQL exécutée
par un propriétaire de la base (remplacer l'adresse e-mail) :

```sql
INSERT INTO public.roles (role_name)
VALUES ('Administrator')
ON CONFLICT (role_name) DO NOTHING;

INSERT INTO public.role_assignments (assignment_type, id_role, id_user)
SELECT 'assigned', roles.id_role, users.id_user
FROM public.roles
CROSS JOIN public.users
WHERE roles.role_name = 'Administrator'
  AND users.email = 'admin@example.com'
  AND NOT EXISTS (
    SELECT 1
    FROM public.role_assignments
    WHERE id_role = roles.id_role
      AND id_user = users.id_user
  );
```

## Connexion

`POST /api/v1/auth/login` accepte une adresse e-mail et un mot de passe, puis renvoie
un JWT de type Bearer si les identifiants sont valides. Le token expire après 30 jours
par défaut (`ACCESS_TOKEN_EXPIRE_MINUTES=43200`). Le frontend peut le conserver dans
`localStorage` et l'envoyer dans l'en-tête `Authorization: Bearer <token>` pour ses
requêtes authentifiées.

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
