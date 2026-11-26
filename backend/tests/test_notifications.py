from collections.abc import Iterator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.modules.auth.cookies import ACCESS_TOKEN_COOKIE
from app.modules.auth.models import RefreshToken, RevokedToken, Role, RoleAssignment, User
from app.modules.notifications.models import Notification


@pytest.fixture()
def notification_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        "test-jwt-secret-for-tests-at-least-32-bytes",
    )
    monkeypatch.setattr(settings, "access_token_expire_minutes", 30)

    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        User.__table__,
        Role.__table__,
        RoleAssignment.__table__,
        RevokedToken.__table__,
        RefreshToken.__table__,
        Notification.__table__,
    ]
    Base.metadata.create_all(engine, tables=tables)
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
        Base.metadata.drop_all(engine, tables=tables)
        engine.dispose()


def register_user(client: TestClient) -> tuple[str, dict[str, str]]:
    response = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Test",
            "lastname": "Notification",
            "email": f"notification_{uuid4().hex[:8]}@example.com",
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )
    assert response.status_code == 201, response.text
    token = response.cookies.get(ACCESS_TOKEN_COOKIE)
    assert token
    return response.json()["id_user"], {"Authorization": f"Bearer {token}"}


def test_get_my_notifications_filters_and_paginates(
    notification_client: tuple[TestClient, sessionmaker[Session]],
):
    client, test_session = notification_client
    user_id, headers = register_user(client)
    user_uuid = UUID(user_id)

    with test_session() as session:
        session.add_all(
            [
                Notification(
                    id_notif=uuid4(),
                    id_user=user_uuid,
                    title="Première",
                    message="Notification lue",
                    is_read=True,
                ),
                Notification(
                    id_notif=uuid4(),
                    id_user=user_uuid,
                    title="Deuxième",
                    message="Notification non lue",
                    is_read=False,
                ),
                Notification(
                    id_notif=uuid4(),
                    id_user=user_uuid,
                    title="Troisième",
                    message="Autre notification non lue",
                    is_read=False,
                ),
            ]
        )
        session.commit()

    response = client.get(
        "/api/v1/notifications/me",
        params={"is_read": "false", "page": 1, "page_size": 1},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["total_pages"] == 2
    assert body["page"] == 1
    assert body["page_size"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["is_read"] is False


def test_get_my_notifications_requires_authentication(
    notification_client: tuple[TestClient, sessionmaker[Session]],
):
    client, _ = notification_client

    response = client.get("/api/v1/notifications/me")

    assert response.status_code == 401
