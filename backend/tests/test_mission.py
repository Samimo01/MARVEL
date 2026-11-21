"""Tests des routes API Missions et inscriptions des bénévoles : MIS-01 à MIS-15."""

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, String, JSON, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.modules.auth.models import User, Role, RoleAssignment, RevokedToken
from app.modules.campaigns.models import Campaign, Event
from app.modules.natural_donations.models import Collect
from app.modules.volunteers.models import Mission, SignIn


class SQLiteArray(TypeDecorator):
    """Remplace ARRAY PostgreSQL par JSON dans SQLite."""
    impl = JSON
    cache_ok = True


@pytest.fixture()
def mission_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:

    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        "test-jwt-secret-for-tests-at-least-32-bytes",
    )
    monkeypatch.setattr(
        settings,
        "access_token_expire_minutes",
        30 * 24 * 60,
    )

    Mission.__table__.c.skills.type = SQLiteArray()
    Mission.__table__.c.skills.server_default.arg = "'[]'"

    Mission.__table__.c.status.type = String()
    Mission.__table__.c.status.server_default.arg = "'Publish'"

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def register_sqlite_functions(dbapi_connection, connection_record):
        dbapi_connection.create_function(
            "gen_random_uuid",
            0,
            lambda: uuid4().hex,
        )

    test_tables = [
        User.__table__,
        Role.__table__,
        RoleAssignment.__table__,
        RevokedToken.__table__,
        Campaign.__table__,
        Event.__table__,
        Collect.__table__,
        Mission.__table__,
        SignIn.__table__,
    ]

    Base.metadata.create_all(engine, tables=test_tables)

    test_session = sessionmaker(
        bind=engine,
        autoflush=False,
    )

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
        Base.metadata.drop_all(engine, tables=test_tables)
        engine.dispose()


# ---------------------------------------------------------------------
# Fonctions auxiliaires
# ---------------------------------------------------------------------

def register_user(
    client: TestClient,
    email: str,
) -> tuple[UUID, str]:

    response = client.post(
        "/api/v1/auth/register",
        data={
            "firstname": "Test",
            "lastname": "Mission",
            "email": email,
            "password": "a-very-strong-password",
            "tel": "0612345678",
        },
    )

    assert response.status_code == 201, response.text

    return (
        UUID(response.json()["id_user"]),
        response.json()["access_token"],
    )


def assign_role(
    test_session: sessionmaker[Session],
    user_id: UUID,
    role_name: str,
) -> None:

    with test_session() as session:
        role = session.query(Role).filter_by(
            role_name=role_name
        ).first()

        if role is None:
            role = Role(role_name=role_name)
            session.add(role)
            session.flush()

        session.add(
            RoleAssignment(
                id_user=user_id,
                id_role=role.id_role,
                assignment_type="assigned",
            )
        )
        session.commit()


def create_mission_payload() -> dict:
    start = datetime.now(timezone.utc) + timedelta(days=5)

    return {
        "title": f"Mission test {uuid4().hex[:6]}",
        "start_at": start.isoformat(),
        "finish_at": (start + timedelta(hours=4)).isoformat(),
        "seat_number": 5,
        "skills": ["Organisation", "Travail en équipe"],
    }


def create_admin(
    client: TestClient,
    test_session: sessionmaker[Session],
) -> dict:

    user_id, token = register_user(
        client,
        f"admin_{uuid4().hex[:8]}@example.com",
    )

    assign_role(test_session, user_id, "Administrator")

    return {
        "id": user_id,
        "headers": {"Authorization": f"Bearer {token}"},
    }


def create_volunteer(
    client: TestClient,
    test_session: sessionmaker[Session],
) -> dict:

    user_id, token = register_user(
        client,
        f"volunteer_{uuid4().hex[:8]}@example.com",
    )

    assign_role(test_session, user_id, "Volunteer")

    return {
        "id": user_id,
        "headers": {"Authorization": f"Bearer {token}"},
    }


def create_mission(
    client: TestClient,
    admin: dict,
    publish: bool = False,
) -> dict:
    """Crée une mission et la publie si nécessaire."""

    response = client.post(
        "/api/v1/missions",
        json=create_mission_payload(),
        headers=admin["headers"],
    )

    assert response.status_code == 201, response.text

    mission = response.json()

    if publish:
        publish_response = client.post(
            f"/api/v1/missions/{mission['id_mission']}/publish",
            headers=admin["headers"],
        )
        assert publish_response.status_code == 200, publish_response.text
        mission = publish_response.json()

    return mission


def register_volunteer_for_mission(
    client: TestClient,
    mission_id: str,
    volunteer: dict,
):
    return client.post(
        f"/api/v1/missions/{mission_id}/sign-ins",
        headers=volunteer["headers"],
    )


# ---------------------------------------------------------------------
# MIS-01 : Créer une mission
# ---------------------------------------------------------------------

def test_mis01_create_mission(mission_client):
    client, test_session = mission_client
    admin = create_admin(client, test_session)

    payload = create_mission_payload()

    response = client.post(
        "/api/v1/missions",
        json=payload,
        headers=admin["headers"],
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["title"] == payload["title"]
    assert data["status"] == "Draft"
    assert data["seat_number"] == 5
    assert data["skills"] == payload["skills"]


# ---------------------------------------------------------------------
# MIS-02 : Consulter la liste des missions
# ---------------------------------------------------------------------

def test_mis02_list_missions(mission_client):
    client, test_session = mission_client
    admin = create_admin(client, test_session)

    payload1 = create_mission_payload()
    payload2 = create_mission_payload()

    response1 = client.post(
        "/api/v1/missions",
        json=payload1,
        headers=admin["headers"],
    )
    response2 = client.post(
        "/api/v1/missions",
        json=payload2,
        headers=admin["headers"],
    )

    assert response1.status_code == 201, response1.text
    assert response2.status_code == 201, response2.text

    response = client.get(
        "/api/v1/missions",
        headers=admin["headers"],
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert isinstance(data, list)

    titles = [mission["title"] for mission in data]

    assert payload1["title"] in titles
    assert payload2["title"] in titles


# ---------------------------------------------------------------------
# MIS-03 : Consulter les détails d'une mission
# ---------------------------------------------------------------------

def test_mis03_get_mission_details(mission_client):
    client, test_session = mission_client
    admin = create_admin(client, test_session)

    mission = create_mission(client, admin)

    response = client.get(
        f"/api/v1/missions/{mission['id_mission']}",
        headers=admin["headers"],
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["id_mission"] == mission["id_mission"]
    assert data["title"] == mission["title"]
    assert data["remaining_seats"] == 5


# ---------------------------------------------------------------------
# MIS-04 : Modifier une mission
# ---------------------------------------------------------------------

def test_mis04_update_mission(mission_client):
    client, test_session = mission_client
    admin = create_admin(client, test_session)

    mission = create_mission(client, admin)

    payload = {
        "title": "Mission modifiée",
        "seat_number": 8,
        "skills": ["Logistique", "Communication"],
    }

    response = client.put(
        f"/api/v1/missions/{mission['id_mission']}",
        json=payload,
        headers=admin["headers"],
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["title"] == payload["title"]
    assert data["seat_number"] == 8
    assert data["skills"] == payload["skills"]


# ---------------------------------------------------------------------
# MIS-05 : Supprimer une mission en brouillon
# ---------------------------------------------------------------------

def test_mis05_delete_draft_mission(mission_client):
    client, test_session = mission_client
    admin = create_admin(client, test_session)

    mission = create_mission(client, admin)

    response = client.delete(
        f"/api/v1/missions/{mission['id_mission']}",
        headers=admin["headers"],
    )

    assert response.status_code == 204

    detail_response = client.get(
        f"/api/v1/missions/{mission['id_mission']}",
        headers=admin["headers"],
    )

    assert detail_response.status_code == 404


# ---------------------------------------------------------------------
# MIS-06 : Publier une mission
# ---------------------------------------------------------------------

def test_mis06_publish_mission(mission_client):
    client, test_session = mission_client
    admin = create_admin(client, test_session)

    mission = create_mission(client, admin)

    response = client.post(
        f"/api/v1/missions/{mission['id_mission']}/publish",
        headers=admin["headers"],
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "Published"


# ---------------------------------------------------------------------
# MIS-07 : Terminer une mission
# ---------------------------------------------------------------------

def test_mis07_complete_mission(mission_client):
    client, test_session = mission_client
    admin = create_admin(client, test_session)

    mission = create_mission(client, admin, publish=True)

    response = client.post(
        f"/api/v1/missions/{mission['id_mission']}/complete",
        headers=admin["headers"],
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "Completed"


# ---------------------------------------------------------------------
# MIS-08 : Annuler une mission
# ---------------------------------------------------------------------

def test_mis08_cancel_mission(mission_client):
    client, test_session = mission_client
    admin = create_admin(client, test_session)

    mission = create_mission(client, admin, publish=True)

    response = client.post(
        f"/api/v1/missions/{mission['id_mission']}/cancel",
        headers=admin["headers"],
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "Cancelled"


# ---------------------------------------------------------------------
# MIS-09 : Consulter le planning
# ---------------------------------------------------------------------

def test_mis09_get_planning(mission_client):
    client, test_session = mission_client
    admin = create_admin(client, test_session)

    mission = create_mission(client, admin, publish=True)

    date_from = datetime.now(timezone.utc).isoformat()
    date_to = (
        datetime.now(timezone.utc) + timedelta(days=10)
    ).isoformat()

    response = client.get(
        "/api/v1/planning",
        params={
            "from": date_from,
            "to": date_to,
        },
        headers=admin["headers"],
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert isinstance(data, list)

    mission_ids = [item["id_mission"] for item in data]

    assert mission["id_mission"] in mission_ids


# ---------------------------------------------------------------------
# MIS-10 : Consulter les inscriptions d'une mission
# ---------------------------------------------------------------------

def test_mis10_get_mission_sign_ins(mission_client):
    client, test_session = mission_client
    admin = create_admin(client, test_session)

    mission = create_mission(client, admin, publish=True)

    response = client.get(
        f"/api/v1/missions/{mission['id_mission']}/sign-ins",
        headers=admin["headers"],
    )

    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


# ---------------------------------------------------------------------
# MIS-11 : Valider ou refuser une inscription
# ---------------------------------------------------------------------

def test_mis11_validate_sign_in(mission_client):
    client, test_session = mission_client
    admin = create_admin(client, test_session)
    volunteer = create_volunteer(client, test_session)

    mission = create_mission(client, admin, publish=True)

    registration = register_volunteer_for_mission(
        client,
        mission["id_mission"],
        volunteer,
    )

    assert registration.status_code == 201, registration.text

    response = client.patch(
        f"/api/v1/missions/{mission['id_mission']}/sign-ins/"
        f"{volunteer['id']}/validation",
        json={"is_validated": False},
        headers=admin["headers"],
    )

    assert response.status_code == 200, response.text
    assert response.json()["is_validated"] is False

    # Réactiver la validation
    response = client.patch(
        f"/api/v1/missions/{mission['id_mission']}/sign-ins/"
        f"{volunteer['id']}/validation",
        json={"is_validated": True},
        headers=admin["headers"],
    )

    assert response.status_code == 200, response.text
    assert response.json()["is_validated"] is True


# ---------------------------------------------------------------------
# MIS-12 : S'inscrire à une mission
# ---------------------------------------------------------------------

def test_mis12_register_for_mission(mission_client):
    client, test_session = mission_client
    admin = create_admin(client, test_session)
    volunteer = create_volunteer(client, test_session)

    mission = create_mission(client, admin, publish=True)

    response = register_volunteer_for_mission(
        client,
        mission["id_mission"],
        volunteer,
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert "sign_in" in data
    assert data["sign_in"]["id_user"] == str(volunteer["id"])
    assert data["sign_in"]["id_mission"] == mission["id_mission"]
    assert data["sign_in"]["is_validated"] is True
    assert data["sign_in"]["is_canceled"] is False


# ---------------------------------------------------------------------
# MIS-13 : Annuler sa propre inscription
# ---------------------------------------------------------------------

def test_mis13_cancel_own_registration(mission_client):
    client, test_session = mission_client
    admin = create_admin(client, test_session)
    volunteer = create_volunteer(client, test_session)

    mission = create_mission(client, admin, publish=True)

    registration = register_volunteer_for_mission(
        client,
        mission["id_mission"],
        volunteer,
    )

    assert registration.status_code == 201, registration.text

    response = client.delete(
        f"/api/v1/missions/{mission['id_mission']}/sign-ins/me",
        headers=volunteer["headers"],
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["is_canceled"] is True
    assert data["is_validated"] is False
    assert data["canceled_at"] is not None
    assert data["validated_at"] is None


# ---------------------------------------------------------------------
# MIS-14 : Consulter ses propres inscriptions
# ---------------------------------------------------------------------

def test_mis14_get_my_sign_ins(mission_client):
    client, test_session = mission_client
    admin = create_admin(client, test_session)
    volunteer = create_volunteer(client, test_session)

    mission = create_mission(client, admin, publish=True)

    registration = register_volunteer_for_mission(
        client,
        mission["id_mission"],
        volunteer,
    )

    assert registration.status_code == 201, registration.text

    response = client.get(
        "/api/v1/volunteers/me/sign-ins",
        headers=volunteer["headers"],
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["sign_in"]["id_mission"] == mission["id_mission"]
    assert data[0]["mission"]["id_mission"] == mission["id_mission"]


# ---------------------------------------------------------------------
# MIS-15 : Consulter l'espace personnel du bénévole
# ---------------------------------------------------------------------

def test_mis15_get_volunteer_space(mission_client):
    client, test_session = mission_client
    admin = create_admin(client, test_session)
    volunteer = create_volunteer(client, test_session)

    mission = create_mission(client, admin, publish=True)

    registration = register_volunteer_for_mission(
        client,
        mission["id_mission"],
        volunteer,
    )

    assert registration.status_code == 201, registration.text

    response = client.get(
        "/api/v1/volunteers/me/space",
        headers=volunteer["headers"],
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert "upcoming_missions" in data
    assert "history" in data
    assert "notifications" in data

    assert isinstance(data["upcoming_missions"], list)
    assert isinstance(data["history"], list)
    assert isinstance(data["notifications"], list)

    assert len(data["upcoming_missions"]) >= 1
