from collections.abc import Iterator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.modules.auth.models import Role, RoleAssignment, User
from app.modules.campaigns.models import Campaign
from app.modules.financial_donations.models import FinancialDon 
from decimal import Decimal


@pytest.fixture()
def campaigns_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(settings, "jwt_secret_key", "test-jwt-secret-for-tests-at-least-32-bytes")
    monkeypatch.setattr(settings, "access_token_expire_minutes", 30 * 24 * 60)
    
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # 👇 AJOUT DE FinancialDon.__table__ DANS LA LISTE
    test_tables = [
        User.__table__, Role.__table__, RoleAssignment.__table__, 
        Campaign.__table__, FinancialDon.__table__
    ]
    Base.metadata.create_all(engine, tables=test_tables)
    
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
        Base.metadata.drop_all(engine, tables=test_tables)
        engine.dispose()


# Helpers
def _register_test_user(client: TestClient, email: str) -> tuple[UUID, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "firstname": "Ada", "lastname": "Lovelace",
            "email": email, "password": "a-very-strong-password", "tel": "0612345678",
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
        session.add(RoleAssignment(id_user=user.id_user, id_role=role.id_role, assignment_type="assigned"))
        session.commit()

def _create_campaign_payload() -> dict:
    return {
        "title": f"Campagne Test {uuid4().hex[:6]}",
        "description": "Une campagne de test",
        "goal": 10000.00,
        "categories": ["Food_aid"]
    }


# Tests
def test_create_campaign_success(campaigns_client) -> None:
    client, test_session = campaigns_client
    admin_id, token = _register_test_user(client, "admin_camp@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    payload = _create_campaign_payload()
    response = client.post("/api/v1/campaigns", json=payload, headers=headers)

    assert response.status_code == 201
    assert response.json()["title"] == payload["title"]
    assert response.json()["status"] == "Draft"
    assert response.json()["id_user"] == str(admin_id)

def test_create_campaign_unauthorized(campaigns_client) -> None:
    client, _ = campaigns_client
    _, token = _register_test_user(client, "user_camp@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/v1/campaigns", json=_create_campaign_payload(), headers=headers)
    assert response.status_code == 403

def test_publish_and_close_campaign(campaigns_client) -> None:
    client, test_session = campaigns_client
    admin_id, token = _register_test_user(client, "admin_camp2@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post("/api/v1/campaigns", json=_create_campaign_payload(), headers=headers)
    campaign_id = create_res.json()["id_campaign"]

    pub_res = client.post(f"/api/v1/campaigns/{campaign_id}/publish", headers=headers)
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "In_progress"

    close_res = client.post(f"/api/v1/campaigns/{campaign_id}/close", headers=headers)
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "closed"

def test_list_public_campaigns(campaigns_client) -> None:
    client, test_session = campaigns_client
    admin_id, token = _register_test_user(client, "admin_camp3@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    c1 = client.post("/api/v1/campaigns", json=_create_campaign_payload(), headers=headers).json()
    client.post(f"/api/v1/campaigns/{c1['id_campaign']}/publish", headers=headers)

    c2 = client.post("/api/v1/campaigns", json=_create_campaign_payload(), headers=headers).json()

    response = client.get("/api/v1/catalog/campaigns")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id_campaign"] == c1["id_campaign"]

def test_get_gauge(campaigns_client) -> None:
    client, test_session = campaigns_client
    admin_id, token = _register_test_user(client, "admin_camp4@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    c = client.post("/api/v1/campaigns", json=_create_campaign_payload(), headers=headers).json()
    
    # Vérifier que la campagne a bien un ID
    assert "id_campaign" in c, f"Erreur création campagne: {c}"

    response = client.get(f"/api/v1/campaigns/{c['id_campaign']}/gauge")

    assert response.status_code == 200
    assert response.json()["goal"] == "10000.00"
    assert response.json()["collected"] == "0.00"
    assert Decimal(response.json()["collected"]) == Decimal("0.00") 
    assert response.json()["percentage"] == 0.0