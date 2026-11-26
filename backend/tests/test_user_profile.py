from uuid import UUID

import pytest

from app.modules.auth.models import User


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
