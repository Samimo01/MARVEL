from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.modules.auth.cookies import ACCESS_TOKEN_COOKIE
from app.modules.auth.models import RefreshToken, RevokedToken, Role, RoleAssignment, User
from app.modules.campaigns.models import Campaign
from app.modules.financial_donations.models import FinancialDon


@pytest.fixture()
def donations_client(
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
        RefreshToken.__table__,
        Campaign.__table__,
        FinancialDon.__table__,
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
        data={
            "firstname": "Donor",
            "lastname": "Test",
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


def _create_test_campaign(client: TestClient, headers: dict) -> str:
    """Helper pour créer une campagne et renvoyer son ID."""
    payload = {
        "title": f"Campagne Don {uuid4().hex[:6]}",
        "goal": 50000.00,
        "categories": ["Health"],
    }
    res = client.post("/api/v1/campaigns", json=payload, headers=headers)
    assert res.status_code == 201
    return res.json()["id_campaign"]


# ============================================================
# TESTS EXISTANTS (DON-01, 02, 03, 05, 06, 08)
# ============================================================


def test_create_financial_donation_success(donations_client) -> None:
    client, test_session = donations_client
    admin_id, admin_token = _register_test_user(client, "admin_don@example.com")
    _assign_administrator_role(test_session, admin_id)

    user_id, user_token = _register_test_user(client, "donor@example.com")
    campaign_id = _create_test_campaign(client, {"Authorization": f"Bearer {admin_token}"})

    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "amount": 500.00,
        "id_campaign": campaign_id,
        "is_anonymous": False,
    }
    response = client.post("/api/v1/dons/financiers", json=payload, headers=headers)

    assert response.status_code == 201
    assert response.json()["amount"] == "500.00"
    assert response.json()["status"] == "Pending"
    assert response.json()["paid_at"] is None
    assert response.json()["id_user"] == str(user_id)


def test_pay_and_check_status(donations_client) -> None:
    client, test_session = donations_client
    admin_id, admin_token = _register_test_user(client, "admin_don2@example.com")
    _assign_administrator_role(test_session, admin_id)
    _, user_token = _register_test_user(client, "donor2@example.com")

    campaign_id = _create_test_campaign(client, {"Authorization": f"Bearer {admin_token}"})
    headers = {"Authorization": f"Bearer {user_token}"}

    don_res = client.post(
        "/api/v1/dons/financiers",
        json={
            "amount": 1500.00,
            "id_campaign": campaign_id,
            "is_anonymous": False,
        },
        headers=headers,
    )
    don_id = don_res.json()["id_don_f"]

    pay_res = client.post(f"/api/v1/dons/financiers/{don_id}/pay", headers=headers)
    assert pay_res.status_code == 200
    assert "mock-payment-gateway.com" in pay_res.json()["payment_url"]

    status_res = client.get(f"/api/v1/dons/financiers/{don_id}/payment-status", headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "Success"


def test_get_donation_detail_and_receipt(donations_client) -> None:
    client, test_session = donations_client
    admin_id, admin_token = _register_test_user(client, "admin_don4@example.com")
    _assign_administrator_role(test_session, admin_id)
    _, user_token = _register_test_user(client, "donor4@example.com")

    campaign_id = _create_test_campaign(client, {"Authorization": f"Bearer {admin_token}"})
    user_headers = {"Authorization": f"Bearer {user_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Créer un don anonyme (statut Pending)
    don = client.post(
        "/api/v1/dons/financiers",
        json={
            "amount": 300.00,
            "id_campaign": campaign_id,
            "is_anonymous": True,
        },
        headers=user_headers,
    ).json()
    don_id = don["id_don_f"]

    # 2. Détail du don (DON-05)
    detail = client.get(f"/api/v1/dons/{don_id}", headers=user_headers)
    assert detail.status_code == 200
    assert detail.json()["is_anonymous"] is True
    assert detail.json()["status"] == "Pending"

    # 3. Receipt AVANT paiement -> 400 (DON-06 refuse les non-Success)
    receipt_fail = client.get(f"/api/v1/dons/{don_id}/receipt", headers=user_headers)
    assert receipt_fail.status_code == 400

    # 4. Payer + confirmer
    client.post(f"/api/v1/dons/financiers/{don_id}/pay", headers=user_headers)
    client.get(
        f"/api/v1/dons/financiers/{don_id}/payment-status",
        headers=user_headers,
    )

    # 5. Receipt APRÈS paiement -> 200 + PDF valide (généré en mémoire)
    receipt_ok = client.get(f"/api/v1/dons/{don_id}/receipt", headers=user_headers)
    assert receipt_ok.status_code == 200
    assert receipt_ok.headers["content-type"].startswith("application/pdf")
    assert receipt_ok.content[:4] == b"%PDF"
    assert len(receipt_ok.content) > 0
    assert receipt_ok.headers.get("cache-control") == "no-store"

    # 6. Accessible aussi par l'admin (CurrentUser)
    receipt_admin = client.get(f"/api/v1/dons/{don_id}/receipt", headers=admin_headers)
    assert receipt_admin.status_code == 200
    assert receipt_admin.content[:4] == b"%PDF"
# ============================================================
# NOUVEAUX TESTS (DON-04, DON-07, DON-09)
# ============================================================


def test_don04_list_my_donations(donations_client) -> None:
    client, test_session = donations_client
    admin_id, admin_token = _register_test_user(client, "admin_don_me@example.com")
    _assign_administrator_role(test_session, admin_id)
    _, user_token = _register_test_user(client, "donor_me@example.com")

    campaign_id = _create_test_campaign(client, {"Authorization": f"Bearer {admin_token}"})
    user_headers = {"Authorization": f"Bearer {user_token}"}

    res1 = client.post(
        "/api/v1/dons/financiers",
        json={
            "amount": 100.00,
            "id_campaign": campaign_id,
            "is_anonymous": False,
        },
        headers=user_headers,
    )
    don1_id = res1.json()["id_don_f"]

    with test_session() as session:
        don1 = session.get(FinancialDon, UUID(don1_id))
        don1.created_at = datetime.now(UTC) - timedelta(days=1)
        session.commit()

    client.post(
        "/api/v1/dons/financiers",
        json={
            "amount": 200.00,
            "id_campaign": campaign_id,
            "is_anonymous": False,
        },
        headers=user_headers,
    )

    response = client.get("/api/v1/dons/me", headers=user_headers)

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["amount"] == "200.00"
    assert response.json()[1]["amount"] == "100.00"


def test_don07_list_all_donations_with_filters(donations_client) -> None:
    """DON-07 : Tester la liste globale avec filtres."""
    client, test_session = donations_client
    admin_id, admin_token = _register_test_user(client, "admin_don_all@example.com")
    _assign_administrator_role(test_session, admin_id)
    _, user_token = _register_test_user(client, "donor_all@example.com")

    campaign1 = _create_test_campaign(client, {"Authorization": f"Bearer {admin_token}"})
    campaign2 = _create_test_campaign(client, {"Authorization": f"Bearer {admin_token}"})

    user_headers = {"Authorization": f"Bearer {user_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    payload_10 = {
        "amount": 10.00,
        "id_campaign": campaign1,
        "is_anonymous": False,
    }
    payload_20 = {
        "amount": 20.00,
        "id_campaign": campaign1,
        "is_anonymous": False,
    }
    payload_30 = {
        "amount": 30.00,
        "id_campaign": campaign2,
        "is_anonymous": False,
    }

    client.post("/api/v1/dons/financiers", json=payload_10, headers=user_headers)
    client.post("/api/v1/dons/financiers", json=payload_20, headers=user_headers)
    client.post("/api/v1/dons/financiers", json=payload_30, headers=user_headers)

    res_all = client.get("/api/v1/dons", headers=admin_headers)
    assert res_all.status_code == 200
    assert len(res_all.json()) == 3

    res_filtered = client.get(f"/api/v1/dons?id_campaign={campaign1}", headers=admin_headers)
    assert res_filtered.status_code == 200
    assert len(res_filtered.json()) == 2


def test_don09_list_successful_donations_by_campaign(
    donations_client,
) -> None:
    """DON-09 : Tous les dons réussis d'une campagne."""
    client, test_session = donations_client
    admin_id, admin_token = _register_test_user(client, "admin_don_camp@example.com")
    _assign_administrator_role(test_session, admin_id)
    _, user_token = _register_test_user(client, "donor_camp@example.com")

    campaign_id = _create_test_campaign(client, {"Authorization": f"Bearer {admin_token}"})
    user_headers = {"Authorization": f"Bearer {user_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    don_ok = client.post(
        "/api/v1/dons/financiers",
        json={
            "amount": 1000.00,
            "id_campaign": campaign_id,
            "is_anonymous": False,
        },
        headers=user_headers,
    ).json()
    client.post(
        f"/api/v1/dons/financiers/{don_ok['id_don_f']}/pay",
        headers=user_headers,
    )
    client.get(
        f"/api/v1/dons/financiers/{don_ok['id_don_f']}/payment-status",
        headers=user_headers,
    )

    client.post(
        "/api/v1/dons/financiers",
        json={
            "amount": 200.00,
            "id_campaign": campaign_id,
            "is_anonymous": False,
        },
        headers=user_headers,
    )

    response = client.get(f"/api/v1/dons/{campaign_id}/succeed", headers=admin_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["amount"] == "1000.00"
    assert response.json()[0]["status"] == "Success"
