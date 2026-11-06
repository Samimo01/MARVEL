from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.api.router import api_router
from app.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")

# CORS : autorise les deux frontends (vitrine et back-office) à appeler l'API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes versionnées : /api/v1/...
app.include_router(api_router, prefix=settings.api_prefix)

# Healthcheck à la racine (Docker, supervision) : indépendant du préfixe de version.
app.include_router(health.router)
