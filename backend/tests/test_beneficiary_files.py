from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.modules.auth.models import Role, RoleAssignment, User
from app.modules.beneficiaries.models import BeneficiaryFile, HelpRequest, SupportingDocument
from app.modules.distributions.models import Distribution, DistributionLine
from app.modules.stock.models import Stock
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


def _add_beneficiary_file(session, firstname, email, status, day):
    beneficiary = User(
        firstname=firstname,
        lastname="Test",
        email=email,
        password_hash="not-used",
    )
    session.add(beneficiary)
    session.flush()
    request = HelpRequest(
        nature_need="Aide alimentaire",
        address="12 rue des Lilas",
        request_at=datetime(2026, 1, day, tzinfo=UTC),
        status="Accept",
        id_user_request=beneficiary.id_user,
    )
    beneficiary_file = BeneficiaryFile(
        status=status,
        created_at=datetime(2026, 1, day, tzinfo=UTC),
        help_request=request,
    )
    session.add_all([request, beneficiary_file])
    session.flush()
    return beneficiary, request, beneficiary_file


def test_list_beneficiary_files_filters_search_status_and_pagination(auth_client) -> None:
    client, test_session = auth_client
    admin_id, admin_token = _register_test_user(client, "beneficiary-admin@example.com")
    _assign_administrator_role(test_session, admin_id)

    with test_session() as session:
        _add_beneficiary_file(session, "Amina", "amina@example.com", "activated", 3)
        _add_beneficiary_file(session, "Brahim", "brahim@example.com", "Suspended", 2)
        _add_beneficiary_file(session, "Chloé", "chloe@example.com", "Closed", 1)
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
    assert all(item["id_ben_file"] for item in all_files.json())
    assert [item["firstname"] for item in active_files.json()] == ["Amina"]
    assert [item["firstname"] for item in suspended_files.json()] == ["Brahim"]
    assert [item["firstname"] for item in closed_files.json()] == ["Chloé"]
    assert [item["firstname"] for item in search.json()] == ["Brahim"]
    assert [item["firstname"] for item in page.json()] == ["Brahim"]


def test_get_beneficiary_file_returns_request_and_confirmed_aid(auth_client) -> None:
    client, test_session = auth_client
    admin_id, admin_token = _register_test_user(client, "beneficiary-detail-admin@example.com")
    _assign_administrator_role(test_session, admin_id)
    with test_session() as session:
        beneficiary, request, beneficiary_file = _add_beneficiary_file(
            session,
            "Amina",
            "amina-detail@example.com",
            "activated",
            3,
        )
        session.add(
            SupportingDocument(
                id_help_req=request.id_help_req,
                document_url="https://example.com/proof.pdf",
                title="Justificatif",
            )
        )
        stock = Stock(title="Panier alimentaire", available_quantity=Decimal("10.00"))
        confirmed_distribution = Distribution(
            id_distrib=uuid4(),
            id_ben_file=beneficiary_file.id_ben_file,
            status="Delivered_confirmed",
        )
        planned_distribution = Distribution(
            id_distrib=uuid4(),
            id_ben_file=beneficiary_file.id_ben_file,
            status="Planned",
        )
        session.add_all([stock, confirmed_distribution, planned_distribution])
        session.flush()
        session.add(
            DistributionLine(
                id_distrib=confirmed_distribution.id_distrib,
                id_distrib_n=uuid4(),
                id_stock=stock.id_stock,
                quantity=Decimal("2.00"),
            )
        )
        session.commit()
        beneficiary_id = beneficiary.id_user
        request_id = request.id_help_req
        beneficiary_file_id = beneficiary_file.id_ben_file

    response = client.get(
        f"/api/v1/beneficiary-files/{beneficiary_file_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["id_ben_file"] == str(beneficiary_file_id)
    assert result["beneficiary"]["id_user"] == str(beneficiary_id)
    assert result["origin_request"]["id_help_req"] == str(request_id)
    assert result["origin_request"]["status"] == "Accept"
    assert result["origin_request"]["supporting_documents"][0]["title"] == "Justificatif"
    assert len(result["received_aids"]) == 1
    assert result["received_aids"][0]["status"] == "Delivered_confirmed"
    assert result["received_aids"][0]["lines"][0]["stock_title"] == "Panier alimentaire"
    assert result["received_aids"][0]["lines"][0]["quantity"] == "2.00"


def test_get_unknown_beneficiary_file_returns_404(auth_client) -> None:
    client, test_session = auth_client
    admin_id, admin_token = _register_test_user(client, "beneficiary-missing-admin@example.com")
    _assign_administrator_role(test_session, admin_id)

    response = client.get(
        f"/api/v1/beneficiary-files/{uuid4()}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("role_name", "allowed"),
    [
        ("Collection_Manager", True),
        ("Stock_Manager", True),
        ("Administrator", True),
        ("Treasurer", False),
    ],
)
def test_beneficiary_file_routes_require_an_allowed_role(
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
    detail = client.get(
        f"/api/v1/beneficiary-files/{uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == (200 if allowed else 403)
    assert detail.status_code == (404 if allowed else 403)
