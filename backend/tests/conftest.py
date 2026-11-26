from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import JSON, String, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.modules.auth.models import RefreshToken, RevokedToken, Role, RoleAssignment, User
from app.modules.beneficiaries.models import BeneficiaryFile, HelpRequest, SupportingDocument
from app.modules.campaigns.models import Campaign, Event
from app.modules.distributions.models import Distribution, DistributionLine
from app.modules.financial_donations.models import FinancialDon
from app.modules.natural_donations.models import (
    Collect,
    NaturalDon,
    NaturalDonItem,
    ObjectType,
)
from app.modules.stock.models import Stock
from app.modules.treasury.models import Fund
from app.modules.volunteers.models import Mission, SignIn


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


class SQLiteArray(TypeDecorator):
    impl = JSON
    cache_ok = True


@pytest.fixture()
def auth_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        "test-jwt-secret-for-tests-at-least-32-bytes",
    )
    monkeypatch.setattr(settings, "access_token_expire_minutes", 15)
    monkeypatch.setattr(settings, "refresh_token_expire_days", 30)
    monkeypatch.setattr(settings, "auth_cookie_secure", False)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    auth_tables = [
        User.__table__,
        Role.__table__,
        RoleAssignment.__table__,
        RevokedToken.__table__,
        RefreshToken.__table__,
        BeneficiaryFile.__table__,
        HelpRequest.__table__,
        SupportingDocument.__table__,
        Distribution.__table__,
        DistributionLine.__table__,
        Stock.__table__,
    ]
    Base.metadata.create_all(engine, tables=auth_tables)
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
        Base.metadata.drop_all(engine, tables=auth_tables)
        engine.dispose()


@pytest.fixture()
def user_detail_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        "test-jwt-secret-for-tests-at-least-32-bytes",
    )
    monkeypatch.setattr(settings, "access_token_expire_minutes", 15)
    monkeypatch.setattr(settings, "refresh_token_expire_days", 30)
    monkeypatch.setattr(settings, "auth_cookie_secure", False)
    monkeypatch.setattr(Mission.__table__.c.required_skills, "type", SQLiteArray())
    monkeypatch.setattr(Mission.__table__.c.status, "type", String())
    monkeypatch.setattr(Mission.__table__.c.status, "server_default", None)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    detail_tables = [
        User.__table__,
        Role.__table__,
        RoleAssignment.__table__,
        RevokedToken.__table__,
        RefreshToken.__table__,
        Campaign.__table__,
        Event.__table__,
        FinancialDon.__table__,
        Collect.__table__,
        NaturalDon.__table__,
        NaturalDonItem.__table__,
        ObjectType.__table__,
        Fund.__table__,
        Mission.__table__,
        SignIn.__table__,
    ]
    Base.metadata.create_all(engine, tables=detail_tables)
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
        Base.metadata.drop_all(engine, tables=detail_tables)
        engine.dispose()
