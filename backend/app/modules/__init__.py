"""Un sous-package par domaine métier : router → service → repository (+ schemas, models)."""

# Utilisé par alembic/env.py pour importer tous les modèles (autogenerate).
MODULES = [
    "auth",
    "campaigns",
    "financial_donations",
    "natural_donations",
    "receipts",
    "stock",
    "beneficiaries",
    "distributions",
    "treasury",
    "volunteers",
    "dashboard",
]
