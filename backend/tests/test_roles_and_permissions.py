from uuid import UUID

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.core.dependencies import require_campaign_editor
from app.modules.auth.cookies import ACCESS_TOKEN_COOKIE
from app.modules.auth.models import Role, RoleAssignment, User
from tests.auth_helpers import _assign_administrator_role, _register_test_user


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
        headers={"Authorization": f"Bearer {registration.cookies.get(ACCESS_TOKEN_COOKIE)}"},
    )

    assert response.status_code == 403


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
    assert repeated_revocation.json()["id_role_assignment"] == revoked.json()["id_role_assignment"]
    forbidden = client.delete(
        endpoint,
        headers={"Authorization": f"Bearer {non_admin_token}"},
    )
    assert forbidden.status_code == 403

    with test_session() as session:
        history = session.scalars(
            select(RoleAssignment).where(
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
        administrator_role = session.scalar(select(Role).where(Role.role_name == "Administrator"))

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
