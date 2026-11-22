from collections.abc import Iterator
from decimal import Decimal
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
from app.modules.auth.models import RevokedToken, Role, RoleAssignment, User
from app.modules.campaigns.models import Campaign, Event
from app.modules.financial_donations.models import FinancialDon


@pytest.fixture()
def campaigns_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        "test-jwt-secret-for-tests-at-least-32-bytes",
    )
    monkeypatch.setattr(settings, "access_token_expire_minutes", 30 * 24 * 60)

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    test_tables = [
        User.__table__,
        Role.__table__,
        RoleAssignment.__table__,
        RevokedToken.__table__,
        Campaign.__table__,
        FinancialDon.__table__,
        Event.__table__,
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
    return UUID(response.json()["id_user"]), response.json()["access_token"]


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


def _create_campaign_payload() -> dict:
    return {
        "title": f"Campagne Test {uuid4().hex[:6]}",
        "description": "Une campagne de test",
        "goal": 10000.00,
        "categories": ["Food_aid"],
    }


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

    response = client.post(
        "/api/v1/campaigns",
        json=_create_campaign_payload(),
        headers=headers,
    )
    assert response.status_code == 403


def test_publish_and_close_campaign(campaigns_client) -> None:
    client, test_session = campaigns_client
    admin_id, token = _register_test_user(client, "admin_camp2@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post(
        "/api/v1/campaigns",
        json=_create_campaign_payload(),
        headers=headers,
    )
    campaign_id = create_res.json()["id_campaign"]

    pub_res = client.post(
        f"/api/v1/campaigns/{campaign_id}/publish",
        headers=headers,
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "In_progress"

    close_res = client.post(
        f"/api/v1/campaigns/{campaign_id}/close",
        headers=headers,
    )
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "closed"


def test_list_public_campaigns(campaigns_client) -> None:
    client, test_session = campaigns_client
    admin_id, token = _register_test_user(client, "admin_camp3@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    c1 = client.post(
        "/api/v1/campaigns",
        json=_create_campaign_payload(),
        headers=headers,
    ).json()
    client.post(
        f"/api/v1/campaigns/{c1['id_campaign']}/publish",
        headers=headers,
    )

    client.post(
        "/api/v1/campaigns",
        json=_create_campaign_payload(),
        headers=headers,
    ).json()

    response = client.get("/api/v1/catalog/campaigns")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id_campaign"] == c1["id_campaign"]


def test_get_gauge(campaigns_client) -> None:
    client, test_session = campaigns_client
    admin_id, token = _register_test_user(client, "admin_camp4@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    c = client.post(
        "/api/v1/campaigns",
        json=_create_campaign_payload(),
        headers=headers,
    ).json()

    assert "id_campaign" in c, f"Erreur création campagne: {c}"

    response = client.get(f"/api/v1/campaigns/{c['id_campaign']}/gauge")

    assert response.status_code == 200
    assert response.json()["goal"] == "10000.00"
    assert response.json()["collected"] == "0.00"
    assert Decimal(response.json()["collected"]) == Decimal("0.00")
    assert response.json()["percentage"] == 0.0


@patch("app.modules.campaigns.service.convert_image_to_webp")
@patch("app.modules.campaigns.service.supabase_admin")
def test_cam12_upload_image_success(mock_supabase, mock_convert, campaigns_client) -> None:
    """Teste l'upload réussi d'une image pour une campagne."""
    client, test_session = campaigns_client
    admin_id, token = _register_test_user(client, "admin_img1@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    c = client.post(
        "/api/v1/campaigns",
        json=_create_campaign_payload(),
        headers=headers,
    ).json()
    c_id = c["id_campaign"]

    mock_convert.return_value = b"fake_webp_bytes"
    fake_url = "https://mock.supabase.co/storage/v1/object/public/campaigns/test/cover.webp"
    mock_supabase.storage.from_().get_public_url.return_value = fake_url

    response = client.post(
        f"/api/v1/campaigns/{c_id}/image",
        files={"image": ("test.png", b"fake_png_bytes", "image/png")},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["image_url"] == fake_url
    mock_convert.assert_called_once_with(b"fake_png_bytes")
    mock_supabase.storage.from_().upload.assert_called_once()


@patch("app.modules.campaigns.service.convert_image_to_webp")
@patch("app.modules.campaigns.service.supabase_admin")
def test_cam12_upload_image_already_exists(mock_supabase, mock_convert, campaigns_client) -> None:
    """Teste qu'on ne peut pas uploader une image si elle existe déjà (CAM-12)."""
    client, test_session = campaigns_client
    admin_id, token = _register_test_user(client, "admin_img2@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    c = client.post(
        "/api/v1/campaigns",
        json=_create_campaign_payload(),
        headers=headers,
    ).json()
    c_id = c["id_campaign"]

    with test_session() as session:
        campaign = session.get(Campaign, UUID(c_id))
        campaign.image_url = "https://existing.url/image.webp"
        session.commit()

    response = client.post(
        f"/api/v1/campaigns/{c_id}/image",
        files={"image": ("test.png", b"fake_png_bytes", "image/png")},
        headers=headers,
    )

    assert response.status_code == 409
    assert "existe déjà" in response.json()["detail"]


@patch("app.modules.campaigns.service.convert_image_to_webp")
@patch("app.modules.campaigns.service.supabase_admin")
def test_cam13_replace_image_success(mock_supabase, mock_convert, campaigns_client) -> None:
    """Teste le remplacement réussi d'une image existante (CAM-13)."""
    client, test_session = campaigns_client
    admin_id, token = _register_test_user(client, "admin_img3@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    c = client.post(
        "/api/v1/campaigns",
        json=_create_campaign_payload(),
        headers=headers,
    ).json()
    c_id = c["id_campaign"]

    with test_session() as session:
        campaign = session.get(Campaign, UUID(c_id))
        campaign.image_url = "https://existing.url/image.webp"
        session.commit()

    mock_convert.return_value = b"fake_webp_bytes"
    new_url = "https://mock.supabase.co/storage/v1/object/public/campaigns/test/new_cover.webp"
    mock_supabase.storage.from_().get_public_url.return_value = new_url

    response = client.patch(
        f"/api/v1/campaigns/{c_id}/image",
        files={"image": ("test.png", b"new_png_bytes", "image/png")},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["image_url"] == new_url


def test_upload_image_invalid_mime(campaigns_client) -> None:
    """Teste le rejet d'un fichier qui n'est pas une image."""
    client, test_session = campaigns_client
    admin_id, token = _register_test_user(client, "admin_img4@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    c = client.post(
        "/api/v1/campaigns",
        json=_create_campaign_payload(),
        headers=headers,
    ).json()
    c_id = c["id_campaign"]

    response = client.post(
        f"/api/v1/campaigns/{c_id}/image",
        files={"image": ("test.txt", b"not_an_image", "text/plain")},
        headers=headers,
    )

    assert response.status_code == 400
    assert "n'est pas une image" in response.json()["detail"]


def test_image_url_is_persisted_in_db(campaigns_client) -> None:
    """
    Vérifie que l'URL de l'image est bien enregistrée dans la table
    'campaigns' après un appel réussi à la route CAM-12.
    """
    client, test_session = campaigns_client
    admin_id, token = _register_test_user(client, "admin_img_db@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    c = client.post(
        "/api/v1/campaigns",
        json=_create_campaign_payload(),
        headers=headers,
    ).json()
    campaign_id = UUID(c["id_campaign"])

    with test_session() as session:
        campaign_in_db = session.get(Campaign, campaign_id)
        assert campaign_in_db.image_url is None

    fake_url = "https://mock.supabase.co/storage/v1/object/public/campaigns/test/cover.webp"

    with (
        patch("app.modules.campaigns.service.convert_image_to_webp") as mock_convert,
        patch("app.modules.campaigns.service.supabase_admin") as mock_supabase,
    ):
        mock_convert.return_value = b"fake_webp"
        mock_supabase.storage.from_().get_public_url.return_value = fake_url

        response = client.post(
            f"/api/v1/campaigns/{campaign_id}/image",
            files={"image": ("test.png", b"fake_png_bytes", "image/png")},
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["image_url"] == fake_url

    with test_session() as session:
        campaign_in_db = session.get(Campaign, campaign_id)
        assert campaign_in_db.image_url is not None, "L'image_url n'a pas été sauvegardée en base !"
        assert campaign_in_db.image_url == fake_url, (
            "L'URL en base ne correspond pas à celle retournée par Supabase"
        )


def _create_test_event(client: TestClient, headers: dict, campaign_id: str) -> dict:
    payload = {
        "title": "Iftar Solidaire",
        "event_at": "2099-03-20T17:30:00Z",
        "place": "Mosquée El Feth, Alger",
        "goal": 20000.00,
    }

    response = client.post(
        f"/api/v1/campaigns/{campaign_id}/events",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 201, response.text
    return response.json()


def test_event_crud_success(campaigns_client) -> None:
    client, test_session = campaigns_client

    admin_id, token = _register_test_user(client, "admin_events@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    campaign_response = client.post(
        "/api/v1/campaigns",
        json=_create_campaign_payload(),
        headers=headers,
    )
    assert campaign_response.status_code == 201
    campaign_id = campaign_response.json()["id_campaign"]

    event = _create_test_event(client, headers, campaign_id)
    event_id = event["id_event"]

    assert event["title"] == "Iftar Solidaire"
    assert event["id_campaign"] == campaign_id

    response = client.get("/api/v1/events", headers=headers)
    assert response.status_code == 200
    assert any(e["id_event"] == event_id for e in response.json())

    response = client.get(f"/api/v1/events/{event_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Iftar Solidaire"

    response = client.patch(
        f"/api/v1/events/{event_id}",
        json={"title": "Iftar Solidaire 2026"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Iftar Solidaire 2026"

    response = client.delete(
        f"/api/v1/events/{event_id}",
        headers=headers,
    )
    assert response.status_code in (200, 204)

    response = client.get(f"/api/v1/events/{event_id}", headers=headers)
    assert response.status_code == 404


def test_event_creation_unauthorized(campaigns_client) -> None:
    client, test_session = campaigns_client

    admin_id, admin_token = _register_test_user(client, "admin_events_auth@example.com")
    _assign_administrator_role(test_session, admin_id)

    campaign_response = client.post(
        "/api/v1/campaigns",
        json=_create_campaign_payload(),
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    campaign_id = campaign_response.json()["id_campaign"]

    _, user_token = _register_test_user(client, "user_events_auth@example.com")

    response = client.post(
        f"/api/v1/campaigns/{campaign_id}/events",
        json={
            "title": "Événement non autorisé",
            "event_at": "2099-03-20T17:30:00Z",
            "place": "Alger",
            "goal": 1000.00,
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 403


def test_event_creation_without_authentication(campaigns_client) -> None:
    client, test_session = campaigns_client

    admin_id, token = _register_test_user(client, "admin_events_noauth@example.com")
    _assign_administrator_role(test_session, admin_id)

    campaign_response = client.post(
        "/api/v1/campaigns",
        json=_create_campaign_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = campaign_response.json()["id_campaign"]

    response = client.post(
        f"/api/v1/campaigns/{campaign_id}/events",
        json={
            "title": "Événement sans authentification",
            "event_at": "2099-03-20T17:30:00Z",
            "place": "Alger",
            "goal": 1000.00,
        },
    )

    assert response.status_code == 401


def test_public_event_catalog(campaigns_client) -> None:
    client, test_session = campaigns_client

    admin_id, token = _register_test_user(client, "admin_events_catalog@example.com")
    _assign_administrator_role(test_session, admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    campaign_response = client.post(
        "/api/v1/campaigns",
        json=_create_campaign_payload(),
        headers=headers,
    )
    campaign_id = campaign_response.json()["id_campaign"]

    event = _create_test_event(client, headers, campaign_id)
    event_id = event["id_event"]

    response = client.get("/api/v1/catalogue/events")

    assert response.status_code == 200
    assert any(e["id_event"] == event_id for e in response.json())

    response = client.get(f"/api/v1/catalogue/events/{event_id}")

    assert response.status_code == 200
    assert response.json()["id_event"] == event_id
