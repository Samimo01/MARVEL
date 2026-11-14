from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import health
from app.api.router import api_router
from app.config import settings
from app.database import SessionLocal
from app.middleware.security import SecurityHeadersMiddleware

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)
app.include_router(health.router)


@app.on_event("startup")
def check_db_connection() -> None:
    
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        print(" Connexion Supabase OK")
    except Exception as exc:
        print(f" Connexion Supabase ÉCHEC : {exc}")
        raise