from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.modules.auth.models import Role, RoleAssignment, User
from app.modules.campaigns.models import Campaign, Event
from app.modules.financial_donations.models import FinancialDon
from app.modules.treasury import repository as repo
from app.modules.treasury import service
from app.modules.treasury.models import Fund
from app.modules.treasury.schemas import ExpenseCreate, ExpenseUpdate

# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    tables = [
        User.__table__,
        Role.__table__,
        RoleAssignment.__table__,
        Campaign.__table__,
        Event.__table__,
        FinancialDon.__table__,
        Fund.__table__,
    ]

    Base.metadata.create_all(engine, tables=tables)

    TestingSession = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    session = TestingSession()

    yield session

    session.close()
    Base.metadata.drop_all(engine, tables=tables)
    engine.dispose()


@pytest.fixture
def data(db):
    user = User(
        firstname="Test",
        lastname="Treasury",
        email="treasury@test.com",
        password_hash="hashed-password",
    )
    db.add(user)
    db.flush()

    campaign = Campaign(
        title="Campagne de test",
        id_user=user.id_user,
        status="In_progress",
    )
    db.add(campaign)
    db.flush()

    event = Event(
        title="Événement de test",
        id_campaign=campaign.id_campaign,
    )
    db.add(event)
    db.flush()

    return {
        "user": user,
        "campaign": campaign,
        "event": event,
    }


def add_fund(db, event_id, user_id, amount, category="Achat", date=None):
    fund = Fund(
        amount=Decimal(str(amount)),
        category=category,
        transaction_at=date or datetime(2026, 1, 10),
        justificative="Justificatif test",
        id_event=event_id,
        id_user=user_id,
    )
    db.add(fund)
    db.flush()
    return fund


def add_donation(db, campaign_id, user_id, amount, status="Success"):
    donation = FinancialDon(
        amount=Decimal(str(amount)),
        status=status,
        is_anonymous=False,
        id_campaign=campaign_id,
        id_user=user_id,
    )
    db.add(donation)
    db.flush()
    return donation


# ============================================================
# REPOSITORY : LECTURE DES OPÉRATIONS
# ============================================================


def test_get_fund_by_id(db, data):
    fund = add_fund(db, data["event"].id_event, data["user"].id_user, -100)

    result = repo.get_fund_by_id(db, fund.id_fund)

    assert result is not None
    assert result.id_fund == fund.id_fund


def test_get_fund_by_id_not_found(db):
    assert repo.get_fund_by_id(db, uuid4()) is None


def test_list_all_funds_ordered_by_date(db, data):
    event_id = data["event"].id_event
    user_id = data["user"].id_user

    older = add_fund(
        db,
        event_id,
        user_id,
        -100,
        date=datetime(2026, 1, 1),
    )
    newer = add_fund(
        db,
        event_id,
        user_id,
        -200,
        date=datetime(2026, 1, 15),
    )

    result = repo.list_all_funds(db)

    assert len(result) == 2
    assert result[0].id_fund == newer.id_fund
    assert result[1].id_fund == older.id_fund


def test_list_expenses_by_event(db, data):
    event_id = data["event"].id_event
    user_id = data["user"].id_user

    expense1 = add_fund(
        db,
        event_id,
        user_id,
        -100,
        "Transport",
        datetime(2026, 1, 5),
    )
    expense2 = add_fund(
        db,
        event_id,
        user_id,
        -200,
        "Achat",
        datetime(2026, 1, 10),
    )
    add_fund(db, event_id, user_id, 300, "Revenu")

    result = repo.list_expenses_by_event(db, event_id)

    assert len(result) == 2
    assert all(item.amount < 0 for item in result)
    assert result[0].id_fund == expense2.id_fund
    assert result[1].id_fund == expense1.id_fund


def test_list_expenses_with_category_filter(db, data):
    event_id = data["event"].id_event
    user_id = data["user"].id_user

    add_fund(db, event_id, user_id, -100, "Transport")
    expected = add_fund(db, event_id, user_id, -200, "Achat")

    result = repo.list_expenses_by_event(db, event_id, category="Achat")

    assert len(result) == 1
    assert result[0].id_fund == expected.id_fund


def test_list_expenses_with_date_filters(db, data):
    event_id = data["event"].id_event
    user_id = data["user"].id_user

    add_fund(
        db,
        event_id,
        user_id,
        -100,
        date=datetime(2026, 1, 1),
    )
    expected = add_fund(
        db,
        event_id,
        user_id,
        -200,
        date=datetime(2026, 1, 10),
    )
    add_fund(
        db,
        event_id,
        user_id,
        -300,
        date=datetime(2026, 1, 20),
    )

    result = repo.list_expenses_by_event(
        db,
        event_id,
        start_date=datetime(2026, 1, 5),
        end_date=datetime(2026, 1, 15),
    )

    assert len(result) == 1
    assert result[0].id_fund == expected.id_fund


def test_list_expenses_with_pagination(db, data):
    event_id = data["event"].id_event
    user_id = data["user"].id_user

    for day in range(1, 5):
        add_fund(
            db,
            event_id,
            user_id,
            -day * 100,
            date=datetime(2026, 1, day),
        )

    result = repo.list_expenses_by_event(db, event_id, limit=2, offset=1)

    assert len(result) == 2
    assert result[0].amount == Decimal("-300.00")
    assert result[1].amount == Decimal("-200.00")


# ============================================================
# REPOSITORY : ÉCRITURE
# ============================================================


def test_add_fund(db, data):
    fund = Fund(
        amount=Decimal("-150.00"),
        category="Transport",
        transaction_at=datetime(2026, 1, 10),
        id_event=data["event"].id_event,
        id_user=data["user"].id_user,
    )

    repo.add_fund(db, fund)
    db.commit()

    assert db.get(Fund, fund.id_fund) is not None


def test_update_fund_repository(db, data):
    fund = add_fund(db, data["event"].id_event, data["user"].id_user, -100)

    result = repo.update_fund(
        db,
        fund,
        {"category": "Transport"},
    )

    assert result.category == "Transport"


# ============================================================
# REPOSITORY : AGRÉGATS GLOBAUX
# ============================================================


def test_get_global_donations_total(db, data):
    campaign_id = data["campaign"].id_campaign
    user_id = data["user"].id_user

    add_donation(db, campaign_id, user_id, 500)
    add_donation(db, campaign_id, user_id, 200)
    add_donation(db, campaign_id, user_id, 100, "Failure")

    result = repo.get_global_donations_total(db)

    assert result == Decimal("700.00")


def test_get_global_fund_totals(db, data):
    event_id = data["event"].id_event
    user_id = data["user"].id_user

    add_fund(db, event_id, user_id, 300)
    add_fund(db, event_id, user_id, -100)
    add_fund(db, event_id, user_id, -50)

    result = repo.get_global_fund_totals(db)

    assert result["total_income"] == Decimal("300.00")
    assert result["total_expenses"] == Decimal("150.00")


# ============================================================
# REPOSITORY : AGRÉGATS PAR CAMPAGNE
# ============================================================


def test_get_campaign_donations_total(db, data):
    campaign_id = data["campaign"].id_campaign
    user_id = data["user"].id_user

    add_donation(db, campaign_id, user_id, 500)
    add_donation(db, campaign_id, user_id, 200)
    add_donation(db, campaign_id, user_id, 100, "Failure")

    result = repo.get_campaign_donations_total(db, campaign_id)

    assert result == Decimal("700.00")


def test_get_campaign_fund_totals(db, data):
    event_id = data["event"].id_event
    user_id = data["user"].id_user
    campaign_id = data["campaign"].id_campaign

    add_fund(db, event_id, user_id, 300)
    add_fund(db, event_id, user_id, -100)

    result = repo.get_campaign_fund_totals(db, campaign_id)

    assert result["total_fund_income"] == Decimal("300.00")
    assert result["total_expenses"] == Decimal("100.00")


def test_get_campaign_events_fund_totals(db, data):
    event_id = data["event"].id_event
    user_id = data["user"].id_user
    campaign_id = data["campaign"].id_campaign

    add_fund(db, event_id, user_id, 500)
    add_fund(db, event_id, user_id, -200)

    result = repo.get_campaign_events_fund_totals(db, campaign_id)

    assert result["total_income"] == Decimal("500.00")
    assert result["total_expenses"] == Decimal("200.00")


# ============================================================
# REPOSITORY : AGRÉGATS PAR ÉVÉNEMENT
# ============================================================


def test_get_event_fund_totals(db, data):
    event_id = data["event"].id_event
    user_id = data["user"].id_user

    add_fund(db, event_id, user_id, 400)
    add_fund(db, event_id, user_id, -150)

    result = repo.get_event_fund_totals(db, event_id)

    assert result["total_income"] == Decimal("400.00")
    assert result["total_expenses"] == Decimal("150.00")


def test_get_event_by_id(db, data):
    event = repo.get_event_by_id(db, data["event"].id_event)

    assert event is not None
    assert event.id_event == data["event"].id_event


def test_get_campaign_by_id(db, data):
    campaign = repo.get_campaign_by_id(db, data["campaign"].id_campaign)

    assert campaign is not None
    assert campaign.id_campaign == data["campaign"].id_campaign


def test_list_system_campaigns(db, data):
    beneficiary = User(
        firstname="Beneficiary",
        lastname="Test",
        email="beneficiary@test.com",
        password_hash="hashed-password",
    )
    db.add(beneficiary)
    db.flush()

    beneficiary_campaign = Campaign(
        title="Campagne bénéficiaire",
        id_user=beneficiary.id_user,
    )
    db.add(beneficiary_campaign)
    db.flush()

    role = Role(role_name="Beneficiary")
    db.add(role)
    db.flush()

    db.add(
        RoleAssignment(
            assignment_type="assigned",
            id_role=role.id_role,
            id_user=beneficiary.id_user,
        )
    )
    db.flush()

    result = repo.list_system_campaigns(db)

    result_ids = [campaign.id_campaign for campaign in result]

    assert data["campaign"].id_campaign in result_ids
    assert beneficiary_campaign.id_campaign not in result_ids


# ============================================================
# REPOSITORY : EXPORT
# ============================================================


def test_list_all_expenses(db, data):
    event_id = data["event"].id_event
    user_id = data["user"].id_user

    expense = add_fund(db, event_id, user_id, -100)
    add_fund(db, event_id, user_id, 200)

    result = repo.list_all_expenses(db)

    assert len(result) == 1
    assert result[0].id_fund == expense.id_fund


def test_list_successful_donations(db, data):
    campaign_id = data["campaign"].id_campaign
    user_id = data["user"].id_user

    success = add_donation(db, campaign_id, user_id, 500)
    add_donation(db, campaign_id, user_id, 200, "Failure")

    result = repo.list_successful_donations(db)

    assert len(result) == 1
    assert result[0].id_don_f == success.id_don_f


# ============================================================
# SERVICE : TRE-01 ET TRE-02
# ============================================================


def test_service_list_funds(db, data):
    fund = add_fund(db, data["event"].id_event, data["user"].id_user, -100)

    result = service.list_funds(db)

    assert len(result) == 1
    assert result[0].id_fund == fund.id_fund


def test_service_get_fund_detail(db, data):
    fund = add_fund(db, data["event"].id_event, data["user"].id_user, -100)

    result = service.get_fund_detail(db, fund.id_fund)

    assert result.id_fund == fund.id_fund


def test_service_get_fund_detail_not_found(db):
    with pytest.raises(service.FundNotFoundError):
        service.get_fund_detail(db, uuid4())


# ============================================================
# SERVICE : TRE-03 - CRÉER UNE DÉPENSE
# ============================================================


def test_service_create_expense(db, data):
    payload = ExpenseCreate(
        amount=Decimal("150"),
        category="  Transport  ",
        transaction_at=datetime(2026, 1, 10),
        justificative="Facture test",
    )

    result = service.create_expense(
        db,
        user=data["user"],
        id_event=data["event"].id_event,
        payload=payload,
    )

    assert result.amount == Decimal("-150.00")
    assert result.category == "Transport"
    assert result.justificative == "Facture test"


def test_service_create_expense_event_not_found(db, data):
    payload = ExpenseCreate(
        amount=100,
        category="Transport",
        transaction_at=datetime(2026, 1, 10),
    )

    with pytest.raises(service.EventNotFoundError):
        service.create_expense(
            db,
            user=data["user"],
            id_event=uuid4(),
            payload=payload,
        )


def test_service_create_expense_rejects_two_justifications(db, data):
    payload = ExpenseCreate(
        amount=100,
        category="Transport",
        transaction_at=datetime(2026, 1, 10),
        justificative="Facture",
    )

    with pytest.raises(service.InvalidExpenseError):
        service.create_expense(
            db,
            user=data["user"],
            id_event=data["event"].id_event,
            payload=payload,
            image_bytes=b"image",
        )


def test_service_create_expense_with_image(db, data, monkeypatch):
    monkeypatch.setattr(
        service,
        "_upload_expense_image",
        lambda id_fund, image_bytes: "https://test/image.webp",
    )

    payload = ExpenseCreate(
        amount=100,
        category="Transport",
        transaction_at=datetime(2026, 1, 10),
    )

    result = service.create_expense(
        db,
        user=data["user"],
        id_event=data["event"].id_event,
        payload=payload,
        image_bytes=b"image",
    )

    assert result.justificative == "https://test/image.webp"


# ============================================================
# SERVICE : TRE-04 - LISTE DES DÉPENSES
# ============================================================


def test_service_list_expenses(db, data):
    expected = add_fund(db, data["event"].id_event, data["user"].id_user, -100)

    result = service.list_expenses(db, data["event"].id_event)

    assert len(result) == 1
    assert result[0].id_fund == expected.id_fund


def test_service_list_expenses_invalid_dates(db, data):
    with pytest.raises(service.InvalidExpenseError):
        service.list_expenses(
            db,
            data["event"].id_event,
            start_date=datetime(2026, 2, 1),
            end_date=datetime(2026, 1, 1),
        )


def test_service_list_expenses_event_not_found(db):
    with pytest.raises(service.EventNotFoundError):
        service.list_expenses(db, uuid4())


# ============================================================
# SERVICE : MODIFICATION D'UNE DÉPENSE
# ============================================================


def test_service_update_expense(db, data):
    fund = add_fund(
        db,
        data["event"].id_event,
        data["user"].id_user,
        -100,
    )

    payload = ExpenseUpdate(
        amount=200,
        category="Transport",
    )

    result = service.update_expense(
        db,
        id_event=data["event"].id_event,
        id_fund=fund.id_fund,
        payload=payload,
    )

    assert result.amount == Decimal("-200.00")
    assert result.category == "Transport"


def test_service_update_expense_not_found(db, data):
    payload = ExpenseUpdate(category="Transport")

    with pytest.raises(service.FundNotFoundError):
        service.update_expense(
            db,
            id_event=data["event"].id_event,
            id_fund=uuid4(),
            payload=payload,
        )


def test_service_update_expense_wrong_event(db, data):
    fund = add_fund(
        db,
        data["event"].id_event,
        data["user"].id_user,
        -100,
    )

    payload = ExpenseUpdate(category="Transport")

    with pytest.raises(service.FundNotFoundError):
        service.update_expense(
            db,
            id_event=uuid4(),
            id_fund=fund.id_fund,
            payload=payload,
        )


def test_service_update_expense_rejects_income(db, data):
    fund = add_fund(
        db,
        data["event"].id_event,
        data["user"].id_user,
        100,
    )

    payload = ExpenseUpdate(category="Transport")

    with pytest.raises(service.FundNotFoundError):
        service.update_expense(
            db,
            id_event=data["event"].id_event,
            id_fund=fund.id_fund,
            payload=payload,
        )


def test_service_update_expense_rejects_two_justifications(db, data):
    fund = add_fund(
        db,
        data["event"].id_event,
        data["user"].id_user,
        -100,
    )

    payload = ExpenseUpdate(justificative="Facture")

    with pytest.raises(service.InvalidExpenseError):
        service.update_expense(
            db,
            id_event=data["event"].id_event,
            id_fund=fund.id_fund,
            payload=payload,
            image_bytes=b"image",
        )


def test_service_update_expense_with_image(db, data, monkeypatch):
    fund = add_fund(
        db,
        data["event"].id_event,
        data["user"].id_user,
        -100,
    )

    monkeypatch.setattr(
        service,
        "_upload_expense_image",
        lambda id_fund, image_bytes: "https://test/updated.webp",
    )

    payload = ExpenseUpdate(category="Transport")

    result = service.update_expense(
        db,
        id_event=data["event"].id_event,
        id_fund=fund.id_fund,
        payload=payload,
        image_bytes=b"image",
    )

    assert result.justificative == "https://test/updated.webp"


# ============================================================
# SERVICE : TRE-06 - BILAN GLOBAL
# ============================================================


def test_service_get_budget_summary(db, data):
    campaign_id = data["campaign"].id_campaign
    event_id = data["event"].id_event
    user_id = data["user"].id_user

    add_donation(db, campaign_id, user_id, 500)
    add_fund(db, event_id, user_id, 200)
    add_fund(db, event_id, user_id, -100)

    result = service.get_budget_summary(db)

    assert result.total_donations == Decimal("500.00")
    assert result.total_income == Decimal("200.00")
    assert result.total_expenses == Decimal("100.00")
    assert result.balance == Decimal("600.00")


# ============================================================
# SERVICE : TRE-07 - EXPORT
# ============================================================


def test_service_get_export_data_all(db, data):
    campaign_id = data["campaign"].id_campaign
    event_id = data["event"].id_event
    user_id = data["user"].id_user

    add_donation(db, campaign_id, user_id, 500)
    add_fund(db, event_id, user_id, -100)

    result = service.get_export_data(db, "all")

    assert "budget" in result
    assert "operations" in result
    assert len(result["operations"]) == 1


def test_service_get_export_data_budget_only(db):
    result = service.get_export_data(db, "budget")

    assert "budget" in result
    assert "operations" not in result


def test_service_get_export_data_operations_only(db, data):
    add_fund(db, data["event"].id_event, data["user"].id_user, -100)

    result = service.get_export_data(db, "operations")

    assert "operations" in result
    assert "budget" not in result
    assert len(result["operations"]) == 1


# ============================================================
# SERVICE : TRE-08 - GAINS D'UNE CAMPAGNE
# ============================================================


def test_service_get_campaign_gains(db, data):
    campaign_id = data["campaign"].id_campaign
    event_id = data["event"].id_event
    user_id = data["user"].id_user

    add_donation(db, campaign_id, user_id, 500)
    add_fund(db, event_id, user_id, 200)
    add_fund(db, event_id, user_id, -100)

    result = service.get_campaign_gains(db, campaign_id)

    assert result.total_donations == Decimal("500.00")
    assert result.total_fund_income == Decimal("200.00")
    assert result.total_expenses == Decimal("100.00")
    assert result.balance == Decimal("600.00")


def test_service_get_campaign_gains_not_found(db):
    with pytest.raises(service.CampaignNotFoundError):
        service.get_campaign_gains(db, uuid4())


# ============================================================
# SERVICE : TRE-09 - GAINS DES CAMPAGNES SYSTÈME
# ============================================================


def test_service_get_system_campaigns_gains(db, data):
    result = service.get_system_campaigns_gains(db)

    assert len(result) == 1
    assert result[0].id_campaign == data["campaign"].id_campaign
    assert result[0].title == "Campagne de test"


# ============================================================
# SERVICE : TRE-10 - GAINS D'UN ÉVÉNEMENT
# ============================================================


def test_service_get_campaign_event_gains(db, data):
    event_id = data["event"].id_event
    campaign_id = data["campaign"].id_campaign
    user_id = data["user"].id_user

    add_fund(db, event_id, user_id, 300)
    add_fund(db, event_id, user_id, -100)

    result = service.get_campaign_event_gains(db, campaign_id, event_id)

    assert result.total_income == Decimal("300.00")
    assert result.total_expenses == Decimal("100.00")
    assert result.balance == Decimal("200.00")


def test_service_get_campaign_event_gains_wrong_campaign(db, data):
    another_campaign = Campaign(
        title="Autre campagne",
        id_user=data["user"].id_user,
    )
    db.add(another_campaign)
    db.flush()

    with pytest.raises(service.EventNotFoundError):
        service.get_campaign_event_gains(
            db,
            another_campaign.id_campaign,
            data["event"].id_event,
        )


# ============================================================
# SERVICE : TRE-11 - TOTAL DES DONS D'UNE CAMPAGNE
# ============================================================


def test_service_get_campaign_donations_total(db, data):
    campaign_id = data["campaign"].id_campaign
    user_id = data["user"].id_user

    add_donation(db, campaign_id, user_id, 500)
    add_donation(db, campaign_id, user_id, 100, "Failure")

    result = service.get_campaign_donations_total(db, campaign_id)

    assert result.total_donations == Decimal("500.00")


# ============================================================
# SERVICE : TRE-12 - GAINS CUMULÉS DES ÉVÉNEMENTS
# ============================================================


def test_service_get_campaign_events_gains(db, data):
    event_id = data["event"].id_event
    campaign_id = data["campaign"].id_campaign
    user_id = data["user"].id_user

    add_fund(db, event_id, user_id, 400)
    add_fund(db, event_id, user_id, -150)

    result = service.get_campaign_events_gains(db, campaign_id)

    assert result.total_income == Decimal("400.00")
    assert result.total_expenses == Decimal("150.00")
    assert result.balance == Decimal("250.00")


# ============================================================
# SERVICE : BILAN D'UN ÉVÉNEMENT
# ============================================================


def test_service_get_event_gains(db, data):
    event_id = data["event"].id_event
    user_id = data["user"].id_user

    add_fund(db, event_id, user_id, 400)
    add_fund(db, event_id, user_id, -150)

    result = service.get_event_gains(db, event_id)

    assert result.total_income == Decimal("400.00")
    assert result.total_expenses == Decimal("150.00")
    assert result.balance == Decimal("250.00")


def test_service_get_event_gains_not_found(db):
    with pytest.raises(service.EventNotFoundError):
        service.get_event_gains(db, uuid4())
