"""Tests du module natural_donations."""

from collections.abc import Iterator
from unittest.mock import patch
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
from app.modules.natural_donations.models import (
    NaturalDon, NaturalDonItem, ObjectType,
)


# ============================================================
# FIXTURE
# ============================================================
@pytest.fixture()
def natural_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(
        settings, "jwt_secret_key",
        "test-jwt-secret-for-tests-at-least-32-bytes",
    )
    monkeypatch.setattr(settings, "access_token_expire_minutes", 30 * 24 * 60)

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    test_tables = [
        User.__table__, Role.__table__, RoleAssignment.__table__,
        Campaign.__table__, ObjectType.__table__,
        NaturalDon.__table__, NaturalDonItem.__table__,
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
# HELPERS
# ============================================================
def _register_test_user(client: TestClient, email: str) -> tuple[UUID, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "firstname": "User", "lastname": "Test",
            "email": email, "password": "a-very-strong-password",
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
        session.add(RoleAssignment(
            id_user=user.id_user, id_role=role.id_role,
            assignment_type="assigned",
        ))
        session.commit()


def _create_test_campaign(client: TestClient, headers: dict) -> str:
    payload = {
        "title": f"Campagne Nature {uuid4().hex[:6]}",
        "goal": 10000.00,
        "categories": ["Food_aid"],
    }
    res = client.post("/api/v1/campaigns", json=payload, headers=headers)
    assert res.status_code == 201
    return res.json()["id_campaign"]


def _create_test_object_type(
    client: TestClient, headers: dict, name: str = "Vêtements",
) -> str:
    res = client.post(
        "/api/v1/admin/object-types",
        json={"name": name},
        headers=headers,
    )
    assert res.status_code == 201
    return res.json()["id_object"]


def _create_natural_don_with_item(
    client: TestClient, test_session, admin_headers: dict,
) -> tuple[str, str]:
    """Crée un don naturel + 1 item, retourne (id_don_n, id_nat)."""
    obj_id = _create_test_object_type(client, admin_headers, f"Objet {uuid4().hex[:4]}")
    payload = {
        "recovery_mode": "Deposit",
        "items": [{
            "id_object": obj_id,
            "declared_quantity": 5,
            "declared_state": "New",
        }],
    }
    res = client.post(
        "/api/v1/donations/natural", json=payload, headers=admin_headers,
    )
    assert res.status_code == 201
    data = res.json()
    return data["id_don_n"], data["items"][0]["id_nat"]


# ============================================================
# TESTS OBJECT TYPES (NAT-01, NAT-15 à NAT-18)
# ============================================================
def test_nat01_list_active_object_types(natural_client) -> None:
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "admin_obj@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    obj1 = _create_test_object_type(client, headers, "Riz")
    obj2 = _create_test_object_type(client, headers, "Huile")
    obj3 = _create_test_object_type(client, headers, "Périmé")
    client.patch(
        f"/api/v1/admin/object-types/{obj3}/activation?is_active=false",
        headers=headers,
    )

    res = client.get("/api/v1/object-types", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 2
    names = [o["name"] for o in res.json()]
    assert "Riz" in names and "Huile" in names
    assert "Périmé" not in names


def test_nat15_to_18_object_type_crud(natural_client) -> None:
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "admin_crud@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    obj_id = _create_test_object_type(client, headers, "Meubles")

    res_upd = client.put(
        f"/api/v1/admin/object-types/{obj_id}",
        json={"description": "Meubles en bois"},
        headers=headers,
    )
    assert res_upd.status_code == 200
    assert res_upd.json()["description"] == "Meubles en bois"

    res_off = client.patch(
        f"/api/v1/admin/object-types/{obj_id}/activation?is_active=false",
        headers=headers,
    )
    assert res_off.status_code == 200
    assert res_off.json()["is_active"] is False

    res_all = client.get("/api/v1/admin/object-types", headers=headers)
    assert res_all.status_code == 200
    assert len(res_all.json()) == 1


# ============================================================
# TESTS DONS NATURELS (NAT-02 à NAT-11)
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
            {"id_object": obj_id, "declared_quantity": 5, "declared_state": "Good"},
        ],
    }
    res = client.post("/api/v1/donations/natural", json=payload, headers=headers)

    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "Declare"
    assert len(data["items"]) == 2

    quantities = sorted(float(item["declared_quantity"]) for item in data["items"])
    assert quantities == [5.0, 10.0]
    
    # On vérifie aussi que les 2 états sont présents
    states = {item["declared_state"] for item in data["items"]}
    assert states == {"New", "Good"}

def test_nat04_cancel_natural_don(natural_client) -> None:
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "admin_cancel@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    id_don_n, _ = _create_natural_don_with_item(client, test_session, headers)
    res_del = client.delete(f"/api/v1/donations/natural/{id_don_n}", headers=headers)
    assert res_del.status_code == 204


def test_nat05_and_nat06_list_and_detail(natural_client) -> None:
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "admin_list@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    _create_natural_don_with_item(client, test_session, headers)
    _create_natural_don_with_item(client, test_session, headers)

    res_list = client.get(
        "/api/v1/donations/natural?status=Declare", headers=headers,
    )
    assert res_list.status_code == 200
    assert len(res_list.json()) == 2

    don_id = res_list.json()[0]["id_don_n"]
    res_detail = client.get(
        f"/api/v1/donations/natural/{don_id}", headers=headers,
    )
    assert res_detail.status_code == 200
    assert len(res_detail.json()["items"]) == 1


def test_nat07_and_nat08_validate_and_reject(natural_client) -> None:
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "admin_val@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    don1_id, _ = _create_natural_don_with_item(client, test_session, headers)
    res_val = client.post(
        f"/api/v1/donations/natural/{don1_id}/validate", headers=headers,
    )
    assert res_val.status_code == 200
    assert res_val.json()["status"] == "valid"

    don2_id, _ = _create_natural_don_with_item(client, test_session, headers)
    res_rej = client.post(
        f"/api/v1/donations/natural/{don2_id}/reject",
        json={"refusal_reason": "Objets cassés"},
        headers=headers,
    )
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
        "recovery_mode": "Collect",
        "items": [{"id_object": obj_id, "declared_quantity": 1, "declared_state": "New"}],
    }
    don = client.post(
        "/api/v1/donations/natural", json=payload, headers=headers,
    ).json()
    client.post(
        f"/api/v1/donations/natural/{don['id_don_n']}/validate", headers=headers,
    )

    plan_payload = {
        "planned_at": "2024-12-01T10:00:00Z",
        "collection_address": "Cité 12, Alger",
    }
    res_plan = client.post(
        f"/api/v1/donations/natural/{don['id_don_n']}/collects",
        json=plan_payload, headers=headers,
    )
    assert res_plan.status_code == 200
    assert res_plan.json()["status"] == "Collection_Planned"


def test_nat10_and_nat11_reception_and_stock_in(natural_client) -> None:
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "admin_stock@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    id_don_n, id_nat = _create_natural_don_with_item(client, test_session, headers)
    client.post(
        f"/api/v1/donations/natural/{id_don_n}/validate", headers=headers,
    )

    reception_payload = {
        "received_quantity": 4,
        "received_state": "Good",
        "is_compliant": False,
        "non_compliant_reason": "1 manquant",
    }
    res_rec = client.put(
        f"/api/v1/donations/natural/{id_don_n}/items/{id_nat}/reception",
        json=reception_payload, headers=headers,
    )
    assert res_rec.status_code == 200
    assert res_rec.json()["received_quantity"] == "4.00"

    res_stock = client.post(
        f"/api/v1/donations/natural/{id_don_n}/stock-in", headers=headers,
    )
    assert res_stock.status_code == 200
    assert res_stock.json()["status"] == "In_Stock"
    assert res_stock.json()["id_stock"] is not None


# ============================================================
# TESTS IMAGES (NAT-03 et NAT-19)
# ============================================================

@patch("app.modules.natural_donations.service.convert_image_to_webp")
@patch("app.modules.natural_donations.service.supabase_admin")
def test_nat03_upload_item_image_success(
    mock_supabase, mock_convert, natural_client,
) -> None:
    """NAT-03 : Upload réussi d'une image d'article."""
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "nat_img1@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    id_don_n, id_nat = _create_natural_don_with_item(client, test_session, headers)

    mock_convert.return_value = b"fake_webp"
    fake_url = "https://mock.supabase.co/storage/v1/object/public/natural_donations/cover.webp"
    mock_supabase.storage.from_().get_public_url.return_value = fake_url

    response = client.post(
        f"/api/v1/donations/natural/{id_don_n}/items/{id_nat}/image",
        files={"image": ("test.png", b"fake_png", "image/png")},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["image_url"] == fake_url
    mock_convert.assert_called_once()
    mock_supabase.storage.from_().upload.assert_called_once()

    # Persistance en DB
    with test_session() as session:
        item = session.get(NaturalDonItem, (UUID(id_don_n), UUID(id_nat)))
        assert item.image_url == fake_url


@patch("app.modules.natural_donations.service.convert_image_to_webp")
@patch("app.modules.natural_donations.service.supabase_admin")
def test_nat03_upload_fails_if_image_exists(
    mock_supabase, mock_convert, natural_client,
) -> None:
    """NAT-03 : Échoue avec 409 si une image existe déjà."""
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "nat_img2@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    id_don_n, id_nat = _create_natural_don_with_item(client, test_session, headers)

    with test_session() as session:
        item = session.get(NaturalDonItem, (UUID(id_don_n), UUID(id_nat)))
        item.image_url = "https://existing.url/image.webp"
        session.commit()

    response = client.post(
        f"/api/v1/donations/natural/{id_don_n}/items/{id_nat}/image",
        files={"image": ("test.png", b"fake_png", "image/png")},
        headers=headers,
    )

    assert response.status_code == 409
    assert "existe déjà" in response.json()["detail"]


def test_nat03_rejects_non_image(natural_client) -> None:
    """NAT-03 : Rejette un fichier non-image."""
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "nat_img3@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    id_don_n, id_nat = _create_natural_don_with_item(client, test_session, headers)

    response = client.post(
        f"/api/v1/donations/natural/{id_don_n}/items/{id_nat}/image",
        files={"image": ("test.txt", b"not_an_image", "text/plain")},
        headers=headers,
    )

    assert response.status_code == 400
    assert "n'est pas une image" in response.json()["detail"]


def test_nat03_rejects_non_owner(natural_client) -> None:
    """NAT-03 : Seul le propriétaire du don peut uploader une image."""
    client, test_session = natural_client

    # Admin crée le don
    admin_id, admin_token = _register_test_user(client, "nat_admin@example.com")
    _assign_administrator_role(test_session, admin_id)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    id_don_n, id_nat = _create_natural_don_with_item(client, test_session, admin_headers)

    # Un autre utilisateur tente d'uploader
    _, other_token = _register_test_user(client, "nat_other@example.com")
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = client.post(
        f"/api/v1/donations/natural/{id_don_n}/items/{id_nat}/image",
        files={"image": ("test.png", b"fake", "image/png")},
        headers=other_headers,
    )

    assert response.status_code == 409
    assert "propriétaire" in response.json()["detail"]


# ============================================================
# NAT-19 : Remplacement de l'image
# ============================================================

@patch("app.modules.natural_donations.service.convert_image_to_webp")
@patch("app.modules.natural_donations.service.supabase_admin")
def test_nat19_replace_item_image(
    mock_supabase, mock_convert, natural_client,
) -> None:
    """NAT-19 : Remplace l'image d'un article."""
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "nat_img4@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    id_don_n, id_nat = _create_natural_don_with_item(client, test_session, headers)

    # Pré-remplir une image existante
    from app.modules.natural_donations.models import NaturalDonItem
    with test_session() as session:
        item = session.get(NaturalDonItem, (UUID(id_don_n), UUID(id_nat)))
        item.image_url = "https://old.url/cover.webp"
        session.commit()

    mock_convert.return_value = b"fake_webp"
    new_url = "https://mock.supabase.co/storage/v1/object/public/natural_donations/new.webp"
    mock_supabase.storage.from_().get_public_url.return_value = new_url

    # 👇 Nouvelle URL avec id_don_n ET id_nat
    response = client.patch(
        f"/api/v1/donations/natural/{id_don_n}/items/{id_nat}/image",
        files={"image": ("test.png", b"new_png_bytes", "image/png")},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["image_url"] == new_url

    # Vérification en DB
    with test_session() as session:
        item = session.get(NaturalDonItem, (UUID(id_don_n), UUID(id_nat)))
        assert item.image_url == new_url


def test_nat19_fails_if_item_not_found(natural_client) -> None:
    """NAT-19 : 404 si l'item n'existe pas."""
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "nat_img5@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    # Créer un don valide mais avec un id_nat bidon
    id_don_n, _ = _create_natural_don_with_item(client, test_session, headers)
    fake_item_id = uuid4()

    response = client.patch(
        f"/api/v1/donations/natural/{id_don_n}/items/{fake_item_id}/image",
        files={"image": ("test.png", b"fake", "image/png")},
        headers=headers,
    )

    assert response.status_code == 404


def test_nat19_fails_if_donation_not_found(natural_client) -> None:
    """NAT-19 : 404 si le don n'existe pas."""
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "nat_img6@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    fake_don_id = uuid4()
    fake_item_id = uuid4()

    response = client.patch(
        f"/api/v1/donations/natural/{fake_don_id}/items/{fake_item_id}/image",
        files={"image": ("test.png", b"fake", "image/png")},
        headers=headers,
    )

    assert response.status_code == 404


def test_nat19_rejects_non_image(natural_client) -> None:
    """NAT-19 : Rejette un fichier non-image."""
    client, test_session = natural_client
    admin_id, token = _register_test_user(client, "nat_img7@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    id_don_n, id_nat = _create_natural_don_with_item(client, test_session, headers)

    response = client.patch(
        f"/api/v1/donations/natural/{id_don_n}/items/{id_nat}/image",
        files={"image": ("test.txt", b"not_an_image", "text/plain")},
        headers=headers,
    )

    assert response.status_code == 400
    assert "n'est pas une image" in response.json()["detail"]