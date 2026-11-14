from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.modules.auth.models import User


@pytest.fixture()
def auth_client() -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, autoflush=False)

    def override_get_db() -> Iterator[Session]:
        with test_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client, test_session
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_registration_creates_user_without_email_configuration_or_role(auth_client) -> None:
    client, test_session = auth_client
    response = client.post(
        "/api/v1/auth/register",
        json={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "Ada@example.com",
            "password": "a-very-strong-password",
        },
    )

    assert response.status_code == 201
    assert response.json()["message"] == "Compte créé."
    assert response.json()["id_user"]

    with test_session() as session:
        user = session.scalar(select(User).where(User.email == "ada@example.com"))
        assert user is not None
        assert user.password_hash != "a-very-strong-password"


def test_registration_rejects_duplicate_email(auth_client) -> None:
    client, test_session = auth_client
    payload = {
        "firstname": "Ada",
        "lastname": "Lovelace",
        "email": "ada@example.com",
        "password": "a-very-strong-password",
    }

    created = client.post("/api/v1/auth/register", json=payload)
    duplicate = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert created.status_code == 201
    assert duplicate.status_code == 409
    with test_session() as session:
        assert len(session.scalars(select(User)).all()) == 1
