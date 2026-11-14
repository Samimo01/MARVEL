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
from app.modules.natural_donations.models import NaturalDon, NaturalDonItem, ObjectType


@pytest.fixture()
def natural_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(settings, "jwt_secret_key", "test-jwt-secret-for-tests-at-least-32-bytes")
    monkeypatch.setattr(settings, "access_token_expire_minutes", 30 * 24 * 60)
    
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # On inclut toutes les tables nécessaires
    test_tables = [
        User.__table__, Role.__table__, RoleAssignment.__table__, 
        Campaign.__table__, ObjectType.__table__, 
        NaturalDon.__table__, NaturalDonItem.__table__
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


# ============================================================
# Helpers
# ============================================================
def _register_test_user(client: TestClient, email: str) -> tuple[UUID, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "firstname": "User", "lastname": "Test",
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

def _create_test_campaign(client: TestClient, headers: dict) -> str:
    payload = {
        "title": f"Campagne Nature {uuid4().hex[:6]}",
        "goal": 10000.00,
        "categories": ["Food_aid"]
    }
    res = client.post("/api/v1/campaigns", json=payload, headers=headers)
    assert res.status_code == 201
    return res.json()["id_campaign"]

def _create_test_object_type(client: TestClient, headers: dict, name: str = "Vêtements") -> str:
    res = client.post("/api/v1/admin/object-types", json={"name": name}, headers=headers)
    assert res.status_code == 201
    return res.json()["id_object"]


# ============================================================
# TESTS DES TYPES D'OBJETS (NAT-01, NAT-15 à NAT-18)
# ============================================================
def test_nat01_list_active_object_types(natural_client) -> None:
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "admin_obj@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    # Créer 2 actifs, 1 inactif
    obj1 = _create_test_object_type(client, headers, "Riz")
    obj2 = _create_test_object_type(client, headers, "Huile")
    obj3 = _create_test_object_type(client, headers, "Périmé")
    client.patch(f"/api/v1/admin/object-types/{obj3}/activation?is_active=false", headers=headers)

    # Route publique (Authentifié)
    res = client.get("/api/v1/object-types", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 2
    names = [o["name"] for o in res.json()]
    assert "Riz" in names
    assert "Huile" in names
    assert "Périmé" not in names

def test_nat15_to_18_object_type_crud(natural_client) -> None:
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "admin_crud@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    # NAT-16 : Création
    obj_id = _create_test_object_type(client, headers, "Meubles")

    # NAT-17 : Modification
    res_upd = client.put(f"/api/v1/admin/object-types/{obj_id}", json={"description": "Meubles en bois"}, headers=headers)
    assert res_upd.status_code == 200
    assert res_upd.json()["description"] == "Meubles en bois"

    # NAT-18 : Désactivation
    res_off = client.patch(f"/api/v1/admin/object-types/{obj_id}/activation?is_active=false", headers=headers)
    assert res_off.status_code == 200
    assert res_off.json()["is_active"] is False

    # NAT-15 : Liste complète (Admin)
    res_all = client.get("/api/v1/admin/object-types", headers=headers)
    assert res_all.status_code == 200
    assert len(res_all.json()) == 1


# ============================================================
# TESTS DE GESTION DES DONS (NAT-02 à NAT-11)
# ============================================================
def test_nat02_create_natural_don(natural_client) -> None:
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "admin_nat@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}
    
    obj_id = _create_test_object_type(client, headers, "Riz")
    campaign_id = _create_test_campaign(client, headers)

    payload = {
        "recovery_mode": "Deposit",
        "id_campaign": campaign_id,
        "items": [
            {"id_object": obj_id, "declared_quantity": 10, "declared_state": "New"},
            {"id_object": obj_id, "declared_quantity": 5, "declared_state": "Good"}
        ]
    }
    res = client.post("/api/v1/donations/natural", json=payload, headers=headers)
    
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "Declare"
    assert len(data["items"]) == 2
    assert data["items"][0]["declared_quantity"] == "10.00"

def test_nat04_cancel_natural_don(natural_client) -> None:
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "admin_cancel@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}
    
    obj_id = _create_test_object_type(client, headers, "Riz")
    payload = {
        "recovery_mode": "Deposit",
        "items": [{"id_object": obj_id, "declared_quantity": 1, "declared_state": "New"}]
    }
    res_create = client.post("/api/v1/donations/natural", json=payload, headers=headers)
    don_id = res_create.json()["id_don_n"]

    res_del = client.delete(f"/api/v1/donations/natural/{don_id}", headers=headers)
    assert res_del.status_code == 204

def test_nat05_and_nat06_list_and_detail(natural_client) -> None:
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "admin_list@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}
    
    obj_id = _create_test_object_type(client, headers, "Riz")
    
    # Créer 2 dons
    for _ in range(2):
        payload = {
            "recovery_mode": "Deposit",
            "items": [{"id_object": obj_id, "declared_quantity": 1, "declared_state": "New"}]
        }
        client.post("/api/v1/donations/natural", json=payload, headers=headers)

    # NAT-05 : Liste
    res_list = client.get("/api/v1/donations/natural?status=Declare", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 2

    # NAT-06 : Détail
    don_id = res_list.json()[0]["id_don_n"]
    res_detail = client.get(f"/api/v1/donations/natural/{don_id}", headers=headers)
    assert res_detail.status_code == 200
    assert len(res_detail.json()["items"]) == 1


def test_nat07_and_nat08_validate_and_reject(natural_client) -> None:
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "admin_val@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}
    
    obj_id = _create_test_object_type(client, headers, "Riz")
    payload = {
        "recovery_mode": "Deposit",
        "items": [{"id_object": obj_id, "declared_quantity": 1, "declared_state": "New"}]
    }
    
    # Don 1 : Valider
    don1 = client.post("/api/v1/donations/natural", json=payload, headers=headers).json()
    res_val = client.post(f"/api/v1/donations/natural/{don1['id_don_n']}/validate", headers=headers)
    assert res_val.status_code == 200
    assert res_val.json()["status"] == "valid"
    assert res_val.json()["validated_by"] == str(admin_id)

    # Don 2 : Refuser
    don2 = client.post("/api/v1/donations/natural", json=payload, headers=headers).json()
    res_rej = client.post(f"/api/v1/donations/natural/{don2['id_don_n']}/reject", json={"refusal_reason": "Objets cassés"}, headers=headers)
    assert res_rej.status_code == 200
    assert res_rej.json()["status"] == "Refuse"
    assert res_rej.json()["refusal_reason"] == "Objets cassés"


def test_nat09_plan_collect(natural_client) -> None:
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "admin_plan@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}
    
    obj_id = _create_test_object_type(client, headers, "Riz")
    payload = {
        "recovery_mode": "Collect", # Mode collecte
        "items": [{"id_object": obj_id, "declared_quantity": 1, "declared_state": "New"}]
    }
    
    # Créer et valider
    don = client.post("/api/v1/donations/natural", json=payload, headers=headers).json()
    client.post(f"/api/v1/donations/natural/{don['id_don_n']}/validate", headers=headers)

    # Planifier collecte
    plan_payload = {"planned_at": "2024-12-01T10:00:00Z", "collection_address": "Cité 12, Alger"}
    res_plan = client.post(f"/api/v1/donations/natural/{don['id_don_n']}/collects", json=plan_payload, headers=headers)
    
    assert res_plan.status_code == 200
    assert res_plan.json()["status"] == "Collection_Planned"
    assert res_plan.json()["collection_address"] == "Cité 12, Alger"


def test_nat10_and_nat11_reception_and_stock_in(natural_client) -> None:
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "admin_stock@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}
    
    obj_id = _create_test_object_type(client, headers, "Riz")
    payload = {
        "recovery_mode": "Deposit",
        "items": [{"id_object": obj_id, "declared_quantity": 10, "declared_state": "New"}]
    }
    
    # Créer et valider
    don = client.post("/api/v1/donations/natural", json=payload, headers=headers).json()
    don_id = don["id_don_n"]
    item_id = don["items"][0]["id_nat"]
    client.post(f"/api/v1/donations/natural/{don_id}/validate", headers=headers)

    # NAT-10 : Réception
    reception_payload = {
        "received_quantity": 8, 
        "received_state": "Good", 
        "is_compliant": False,
        "non_compliant_reason": "2 sacs manquants"
    }
    res_rec = client.put(f"/api/v1/donations/natural/{don_id}/items/{item_id}/reception", json=reception_payload, headers=headers)
    assert res_rec.status_code == 200
    assert res_rec.json()["received_quantity"] == "8.00"
    assert res_rec.json()["is_compliant"] is False

    # NAT-11 : Stock-in
    res_stock = client.post(f"/api/v1/donations/natural/{don_id}/stock-in", headers=headers)
    assert res_stock.status_code == 200
    assert res_stock.json()["status"] == "In_Stock"
    assert res_stock.json()["id_stock"] is not None # Simulation de l'ID stock
    assert res_stock.json()["received_by"] == str(admin_id)


def test_nat03_upload_image(natural_client) -> None:
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "admin_img@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}
    
    obj_id = _create_test_object_type(client, headers, "Riz")
    payload = {
        "recovery_mode": "Deposit",
        "items": [{"id_object": obj_id, "declared_quantity": 1, "declared_state": "New"}]
    }
    don = client.post("/api/v1/donations/natural", json=payload, headers=headers).json()
    don_id = don["id_don_n"]
    item_id = don["items"][0]["id_nat"]

    # NAT-03 : Upload d'image (Simulé via query param pour l'exemple)
    fake_url = "https://storage.com/image.jpg"
    res = client.post(f"/api/v1/donations/natural/{don_id}/items/{item_id}/image?image_url={fake_url}", headers=headers)
    
    assert res.status_code == 200
    assert res.json()["image_url"] == fake_url