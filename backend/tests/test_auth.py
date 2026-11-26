from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import JSON, String, create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator

from app.config import settings
from app.core.dependencies import require_campaign_editor
from app.database import Base, get_db
from app.main import app
from app.modules.auth.cookies import ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE
from app.modules.auth.models import RefreshToken, RevokedToken, Role, RoleAssignment, User
from app.modules.campaigns.models import Campaign, Event
from app.modules.financial_donations.models import FinancialDon
from app.modules.natural_donations.models import (
    Collect,
    NaturalDon,
    NaturalDonItem,
    ObjectType,
)
from app.modules.treasury.models import Fund
from app.modules.volunteers.models import Mission, SignIn


class SQLiteArray(TypeDecorator):
    impl = JSON
    cache_ok = True


@pytest.fixture()
def auth_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        "test-jwt-secret-for-tests-at-least-32-bytes",
    )
    monkeypatch.setattr(settings, "access_token_expire_minutes", 15)
    monkeypatch.setattr(settings, "refresh_token_expire_days", 30)
    monkeypatch.setattr(settings, "auth_cookie_secure", False)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    auth_tables = [
        User.__table__,
        Role.__table__,
        RoleAssignment.__table__,
        RevokedToken.__table__,
        RefreshToken.__table__,
    ]
    Base.metadata.create_all(engine, tables=auth_tables)
    test_session = sessionmaker(bind=engine, autoflush=False)
    monkeypatch.setattr("app.main.SessionLocal", test_session)

    def override_get_db() -> Iterator[Session]:
        with test_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client, test_session
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine, tables=auth_tables)
        engine.dispose()


@pytest.fixture()
def user_detail_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        "test-jwt-secret-for-tests-at-least-32-bytes",
    )
    monkeypatch.setattr(settings, "access_token_expire_minutes", 15)
    monkeypatch.setattr(settings, "refresh_token_expire_days", 30)
    monkeypatch.setattr(settings, "auth_cookie_secure", False)
    monkeypatch.setattr(Mission.__table__.c.required_skills, "type", SQLiteArray())
    monkeypatch.setattr(Mission.__table__.c.status, "type", String())
    monkeypatch.setattr(Mission.__table__.c.status, "server_default", None)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    detail_tables = [
        User.__table__,
        Role.__table__,
        RoleAssignment.__table__,
        RevokedToken.__table__,
        RefreshToken.__table__,
        Campaign.__table__,
        Event.__table__,
        FinancialDon.__table__,
        Collect.__table__,
        NaturalDon.__table__,
        NaturalDonItem.__table__,
        ObjectType.__table__,
        Fund.__table__,
        Mission.__table__,
        SignIn.__table__,
    ]
    Base.metadata.create_all(engine, tables=detail_tables)
    test_session = sessionmaker(bind=engine, autoflush=False)
    monkeypatch.setattr("app.main.SessionLocal", test_session)

    def override_get_db() -> Iterator[Session]:
        with test_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client, test_session
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine, tables=detail_tables)
        engine.dispose()


def test_registration_creates_user_and_sets_a_persistent_http_only_cookie(auth_client) -> None:
    client, test_session = auth_client
    response = client.post(
        "/api/v1/auth/register",
        data={
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
    assert response.json()["image_url"] is None
    assert "access_token" not in response.json()
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "max-age=2592000" in response.headers["set-cookie"].lower()
    assert "max-age=900" in response.headers["set-cookie"].lower()
    access_token = response.cookies.get(ACCESS_TOKEN_COOKIE)
    refresh_token = response.cookies.get(REFRESH_TOKEN_COOKIE)
    assert access_token
    assert refresh_token
    claims = jwt.decode(
        access_token,
        "test-jwt-secret-for-tests-at-least-32-bytes",
        algorithms=["HS256"],
    )
    assert claims["sub"] == response.json()["id_user"]
    assert claims["exp"] - claims["iat"] == 15 * 60

    with test_session() as session:
        user = session.scalar(select(User).where(User.email == "ada@example.com"))
        assert user is not None
        assert user.password_hash != "a-very-strong-password"
        stored_refresh_token = session.scalar(select(RefreshToken))
        assert stored_refresh_token is not None
        assert stored_refresh_token.token_hash != refresh_token


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
        client.post("/api/v1/auth/register", data=payload)

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

    created = client.post("/api/v1/auth/register", data=payload)
    duplicate = client.post(
        "/api/v1/auth/register",
        data=payload,
    )

    assert created.status_code == 201
    assert duplicate.status_code == 409
    with test_session() as session:
        assert len(session.scalars(select(User)).all()) == 1


@pytest.mark.parametrize("domain", ["gmail.com", "example.com"])
def test_registration_accepts_allowed_email_domains(auth_client, domain: str) -> None:
    client, _ = auth_client

    response = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": f"ada@{domain}",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )

    assert response.status_code == 201


@pytest.mark.parametrize("email", ["ada@outlook.com", "ada@mail.gmail.com"])
def test_registration_rejects_other_email_domains(auth_client, email: str) -> None:
    client, _ = auth_client

    response = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": email,
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )

    assert response.status_code == 422


def test_login_returns_a_persistent_http_only_cookie_for_valid_credentials(auth_client) -> None:
    client, _ = auth_client
    registration = client.post(
        "/api/v1/auth/register",
        data={
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
            "remember_me": True,
        },
    )

    assert registration.status_code == 201
    assert response.status_code == 200
    assert response.json() == {"message": "Connexion réussie."}
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "max-age=2592000" in response.headers["set-cookie"].lower()
    assert "max-age=900" in response.headers["set-cookie"].lower()
    access_token = response.cookies.get(ACCESS_TOKEN_COOKIE)
    refresh_token = response.cookies.get(REFRESH_TOKEN_COOKIE)
    assert access_token
    assert refresh_token
    claims = jwt.decode(
        access_token,
        "test-jwt-secret-for-tests-at-least-32-bytes",
        algorithms=["HS256"],
    )
    assert claims["sub"] == registration.json()["id_user"]
    assert claims["exp"] - claims["iat"] == 15 * 60


def test_login_uses_a_session_cookie_when_remember_me_is_false(auth_client) -> None:
    client, _ = auth_client
    client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "session@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "session@example.com",
            "password": "a-very-strong-password",
            "remember_me": False,
        },
    )

    assert response.status_code == 200
    assert response.cookies.get(ACCESS_TOKEN_COOKIE)
    assert response.cookies.get(REFRESH_TOKEN_COOKIE)
    assert "max-age=" not in response.headers["set-cookie"].lower()


def test_refresh_rotates_tokens_and_revokes_the_family_on_reuse(auth_client) -> None:
    client, test_session = auth_client
    registration = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "refresh@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )
    old_refresh_token = registration.cookies.get(REFRESH_TOKEN_COOKIE)
    assert old_refresh_token

    refreshed = client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "http://localhost:5173"},
    )

    assert refreshed.status_code == 200
    assert refreshed.json() == {"message": "Session renouvelée."}
    new_refresh_token = refreshed.cookies.get(REFRESH_TOKEN_COOKIE)
    new_access_token = refreshed.cookies.get(ACCESS_TOKEN_COOKIE)
    assert new_refresh_token and new_refresh_token != old_refresh_token
    assert new_access_token
    access_claims = jwt.decode(
        new_access_token,
        "test-jwt-secret-for-tests-at-least-32-bytes",
        algorithms=["HS256"],
    )
    assert access_claims["exp"] - access_claims["iat"] == 15 * 60
    assert client.get("/api/v1/users/me").status_code == 200

    with test_session() as session:
        token_records = list(session.scalars(select(RefreshToken)).all())
        assert len(token_records) == 2
        assert token_records[0].family_id == token_records[1].family_id
        assert sum(record.revoked_at is not None for record in token_records) == 1

    reused = client.post(
        "/api/v1/auth/refresh",
        headers={
            "Origin": "http://localhost:5173",
            "Cookie": f"{REFRESH_TOKEN_COOKIE}={old_refresh_token}",
        },
    )
    family_after_reuse = client.post(
        "/api/v1/auth/refresh",
        headers={
            "Origin": "http://localhost:5173",
            "Cookie": f"{REFRESH_TOKEN_COOKIE}={new_refresh_token}",
        },
    )

    assert reused.status_code == 401
    assert family_after_reuse.status_code == 401
    with test_session() as session:
        assert all(
            record.revoked_at is not None
            for record in session.scalars(select(RefreshToken)).all()
        )


def test_refresh_rejects_missing_cookie_and_untrusted_origin(auth_client) -> None:
    client, _ = auth_client

    missing_cookie = client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "http://localhost:5173"},
    )
    untrusted_origin = client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "https://untrusted.example"},
    )

    assert missing_cookie.status_code == 401
    assert "max-age=0" in missing_cookie.headers["set-cookie"].lower()
    assert untrusted_origin.status_code == 403


def test_refresh_rejects_an_expired_refresh_token(auth_client) -> None:
    client, test_session = auth_client
    registration = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "expired-refresh@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )
    refresh_token = registration.cookies.get(REFRESH_TOKEN_COOKIE)
    assert refresh_token

    with test_session() as session:
        token_record = session.scalar(select(RefreshToken))
        assert token_record is not None
        token_record.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        session.commit()

    response = client.post(
        "/api/v1/auth/refresh",
        headers={
            "Origin": "http://localhost:5173",
            "Cookie": f"{REFRESH_TOKEN_COOKIE}={refresh_token}",
        },
    )

    assert response.status_code == 401


def test_current_session_keeps_an_unassigned_user_roleless(auth_client) -> None:
    client, _ = auth_client
    registration = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "visitor@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )

    response = client.get("/api/v1/users/me")

    assert response.status_code == 200
    assert response.json()["id_user"] == registration.json()["id_user"]
    assert response.json()["user"] == {
        "id_user": registration.json()["id_user"],
        "firstname": "Ada",
        "lastname": "Lovelace",
        "nickname": None,
        "email": "visitor@example.com",
        "tel": "0612345678",
        "image_url": None,
        "active": True,
        "created_at": response.json()["user"]["created_at"],
    }
    assert response.json()["roles"] == []


def test_current_session_returns_only_active_roles(auth_client) -> None:
    client, test_session = auth_client
    registration = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "volunteer@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )
    user_id = UUID(registration.json()["id_user"])

    with test_session() as session:
        volunteer_role = Role(role_name="Volunteer")
        manager_role = Role(role_name="Collection_Manager")
        session.add_all([volunteer_role, manager_role])
        session.flush()
        session.add_all(
            [
                RoleAssignment(
                    id_user=user_id,
                    id_role=volunteer_role.id_role,
                    assignment_type="assigned",
                ),
                RoleAssignment(
                    id_user=user_id,
                    id_role=manager_role.id_role,
                    assignment_type="revoked",
                ),
            ]
        )
        session.commit()

    response = client.get("/api/v1/users/me")

    assert response.status_code == 200
    assert response.json()["user"]["email"] == "volunteer@example.com"
    assert response.json()["roles"] == ["Volunteer"]


def test_admin_can_search_filter_and_paginate_users(auth_client) -> None:
    client, test_session = auth_client
    admin_id, admin_token = _register_test_user(client, "admin-list@example.com")
    active_id, _ = _register_test_user(client, "nadia@example.com")
    inactive_id, _ = _register_test_user(client, "omar@gmail.com")
    _assign_administrator_role(test_session, admin_id)

    with test_session() as session:
        active_user = session.get(User, active_id)
        inactive_user = session.get(User, inactive_id)
        assert active_user is not None
        assert inactive_user is not None
        active_user.firstname = "Nadia"
        active_user.lastname = "Bousamedi"
        inactive_user.firstname = "Omar"
        inactive_user.lastname = "Khalil"
        inactive_user.active = False
        session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    by_name = client.get(
        "/api/v1/users?search=Nadia%20Bousamedi&active=true",
        headers=headers,
    )
    by_email_and_state = client.get(
        "/api/v1/users?search=omar@gmail.com&active=false",
        headers=headers,
    )
    first_page = client.get("/api/v1/users?limit=1&offset=0", headers=headers)
    second_page = client.get("/api/v1/users?limit=1&offset=1", headers=headers)

    assert by_name.status_code == 200
    assert [user["id_user"] for user in by_name.json()] == [str(active_id)]
    assert by_email_and_state.status_code == 200
    assert [user["id_user"] for user in by_email_and_state.json()] == [str(inactive_id)]
    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert len(first_page.json()) == 1
    assert len(second_page.json()) == 1
    assert first_page.json()[0]["id_user"] != second_page.json()[0]["id_user"]
    assert "password_hash" not in first_page.json()[0]


def test_user_list_requires_administrator(auth_client) -> None:
    client, _ = auth_client
    _, token = _register_test_user(client, "regular-user@example.com")

    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_profile_update_changes_only_submitted_fields_and_normalizes_email(auth_client) -> None:
    client, _ = auth_client
    client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "profile@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )

    response = client.patch(
        "/api/v1/users/me",
        json={
            "firstname": " Grace ",
            "email": " Grace@Example.com ",
            "tel": "0712345678",
        },
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 200
    assert response.json()["firstname"] == "Grace"
    assert response.json()["lastname"] == "Lovelace"
    assert response.json()["email"] == "grace@example.com"
    assert response.json()["tel"] == "0712345678"

    cleared_phone = client.patch(
        "/api/v1/users/me",
        json={"tel": None},
        headers={"Origin": "http://localhost:5173"},
    )

    assert cleared_phone.status_code == 200
    assert cleared_phone.json()["tel"] is None


def test_profile_update_rejects_duplicate_email(auth_client) -> None:
    client, test_session = auth_client
    client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "first@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )
    second_user = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Grace",
            "lastname": "Hopper",
            "email": "second@example.com",
            "password": "a-very-strong-password",
            "tel": "0712345678",
        },
    )

    response = client.patch(
        "/api/v1/users/me",
        json={"email": "FIRST@example.com"},
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Un compte utilise déjà cette adresse e-mail."
    with test_session() as session:
        user = session.get(User, UUID(second_user.json()["id_user"]))
        assert user is not None
        assert user.email == "second@example.com"


def test_profile_update_requires_a_trusted_origin(auth_client) -> None:
    client, _ = auth_client
    client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "profile-origin@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )

    response = client.patch(
        "/api/v1/users/me",
        json={"firstname": "Grace"},
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"firstname": "A"},
        {"lastname": None},
        {"email": "adresse-invalide"},
        {"email": "profile@outlook.com"},
        {"tel": "1234567890"},
    ],
)
def test_profile_update_rejects_invalid_fields(auth_client, payload) -> None:
    client, _ = auth_client
    client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "profile-validation@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )

    response = client.patch(
        "/api/v1/users/me",
        json=payload,
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 422


def test_password_change_verifies_current_password_and_saves_new_password(auth_client) -> None:
    client, _ = auth_client
    client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "password-change@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )

    response = client.patch(
        "/api/v1/users/me/password",
        json={
            "current_password": "a-very-strong-password",
            "new_password": "a-different-strong-password",
            "confirm_new_password": "a-different-strong-password",
        },
        headers={"Origin": "http://localhost:5173"},
    )
    old_password_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "password-change@example.com",
            "password": "a-very-strong-password",
        },
    )
    new_password_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "password-change@example.com",
            "password": "a-different-strong-password",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Mot de passe modifié avec succès."}
    assert old_password_login.status_code == 401
    assert new_password_login.status_code == 200


def test_password_change_rejects_incorrect_current_password(auth_client) -> None:
    client, _ = auth_client
    client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "wrong-current-password@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )

    response = client.patch(
        "/api/v1/users/me/password",
        json={
            "current_password": "incorrect-current-password",
            "new_password": "a-different-strong-password",
            "confirm_new_password": "a-different-strong-password",
        },
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Le mot de passe actuel est incorrect."


def test_password_change_requires_a_trusted_origin(auth_client) -> None:
    client, _ = auth_client
    client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "password-origin@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )

    response = client.patch(
        "/api/v1/users/me/password",
        json={
            "current_password": "a-very-strong-password",
            "new_password": "a-different-strong-password",
            "confirm_new_password": "a-different-strong-password",
        },
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "new_password,confirmation",
    [
        ("short", "short"),
        ("a-different-strong-password", "another-strong-password"),
    ],
)
def test_password_change_rejects_weak_or_unconfirmed_password(
    auth_client,
    new_password: str,
    confirmation: str,
) -> None:
    client, _ = auth_client
    client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "invalid-password-change@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )

    response = client.patch(
        "/api/v1/users/me/password",
        json={
            "current_password": "a-very-strong-password",
            "new_password": new_password,
            "confirm_new_password": confirmation,
        },
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 422


def test_cookie_logout_requires_a_trusted_origin_and_clears_the_cookie(auth_client) -> None:
    client, _ = auth_client
    client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "cookie-logout@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )

    blocked = client.post("/api/v1/auth/logout")
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Origin": "http://localhost:5173"},
    )

    assert blocked.status_code == 403
    assert response.status_code == 200
    assert "max-age=0" in response.headers["set-cookie"].lower()


def test_login_rejects_invalid_credentials_with_the_same_response(auth_client) -> None:
    client, _ = auth_client
    client.post(
        "/api/v1/auth/register",
        data={
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


def test_logout_revokes_only_the_current_token(auth_client) -> None:
    client, test_session = auth_client
    registration = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "logout@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )
    first_token = registration.cookies.get(ACCESS_TOKEN_COOKIE)
    second_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "logout@example.com",
            "password": "a-very-strong-password",
            "remember_me": True,
        },
    )
    second_token = second_login.cookies.get(ACCESS_TOKEN_COOKIE)
    second_refresh_token = second_login.cookies.get(REFRESH_TOKEN_COOKIE)
    assert first_token and second_token
    assert second_refresh_token

    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {first_token}"},
    )
    repeated_logout = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {first_token}"},
    )
    other_session_logout = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {second_token}"},
    )

    assert logout_response.status_code == 200
    assert logout_response.json() == {"message": "Déconnexion réussie."}
    assert repeated_logout.status_code == 401
    assert other_session_logout.status_code == 200
    rejected_refresh = client.post(
        "/api/v1/auth/refresh",
        headers={
            "Origin": "http://localhost:5173",
            "Cookie": f"{REFRESH_TOKEN_COOKIE}={second_refresh_token}",
        },
    )
    assert rejected_refresh.status_code == 401

    with test_session() as session:
        assert len(session.scalars(select(RevokedToken)).all()) == 2


@pytest.mark.parametrize(
    ("role_name", "assignment_type", "allowed"),
    [
        ("Collection_Manager", "assigned", True),
        ("Administrator", "assigned", True),
        ("Volunteer", "assigned", False),
        ("Collection_Manager", "revoked", False),
    ],
)
def test_campaign_editor_requires_an_active_campaign_role(
    auth_client, role_name: str, assignment_type: str, allowed: bool
) -> None:
    _, test_session = auth_client
    with test_session() as session:
        user = User(
            firstname="Ada",
            lastname="Lovelace",
            email=f"{role_name.lower()}-{assignment_type}@example.com",
            password_hash="not-used",
        )
        role = Role(role_name=role_name)
        session.add_all([user, role])
        session.flush()
        session.add(
            RoleAssignment(
                id_user=user.id_user,
                id_role=role.id_role,
                assignment_type=assignment_type,
            )
        )
        session.commit()

        if allowed:
            assert require_campaign_editor(user, session) is user
        else:
            with pytest.raises(HTTPException) as exc_info:
                require_campaign_editor(user, session)
            assert exc_info.value.status_code == 403


def test_unassigned_user_cannot_close_a_campaign(auth_client) -> None:
    client, _ = auth_client
    registration = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": "ada@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )

    response = client.post(
        "/api/v1/campaigns/00000000-0000-0000-0000-000000000001/close",
        headers={
            "Authorization": f"Bearer {registration.cookies.get(ACCESS_TOKEN_COOKIE)}"
        },
    )

    assert response.status_code == 403


def _register_test_user(client: TestClient, email: str) -> tuple[UUID, str]:
    response = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Ada",
            "lastname": "Lovelace",
            "email": email,
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )
    assert response.status_code == 201
    token = response.cookies.get(ACCESS_TOKEN_COOKIE)
    assert token
    return UUID(response.json()["id_user"]), token


def _assign_administrator_role(test_session, user_id: UUID) -> None:
    with test_session() as session:
        user = session.get(User, user_id)
        role = Role(role_name="Administrator")
        session.add(role)
        session.flush()
        session.add(
            RoleAssignment(
                id_user=user.id_user,
                id_role=role.id_role,
                assignment_type="assigned",
            )
        )
        session.commit()


def test_administrator_can_assign_revoke_and_list_user_roles(auth_client) -> None:
    client, test_session = auth_client
    admin_id, admin_token = _register_test_user(client, "admin@example.com")
    target_id, _ = _register_test_user(client, "target@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {admin_token}"}
    endpoint = f"/api/v1/admin/users/{target_id}/roles/Collection_Manager"

    role_catalog = client.get("/api/v1/admin/roles", headers=headers)
    assigned = client.post(
        endpoint,
        headers=headers,
        json={"assignment_type": "assigned"},
    )

    assert role_catalog.status_code == 200
    assert "Administrator" in role_catalog.json()
    assert assigned.status_code == 200
    assert assigned.json()["role_name"] == "Collection_Manager"
    assert assigned.json()["assignment_type"] == "assigned"

    with test_session() as session:
        target = session.get(User, target_id)
        assert require_campaign_editor(target, session) is target

    revoked = client.post(
        endpoint,
        headers=headers,
        json={"assignment_type": "revoked"},
    )
    listed = client.get(
        f"/api/v1/admin/users/{target_id}/roles",
        headers=headers,
    )

    assert revoked.status_code == 200
    assert revoked.json()["assignment_type"] == "revoked"
    assert listed.status_code == 200
    assert listed.json()[0]["assignment_type"] == "revoked"
    with test_session() as session:
        target = session.get(User, target_id)
        with pytest.raises(HTTPException) as exc_info:
            require_campaign_editor(target, session)
        assert exc_info.value.status_code == 403


def test_administrator_removes_role_by_catalog_id_and_preserves_history(auth_client) -> None:
    client, test_session = auth_client
    admin_id, admin_token = _register_test_user(client, "role-delete-admin@example.com")
    target_id, _ = _register_test_user(client, "role-delete-target@example.com")
    _, non_admin_token = _register_test_user(client, "role-delete-non-admin@example.com")
    _assign_administrator_role(test_session, admin_id)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    assigned = client.post(
        f"/api/v1/admin/users/{target_id}/roles/Volunteer",
        headers=admin_headers,
        json={"assignment_type": "assigned"},
    )
    assert assigned.status_code == 200
    role_id = assigned.json()["id_role"]
    endpoint = f"/api/v1/users/{target_id}/roles/{role_id}"

    revoked = client.delete(endpoint, headers=admin_headers)
    repeated_revocation = client.delete(endpoint, headers=admin_headers)

    assert revoked.status_code == 200
    assert revoked.json()["id_user"] == str(target_id)
    assert revoked.json()["id_role"] == role_id
    assert revoked.json()["assignment_type"] == "revoked"
    assert revoked.json()["created_at"]
    assert repeated_revocation.status_code == 200
    assert repeated_revocation.json()["id_role_assignment"] == revoked.json()[
        "id_role_assignment"
    ]
    forbidden = client.delete(
        endpoint,
        headers={"Authorization": f"Bearer {non_admin_token}"},
    )
    assert forbidden.status_code == 403

    with test_session() as session:
        history = session.scalars(
            select(RoleAssignment)
            .where(
                RoleAssignment.id_user == target_id,
                RoleAssignment.id_role == UUID(role_id),
            )
        ).all()
        assert len(history) == 2
        assert {assignment.assignment_type for assignment in history} == {
            "assigned",
            "revoked",
        }


def test_non_administrator_cannot_assign_roles(auth_client) -> None:
    client, _ = auth_client
    _, token = _register_test_user(client, "user@example.com")

    response = client.post(
        "/api/v1/admin/users/00000000-0000-0000-0000-000000000001/roles/Collection_Manager",
        headers={"Authorization": f"Bearer {token}"},
        json={"assignment_type": "assigned"},
    )

    assert response.status_code == 403


def test_administrator_cannot_revoke_the_last_administrator(auth_client) -> None:
    client, test_session = auth_client
    admin_id, token = _register_test_user(client, "only-admin@example.com")
    _assign_administrator_role(test_session, admin_id)
    with test_session() as session:
        administrator_role = session.scalar(
            select(Role).where(Role.role_name == "Administrator")
        )

    response = client.post(
        f"/api/v1/admin/users/{admin_id}/roles/Administrator",
        headers={"Authorization": f"Bearer {token}"},
        json={"assignment_type": "revoked"},
    )
    delete_response = client.delete(
        f"/api/v1/users/{admin_id}/roles/{administrator_role.id_role}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert delete_response.status_code == 409


def test_administrator_can_toggle_non_admin_accounts_only(auth_client) -> None:
    client, test_session = auth_client
    admin_id, admin_token = _register_test_user(client, "activation-admin@example.com")
    target_id, target_token = _register_test_user(client, "activation-target@example.com")
    protected_admin_id, _ = _register_test_user(client, "protected-admin@example.com")
    other_user_id, other_user_token = _register_test_user(client, "activation-other@example.com")
    _assign_administrator_role(test_session, admin_id)

    with test_session() as session:
        administrator_role = session.scalar(
            select(Role).where(Role.role_name == "Administrator")
        )
        session.add(
            RoleAssignment(
                id_user=protected_admin_id,
                id_role=administrator_role.id_role,
                assignment_type="assigned",
            )
        )
        session.commit()

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    endpoint = f"/api/v1/users/{target_id}/activation"
    deactivated = client.patch(endpoint, headers=admin_headers, json={"active": False})

    assert deactivated.status_code == 200
    assert deactivated.json()["active"] is False
    assert client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {target_token}"},
    ).status_code == 401

    with test_session() as session:
        refresh_tokens = session.scalars(
            select(RefreshToken).where(RefreshToken.id_user == target_id)
        ).all()
        assert refresh_tokens
        assert all(token.revoked_at is not None for token in refresh_tokens)

    reactivated = client.patch(endpoint, headers=admin_headers, json={"active": True})
    protected_admin = client.patch(
        f"/api/v1/users/{protected_admin_id}/activation",
        headers=admin_headers,
        json={"active": False},
    )
    forbidden = client.patch(
        f"/api/v1/users/{target_id}/activation",
        headers={"Authorization": f"Bearer {other_user_token}"},
        json={"active": False},
    )
    missing = client.patch(
        f"/api/v1/users/{uuid4()}/activation",
        headers=admin_headers,
        json={"active": False},
    )

    assert reactivated.status_code == 200
    assert reactivated.json()["active"] is True
    assert protected_admin.status_code == 409
    assert forbidden.status_code == 403
    assert missing.status_code == 404
    with test_session() as session:
        protected_admin = session.get(User, protected_admin_id)
        assert protected_admin is not None
        assert protected_admin.active is True


def test_administrator_can_get_user_detail_with_related_records(user_detail_client) -> None:
    client, test_session = user_detail_client
    admin_id, admin_token = _register_test_user(client, "detail-admin@example.com")
    target_id, target_token = _register_test_user(client, "detail-user@example.com")
    _assign_administrator_role(test_session, admin_id)

    with test_session() as session:
        volunteer_role = Role(role_name="Volunteer")
        session.add(volunteer_role)
        session.flush()
        session.add(
            RoleAssignment(
                id_user=target_id,
                id_role=volunteer_role.id_role,
                assignment_type="assigned",
            )
        )
        campaign = Campaign(title="Campaign by target", id_user=target_id)
        collect = Collect(
            place="Community center",
            planned_at=datetime.now(UTC),
            id_user=target_id,
        )
        session.add_all([campaign, collect])
        session.flush()

        mission = Mission(
            id_mission=uuid4(),
            title="Mission by target",
            required_skills=["organization"],
            status="Publish",
            id_collect=collect.id_collect,
        )
        session.add(mission)
        session.add(SignIn(id_user=target_id, id_mission=mission.id_mission))
        session.add(
            FinancialDon(
                amount=Decimal("25.00"),
                status="Success",
                id_user=target_id,
                id_campaign=campaign.id_campaign,
            )
        )
        user_donation = NaturalDon(
            recovery_mode="Deposit",
            id_user=target_id,
            id_campaign=campaign.id_campaign,
        )
        actor_donation = NaturalDon(
            recovery_mode="Collect",
            id_user=admin_id,
            validated_by=target_id,
        )
        session.add_all([user_donation, actor_donation])
        session.flush()
        session.add(
            NaturalDonItem(
                id_don_n=user_donation.id_don_n,
                id_nat=uuid4(),
                description="Winter coat",
            )
        )
        session.add(
            Fund(
                amount=Decimal("12.50"),
                category="Expense",
                transaction_at=datetime.now(UTC),
                id_user=target_id,
            )
        )
        session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get(f"/api/v1/users/{target_id}", headers=headers)

    assert response.status_code == 200
    detail = response.json()
    assert detail["id_user"] == str(target_id)
    assert detail["role_assignments"][0]["role_name"] == "Volunteer"
    assert len(detail["campaigns"]) == 1
    assert detail["mission_sign_ins"][0]["mission"]["title"] == "Mission by target"
    assert len(detail["financial_donations"]) == 1
    assert len(detail["natural_donations"]) == 2
    assert any(donation["items"] for donation in detail["natural_donations"])
    assert len(detail["collections"]) == 1
    assert len(detail["treasury_operations"]) == 1
    assert "password_hash" not in detail
    assert "refresh_tokens" not in detail

    forbidden = client.get(
        f"/api/v1/users/{target_id}",
        headers={"Authorization": f"Bearer {target_token}"},
    )
    missing = client.get(
        f"/api/v1/users/{uuid4()}",
        headers=headers,
    )
    assert forbidden.status_code == 403
    assert missing.status_code == 404


# ============================================================
# Image utilisateur à l'inscription et modification ultérieure
# ============================================================


@patch("app.modules.auth.service.convert_image_to_webp")
@patch("app.modules.auth.service.supabase_admin")
def test_registration_uploads_optional_profile_image(
    mock_supabase,
    mock_convert,
    auth_client,
) -> None:
    """L'inscription accepte une photo facultative et retourne son URL."""
    client, test_session = auth_client
    mock_convert.return_value = b"fake_webp"
    fake_url = "https://mock.supabase.co/storage/v1/object/public/users/avatar.webp"
    mock_supabase.storage.from_().get_public_url.return_value = fake_url

    response = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Jane",
            "lastname": "Doe",
            "email": "jane@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
        files={"image": ("avatar.png", b"fake_png", "image/png")},
    )

    assert response.status_code == 201
    assert response.json()["image_url"] == fake_url
    user_id = UUID(response.json()["id_user"])
    mock_supabase.storage.from_().upload.assert_called_once_with(
        path=f"{user_id}/avatar.webp",
        file=b"fake_webp",
        file_options={
            "content-type": "image/webp",
            "upsert": "false",
        },
    )

    with test_session() as session:
        user = session.get(User, user_id)
        assert user.image_url == fake_url


@patch("app.modules.auth.service.supabase_admin")
@patch("app.modules.auth.service.convert_image_to_webp")
def test_registration_does_not_create_user_when_avatar_upload_fails(
    mock_convert,
    mock_supabase,
    auth_client,
) -> None:
    client, test_session = auth_client
    mock_convert.return_value = b"fake_webp"
    mock_supabase.storage.from_().upload.side_effect = RuntimeError("Storage unavailable")

    with pytest.raises(RuntimeError, match="Storage unavailable"):
        client.post(
            "/api/v1/auth/register",
            data={
                "firstname": "Jane",
                "lastname": "Doe",
                "email": "jane-storage-error@example.com",
                "password": "a-very-strong-password",
                "tel": "0612345678",
            },
            files={"image": ("avatar.png", b"fake_png", "image/png")},
        )

    with test_session() as session:
        assert session.scalar(select(User)) is None


def test_aut09_rejects_non_image(auth_client) -> None:
    """L'inscription refuse un fichier qui n'est pas une image."""
    client, test_session = auth_client
    response = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Jane",
            "lastname": "Doe",
            "email": "jane3@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
        files={"image": ("doc.txt", b"not_an_image", "text/plain")},
    )

    assert response.status_code == 400
    with test_session() as session:
        assert session.scalar(select(User)) is None


@patch("app.modules.auth.service.convert_image_to_webp")
@patch("app.modules.auth.service.supabase_admin")
def test_aut09_user_image_route_uses_auth_prefix(
    mock_supabase,
    mock_convert,
    auth_client,
) -> None:
    client, _ = auth_client
    mock_convert.return_value = b"fake_webp"
    mock_supabase.storage.from_().get_public_url.return_value = (
        "https://mock.supabase.co/storage/v1/object/public/users/avatar.webp"
    )

    registration = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Jane",
            "lastname": "Doe",
            "email": "jane-image@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )
    user_id = registration.json()["id_user"]

    response = client.post(
        f"/api/v1/auth/{user_id}/image",
        files={"image": ("avatar.png", b"fake_png", "image/png")},
    )
    users_route_response = client.post(
        f"/api/v1/users/{user_id}/image",
        files={"image": ("avatar.png", b"fake_png", "image/png")},
    )

    assert response.status_code == 200
    assert users_route_response.status_code == 405


@patch("app.modules.auth.service.convert_image_to_webp")
@patch("app.modules.auth.service.supabase_admin")
def test_aut10_user_can_replace_own_image_on_users_route(
    mock_supabase,
    mock_convert,
    auth_client,
) -> None:
    """AUT-10 : L'utilisateur peut remplacer sa propre photo."""
    client, test_session = auth_client
    res = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Jane",
            "lastname": "Doe",
            "email": "jane4@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )
    user_id = UUID(res.json()["id_user"])
    token = res.cookies.get(ACCESS_TOKEN_COOKIE)
    assert token

    mock_convert.return_value = b"fake_webp"
    new_url = "https://mock.supabase.co/storage/v1/object/public/users/new.webp"
    mock_supabase.storage.from_().get_public_url.return_value = new_url

    response = client.patch(
        f"/api/v1/users/{user_id}/image",
        files={"image": ("avatar.png", b"fake_png", "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["image_url"] == new_url

    auth_route_response = client.patch(
        f"/api/v1/auth/{user_id}/image",
        files={"image": ("avatar.png", b"fake_png", "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert auth_route_response.status_code == 405


def test_aut10_rejects_other_user(auth_client) -> None:
    """AUT-10 : 403 si un utilisateur modifie la photo d'un autre."""
    client, _ = auth_client

    res1 = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Alice",  # 👈 était "A" (1 char → 422)
            "lastname": "One",
            "email": "user1@example.com",
            "password": "a-very-strong-password",
            "tel": "0600000001",
        },
    )
    assert res1.status_code == 201  # 👈 vérifie le statut avant .json()
    token1 = res1.cookies.get(ACCESS_TOKEN_COOKIE)
    assert token1

    res2 = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Bob",  # 👈 était "B" (1 char → 422)
            "lastname": "Two",
            "email": "user2@example.com",
            "password": "a-very-strong-password",
            "tel": "0600000002",
        },
    )
    assert res2.status_code == 201
    user2_id = UUID(res2.json()["id_user"])

    response = client.patch(
        f"/api/v1/users/{user2_id}/image",
        files={"image": ("avatar.png", b"fake", "image/png")},
        headers={"Authorization": f"Bearer {token1}"},
    )

    assert response.status_code == 403
