"""Modèles SQLAlchemy des distributions d'aide."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, Uuid, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.modules.stock.models import Stock

if TYPE_CHECKING:
    from app.modules.beneficiaries.models import BeneficiaryFile

distribution_status_type = ENUM(
    "Planned",
    "Exited",
    "Delivered_confirmed",
    "Canceled",
    name="distribution_status",
    create_type=False,
)


class Distribution(Base):
    __tablename__ = "distributions"

    id_distrib: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    planned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        distribution_status_type, nullable=False, default="Planned", server_default="Planned"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    id_ben_file: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("beneficiary_files.id_ben_file", ondelete="CASCADE"),
        nullable=False,
    )
    id_user: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id_user", ondelete="SET NULL")
    )

    beneficiary_file: Mapped["BeneficiaryFile"] = relationship(back_populates="distributions")
    lines: Mapped[list["DistributionLine"]] = relationship(
        back_populates="distribution",
        lazy="selectin",
    )


class DistributionLine(Base):
    __tablename__ = "distribution_lines"

    id_distrib: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("distributions.id_distrib", ondelete="CASCADE"),
        primary_key=True,
    )
    id_distrib_n: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    id_stock: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("stocks.id_stock", ondelete="RESTRICT"),
        nullable=False,
    )

    distribution: Mapped["Distribution"] = relationship(back_populates="lines")
    stock: Mapped[Stock] = relationship(lazy="joined")
