from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
import pytest
from sqlalchemy import select

from app.config import settings
from app.modules.auth.cookies import ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE
from app.modules.auth.models import RefreshToken, RevokedToken, Role, RoleAssignment, User


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
            record.revoked_at is not None for record in session.scalars(select(RefreshToken)).all()
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
