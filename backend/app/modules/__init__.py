"""Un sous-package par domaine métier : router → service → repository (+ schemas, models)."""

# Utilisé par alembic/env.py pour importer tous les modèles (autogenerate).
MODULES = [
    "auth",
    "campaigns",
    "donations",
    "receipts",
    "stock",
    "beneficiaries",
    "distributions",
    "budget",
    "volunteers",
    "dashboard",
]
