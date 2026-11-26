from unittest.mock import patch
from uuid import UUID

import pytest
from sqlalchemy import select

from app.modules.auth.cookies import ACCESS_TOKEN_COOKIE
from app.modules.auth.models import User
from tests.auth_helpers import _assign_administrator_role, _register_test_user


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
def test_aut09_user_can_add_first_image_after_registration(
    mock_supabase,
    mock_convert,
    auth_client,
) -> None:
    client, _ = auth_client
    response = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Jane",
            "lastname": "Doe",
            "email": "jane-first-image@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )
    user_id = UUID(response.json()["id_user"])
    token = response.cookies.get(ACCESS_TOKEN_COOKIE)
    assert token

    mock_convert.return_value = b"fake_webp"
    image_url = "https://mock.supabase.co/storage/v1/object/public/users/avatar.webp"
    mock_supabase.storage.from_().get_public_url.return_value = image_url

    uploaded = client.post(
        f"/api/v1/auth/{user_id}/image",
        files={"image": ("avatar.png", b"fake_png", "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert uploaded.status_code == 200
    assert uploaded.json()["image_url"] == image_url


def test_aut09_rejects_adding_image_to_another_user(auth_client) -> None:
    client, test_session = auth_client
    _, owner_token = _register_test_user(client, "image-owner@example.com")
    target_id, _ = _register_test_user(client, "image-target@example.com")

    response = client.post(
        f"/api/v1/auth/{target_id}/image",
        files={"image": ("avatar.png", b"fake_png", "image/png")},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 403
    with test_session() as session:
        target = session.get(User, target_id)
        assert target is not None
        assert target.image_url is None


@patch("app.modules.auth.service.convert_image_to_webp")
@patch("app.modules.auth.service.supabase_admin")
def test_aut09_administrator_can_add_first_image_to_another_user(
    mock_supabase,
    mock_convert,
    auth_client,
) -> None:
    client, test_session = auth_client
    admin_id, admin_token = _register_test_user(client, "image-admin@example.com")
    target_id, _ = _register_test_user(client, "image-admin-target@example.com")
    _assign_administrator_role(test_session, admin_id)

    mock_convert.return_value = b"fake_webp"
    image_url = "https://mock.supabase.co/storage/v1/object/public/users/admin-avatar.webp"
    mock_supabase.storage.from_().get_public_url.return_value = image_url

    response = client.post(
        f"/api/v1/auth/{target_id}/image",
        files={"image": ("avatar.png", b"fake_png", "image/png")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["image_url"] == image_url


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
