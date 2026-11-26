"""Modèles SQLAlchemy des dossiers bénéficiaires et demandes d'aide."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Uuid, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.modules.auth.models import User

if TYPE_CHECKING:
    from app.modules.distributions.models import Distribution

case_status_type = ENUM(
    "activated",
    "Suspended",
    "Closed",
    name="case_status",
    create_type=False,
)

request_status_type = ENUM(
    "Submissive",
    "In_progress",
    "Incomplete",
    "Accept",
    "Refuse",
    name="request_status",
    create_type=False,
)


class HelpRequest(Base):
    __tablename__ = "help_requests"

    id_help_req: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    nature_need: Mapped[str | None] = mapped_column(String)
    address: Mapped[str | None] = mapped_column(String)
    request_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    status: Mapped[str] = mapped_column(
        request_status_type, nullable=False, default="Submissive", server_default="Submissive"
    )
    reply_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str | None] = mapped_column(String)
    help_request_type: Mapped[str | None] = mapped_column(String)
    denomination: Mapped[str | None] = mapped_column(String)
    registration_number: Mapped[str | None] = mapped_column(String)
    representative_name: Mapped[str | None] = mapped_column(String)
    representative_role: Mapped[str | None] = mapped_column(String)
    public_support: Mapped[str | None] = mapped_column(String)
    number_of_people: Mapped[int | None] = mapped_column(Integer)
    household_composition: Mapped[str | None] = mapped_column(String)
    employment_status: Mapped[str | None] = mapped_column(String)
    income: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    id_user_response: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id_user", ondelete="SET NULL")
    )
    id_user_request: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id_user", ondelete="CASCADE")
    )

    supporting_documents: Mapped[list["SupportingDocument"]] = relationship(
        back_populates="help_request",
        lazy="selectin",
    )
    requester: Mapped[User | None] = relationship(foreign_keys=[id_user_request], lazy="joined")


class SupportingDocument(Base):
    __tablename__ = "supporting_documents"

    id_help_req: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("help_requests.id_help_req", ondelete="CASCADE"),
        primary_key=True,
    )
    id_supp_doc: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    document_url: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str | None] = mapped_column(String)

    help_request: Mapped["HelpRequest"] = relationship(back_populates="supporting_documents")


class BeneficiaryFile(Base):
    __tablename__ = "beneficiary_files"

    id_ben_file: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    status: Mapped[str] = mapped_column(
        case_status_type, nullable=False, default="activated", server_default="activated"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    id_help_req: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("help_requests.id_help_req", ondelete="CASCADE"),
        nullable=False,
    )

    help_request: Mapped["HelpRequest"] = relationship(lazy="joined")
    distributions: Mapped[list["Distribution"]] = relationship(
        back_populates="beneficiary_file",
        lazy="selectin",
    )
