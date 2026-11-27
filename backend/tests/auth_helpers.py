from uuid import UUID

from fastapi.testclient import TestClient

from app.modules.auth.cookies import ACCESS_TOKEN_COOKIE
from app.modules.auth.models import Role, RoleAssignment, User


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
