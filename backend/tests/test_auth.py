from collections.abc import Iterator

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.modules.auth.models import User


@pytest.fixture()
def auth_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        "test-jwt-secret-for-tests-at-least-32-bytes",
    )
    monkeypatch.setattr(settings, "access_token_expire_minutes", 30 * 24 * 60)
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


def test_registration_creates_user_and_returns_access_token(auth_client) -> None:
    client, test_session = auth_client
    response = client.post(
        "/api/v1/auth/register",
        json={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "Ada@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )

    assert response.status_code == 201
    assert response.json()["message"] == "Compte créé."
    assert response.json()["id_user"]
    assert response.json()["token_type"] == "bearer"
    claims = jwt.decode(
        response.json()["access_token"],
        "test-jwt-secret-for-tests-at-least-32-bytes",
        algorithms=["HS256"],
    )
    assert claims["sub"] == response.json()["id_user"]
    assert claims["exp"] > claims["iat"]

    with test_session() as session:
        user = session.scalar(select(User).where(User.email == "ada@example.com"))
        assert user is not None
        assert user.password_hash != "a-very-strong-password"


def test_registration_rejects_a_weak_jwt_secret(auth_client, monkeypatch) -> None:
    client, test_session = auth_client
    monkeypatch.setattr(settings, "jwt_secret_key", "too-short")
    payload = {
        "firstname": "Ada",
        "lastname": "Lovelace",
        "email": "ada@example.com",
        "password": "a-very-strong-password",
        "tel": "0612345678",
    }

    with pytest.raises(RuntimeError, match="32 octets"):
        client.post("/api/v1/auth/register", json=payload)

    with test_session() as session:
        assert session.scalar(select(User)) is None


def test_registration_rejects_duplicate_email(auth_client) -> None:
    client, test_session = auth_client
    payload = {
        "firstname": "Ada",
        "lastname": "Lovelace",
        "email": "ada@example.com",
        "password": "a-very-strong-password",
        "tel": "0612345678",
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


def test_login_returns_a_persistent_access_token_for_valid_credentials(auth_client) -> None:
    client, _ = auth_client
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "Ada@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "ADA@example.com",
            "password": "a-very-strong-password",
        },
    )

    assert registration.status_code == 201
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    claims = jwt.decode(
        response.json()["access_token"],
        "test-jwt-secret-for-tests-at-least-32-bytes",
        algorithms=["HS256"],
    )
    assert claims["sub"] == registration.json()["id_user"]
    assert claims["exp"] - claims["iat"] == 30 * 24 * 60 * 60


def test_login_rejects_invalid_credentials_with_the_same_response(auth_client) -> None:
    client, _ = auth_client
    client.post(
        "/api/v1/auth/register",
        json={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "ada@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )

    wrong_password = client.post(
        "/api/v1/auth/login",
        json={"email": "ada@example.com", "password": "incorrect-password"},
    )
    unknown_email = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": "incorrect-password"},
    )

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
