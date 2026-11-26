from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.modules.auth.models import Role, RoleAssignment, User
from tests.auth_helpers import _assign_administrator_role, _register_test_user


def _assign_role(test_session, user_id, role_name: str, assignment_type: str = "assigned"):
    with test_session() as session:
        role = session.scalar(select(Role).where(Role.role_name == role_name))
        if role is None:
            role = Role(role_name=role_name)
            session.add(role)
            session.flush()
        session.add(
            RoleAssignment(
                id_user=user_id,
                id_role=role.id_role,
                assignment_type=assignment_type,
            )
        )
        session.commit()


def test_list_beneficiary_files_filters_search_status_and_pagination(auth_client) -> None:
    client, test_session = auth_client
    admin_id, admin_token = _register_test_user(client, "beneficiary-admin@example.com")
    _assign_administrator_role(test_session, admin_id)

    with test_session() as session:
        beneficiary_role = Role(role_name="Beneficiary")
        volunteer_role = Role(role_name="Volunteer")
        session.add_all([beneficiary_role, volunteer_role])
        session.flush()
        records = [
            User(
                firstname=firstname,
                lastname="Test",
                email=f"{firstname.lower()}-beneficiary@example.com",
                password_hash="not-used",
                active=active,
                created_at=datetime(2026, 1, day, tzinfo=UTC),
            )
            for firstname, active, day in (
                ("Amina", True, 3),
                ("Brahim", False, 2),
                ("Chloé", True, 1),
            )
        ]
        unrelated = User(
            firstname="Non",
            lastname="Beneficiary",
            email="not-beneficiary@example.com",
            password_hash="not-used",
        )
        session.add_all([*records, unrelated])
        session.flush()
        for index, record in enumerate(records):
            session.add(
                RoleAssignment(
                    id_user=record.id_user,
                    id_role=beneficiary_role.id_role,
                    assignment_type="assigned",
                    created_at=datetime(2026, 1, 1, tzinfo=UTC),
                )
            )
            if index == 2:
                session.add(
                    RoleAssignment(
                        id_user=record.id_user,
                        id_role=beneficiary_role.id_role,
                        assignment_type="revoked",
                        created_at=datetime(2026, 1, 4, tzinfo=UTC),
                    )
                )
        session.add(
            RoleAssignment(
                id_user=unrelated.id_user,
                id_role=volunteer_role.id_role,
                assignment_type="assigned",
            )
        )
        session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    endpoint = "/api/v1/beneficiary-files"

    all_files = client.get(endpoint, headers=headers)
    active_files = client.get(f"{endpoint}?status=Actif", headers=headers)
    suspended_files = client.get(f"{endpoint}?status=Suspendu", headers=headers)
    closed_files = client.get(f"{endpoint}?status=Cl%C3%B4tur%C3%A9", headers=headers)
    search = client.get(f"{endpoint}?search=brah&status=Suspendu", headers=headers)
    page = client.get(f"{endpoint}?limit=1&offset=1", headers=headers)

    assert all_files.status_code == 200
    assert [item["firstname"] for item in all_files.json()] == ["Amina", "Brahim", "Chloé"]
    assert [item["status"] for item in all_files.json()] == ["Actif", "Suspendu", "Clôturé"]
    assert [item["firstname"] for item in active_files.json()] == ["Amina"]
    assert [item["firstname"] for item in suspended_files.json()] == ["Brahim"]
    assert [item["firstname"] for item in closed_files.json()] == ["Chloé"]
    assert [item["firstname"] for item in search.json()] == ["Brahim"]
    assert [item["firstname"] for item in page.json()] == ["Brahim"]


@pytest.mark.parametrize(
    ("role_name", "allowed"),
    [
        ("Collection_Manager", True),
        ("Stock_Manager", True),
        ("Administrator", True),
        ("Treasurer", False),
    ],
)
def test_beneficiary_file_list_requires_an_allowed_role(
    auth_client, role_name: str, allowed: bool
) -> None:
    client, test_session = auth_client
    user_id, token = _register_test_user(
        client,
        f"beneficiary-file-{role_name.lower()}@example.com",
    )
    _assign_role(test_session, user_id, role_name)

    response = client.get(
        "/api/v1/beneficiary-files",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == (200 if allowed else 403)
