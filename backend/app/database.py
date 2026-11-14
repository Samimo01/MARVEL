"""Connexion SQLAlchemy et dépendance de session FastAPI."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Base des modèles SQLAlchemy."""


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
