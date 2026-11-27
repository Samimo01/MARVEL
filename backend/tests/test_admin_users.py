from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select

from app.modules.auth.models import RefreshToken, Role, RoleAssignment, User
from app.modules.campaigns.models import Campaign
from app.modules.financial_donations.models import FinancialDon
from app.modules.natural_donations.models import (
    Collect,
    NaturalDon,
    NaturalDonItem,
)
from app.modules.treasury.models import Fund
from app.modules.volunteers.models import Mission, SignIn
from tests.auth_helpers import _assign_administrator_role, _register_test_user


def test_admin_can_search_filter_and_paginate_users(auth_client) -> None:
    client, test_session = auth_client
    admin_id, admin_token = _register_test_user(client, "admin-list@example.com")
    active_id, _ = _register_test_user(client, "nadia@example.com")
    inactive_id, _ = _register_test_user(client, "omar@gmail.com")
    _assign_administrator_role(test_session, admin_id)

    with test_session() as session:
        active_user = session.get(User, active_id)
        inactive_user = session.get(User, inactive_id)
        assert active_user is not None
        assert inactive_user is not None
        active_user.firstname = "Nadia"
        active_user.lastname = "Bousamedi"
        inactive_user.firstname = "Omar"
        inactive_user.lastname = "Khalil"
        inactive_user.active = False
        session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    by_name = client.get(
        "/api/v1/users?search=Nadia%20Bousamedi&active=true",
        headers=headers,
    )
    by_email_and_state = client.get(
        "/api/v1/users?search=omar@gmail.com&active=false",
        headers=headers,
    )
    first_page = client.get("/api/v1/users?limit=1&offset=0", headers=headers)
    second_page = client.get("/api/v1/users?limit=1&offset=1", headers=headers)

    assert by_name.status_code == 200
    assert [user["id_user"] for user in by_name.json()] == [str(active_id)]
    assert by_email_and_state.status_code == 200
    assert [user["id_user"] for user in by_email_and_state.json()] == [str(inactive_id)]
    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert len(first_page.json()) == 1
    assert len(second_page.json()) == 1
    assert first_page.json()[0]["id_user"] != second_page.json()[0]["id_user"]
    assert "password_hash" not in first_page.json()[0]


def test_user_list_requires_administrator(auth_client) -> None:
    client, _ = auth_client
    _, token = _register_test_user(client, "regular-user@example.com")

    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_administrator_can_toggle_non_admin_accounts_only(auth_client) -> None:
    client, test_session = auth_client
    admin_id, admin_token = _register_test_user(client, "activation-admin@example.com")
    target_id, target_token = _register_test_user(client, "activation-target@example.com")
    protected_admin_id, _ = _register_test_user(client, "protected-admin@example.com")
    other_user_id, other_user_token = _register_test_user(client, "activation-other@example.com")
    _assign_administrator_role(test_session, admin_id)

    with test_session() as session:
        administrator_role = session.scalar(select(Role).where(Role.role_name == "Administrator"))
        session.add(
            RoleAssignment(
                id_user=protected_admin_id,
                id_role=administrator_role.id_role,
                assignment_type="assigned",
            )
        )
        session.commit()

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    endpoint = f"/api/v1/users/{target_id}/activation"
    deactivated = client.patch(endpoint, headers=admin_headers, json={"active": False})

    assert deactivated.status_code == 200
    assert deactivated.json()["active"] is False
    assert (
        client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {target_token}"},
        ).status_code
        == 401
    )

    with test_session() as session:
        refresh_tokens = session.scalars(
            select(RefreshToken).where(RefreshToken.id_user == target_id)
        ).all()
        assert refresh_tokens
        assert all(token.revoked_at is not None for token in refresh_tokens)

    reactivated = client.patch(endpoint, headers=admin_headers, json={"active": True})
    protected_admin = client.patch(
        f"/api/v1/users/{protected_admin_id}/activation",
        headers=admin_headers,
        json={"active": False},
    )
    forbidden = client.patch(
        f"/api/v1/users/{target_id}/activation",
        headers={"Authorization": f"Bearer {other_user_token}"},
        json={"active": False},
    )
    missing = client.patch(
        f"/api/v1/users/{uuid4()}/activation",
        headers=admin_headers,
        json={"active": False},
    )

    assert reactivated.status_code == 200
    assert reactivated.json()["active"] is True
    assert protected_admin.status_code == 409
    assert forbidden.status_code == 403
    assert missing.status_code == 404
    with test_session() as session:
        protected_admin = session.get(User, protected_admin_id)
        assert protected_admin is not None
        assert protected_admin.active is True


def test_administrator_can_get_user_detail_with_related_records(user_detail_client) -> None:
    client, test_session = user_detail_client
    admin_id, admin_token = _register_test_user(client, "detail-admin@example.com")
    target_id, target_token = _register_test_user(client, "detail-user@example.com")
    _assign_administrator_role(test_session, admin_id)

    with test_session() as session:
        volunteer_role = Role(role_name="Volunteer")
        session.add(volunteer_role)
        session.flush()
        session.add(
            RoleAssignment(
                id_user=target_id,
                id_role=volunteer_role.id_role,
                assignment_type="assigned",
            )
        )
        campaign = Campaign(title="Campaign by target", id_user=target_id)
        collect = Collect(
            place="Community center",
            planned_at=datetime.now(UTC),
            id_user=target_id,
        )
        session.add_all([campaign, collect])
        session.flush()

        mission = Mission(
            id_mission=uuid4(),
            title="Mission by target",
            required_skills=["organization"],
            status="Publish",
            id_collect=collect.id_collect,
        )
        session.add(mission)
        session.add(SignIn(id_user=target_id, id_mission=mission.id_mission))
        session.add(
            FinancialDon(
                amount=Decimal("25.00"),
                status="Success",
                id_user=target_id,
                id_campaign=campaign.id_campaign,
            )
        )
        user_donation = NaturalDon(
            recovery_mode="Deposit",
            id_user=target_id,
            id_campaign=campaign.id_campaign,
        )
        actor_donation = NaturalDon(
            recovery_mode="Collect",
            id_user=admin_id,
            validated_by=target_id,
        )
        session.add_all([user_donation, actor_donation])
        session.flush()
        session.add(
            NaturalDonItem(
                id_don_n=user_donation.id_don_n,
                id_nat=uuid4(),
                description="Winter coat",
            )
        )
        session.add(
            Fund(
                amount=Decimal("12.50"),
                category="Expense",
                transaction_at=datetime.now(UTC),
                id_user=target_id,
            )
        )
        session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get(f"/api/v1/users/{target_id}", headers=headers)

    assert response.status_code == 200
    detail = response.json()
    assert detail["id_user"] == str(target_id)
    assert detail["role_assignments"][0]["role_name"] == "Volunteer"
    assert len(detail["campaigns"]) == 1
    assert detail["mission_sign_ins"][0]["mission"]["title"] == "Mission by target"
    assert len(detail["financial_donations"]) == 1
    assert len(detail["natural_donations"]) == 2
    assert any(donation["items"] for donation in detail["natural_donations"])
    assert len(detail["collections"]) == 1
    assert len(detail["treasury_operations"]) == 1
    assert "password_hash" not in detail
    assert "refresh_tokens" not in detail

    forbidden = client.get(
        f"/api/v1/users/{target_id}",
        headers={"Authorization": f"Bearer {target_token}"},
    )
    missing = client.get(
        f"/api/v1/users/{uuid4()}",
        headers=headers,
    )
    assert forbidden.status_code == 403
    assert missing.status_code == 404
