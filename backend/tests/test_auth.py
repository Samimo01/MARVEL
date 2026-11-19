from collections.abc import Iterator
from unittest.mock import patch
from uuid import UUID

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.core.dependencies import require_campaign_editor
from app.database import Base, get_db
from app.main import app
from app.modules.auth.models import RevokedToken, Role, RoleAssignment, User


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
    auth_tables = [
        User.__table__,
        Role.__table__,
        RoleAssignment.__table__,
        RevokedToken.__table__,
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


def test_registration_creates_user_and_returns_access_token(auth_client) -> None:
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


def test_login_returns_a_persistent_access_token_for_valid_credentials(auth_client) -> None:
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
    first_token = registration.json()["access_token"]
    second_token = client.post(
        "/api/v1/auth/login",
        json={
            "email": "logout@example.com",
            "password": "a-very-strong-password",
        },
    ).json()["access_token"]

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
        headers={"Authorization": f"Bearer {registration.json()['access_token']}"},
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
    return UUID(response.json()["id_user"]), response.json()["access_token"]


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


def test_non_administrator_cannot_assign_roles(auth_client) -> None:
    client, _ = auth_client
    _, token = _register_test_user(client, "user@example.com")

    response = client.post(
        "/api/v1/admin/users/00000000-0000-0000-0000-000000000001"
        "/roles/Collection_Manager",
        headers={"Authorization": f"Bearer {token}"},
        json={"assignment_type": "assigned"},
    )

    assert response.status_code == 403


def test_administrator_cannot_revoke_the_last_administrator(auth_client) -> None:
    client, test_session = auth_client
    admin_id, token = _register_test_user(client, "only-admin@example.com")
    _assign_administrator_role(test_session, admin_id)

    response = client.post(
        f"/api/v1/admin/users/{admin_id}/roles/Administrator",
        headers={"Authorization": f"Bearer {token}"},
        json={"assignment_type": "revoked"},
    )

    assert response.status_code == 409

# ============================================================
# Image utilisateur à l'inscription et modification ultérieure
# ============================================================

@patch("app.modules.auth.service.convert_image_to_webp")
@patch("app.modules.auth.service.supabase_admin")
def test_registration_uploads_optional_profile_image(
    mock_supabase, mock_convert, auth_client,
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
    mock_convert, mock_supabase, auth_client,
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


def test_public_user_image_route_is_removed(auth_client) -> None:
    client, _ = auth_client

    response = client.post(
        "/api/v1/auth/00000000-0000-0000-0000-000000000001/image",
        files={"image": ("avatar.png", b"fake_png", "image/png")},
    )

    assert response.status_code == 404


@patch("app.modules.auth.service.convert_image_to_webp")
@patch("app.modules.auth.service.supabase_admin")
def test_aut10_user_can_replace_own_image(
    mock_supabase, mock_convert, auth_client,
) -> None:
    """AUT-10 : L'utilisateur peut remplacer sa propre photo."""
    client, test_session = auth_client
    res = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Jane", "lastname": "Doe",
            "email": "jane4@example.com", "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )
    user_id = UUID(res.json()["id_user"])
    token = res.json()["access_token"]

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


def test_aut10_rejects_other_user(auth_client) -> None:
    """AUT-10 : 403 si un utilisateur modifie la photo d'un autre."""
    client, _ = auth_client

    res1 = client.post("/api/v1/auth/register", data={
        "firstname": "Alice",   # 👈 était "A" (1 char → 422)
        "lastname": "One",
        "email": "user1@example.com",
        "password": "a-very-strong-password",
        "tel": "0600000001",
    })
    assert res1.status_code == 201  # 👈 vérifie le statut avant .json()
    token1 = res1.json()["access_token"]

    res2 = client.post("/api/v1/auth/register", data={
        "firstname": "Bob",     # 👈 était "B" (1 char → 422)
        "lastname": "Two",
        "email": "user2@example.com",
        "password": "a-very-strong-password",
        "tel": "0600000002",
    })
    assert res2.status_code == 201
    user2_id = UUID(res2.json()["id_user"])

    response = client.patch(
        f"/api/v1/users/{user2_id}/image",
        files={"image": ("avatar.png", b"fake", "image/png")},
        headers={"Authorization": f"Bearer {token1}"},
    )

    assert response.status_code == 403