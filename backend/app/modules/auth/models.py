from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

account_status_type = ENUM(
    "Enable",
    "Disable",
    name="account_status",
    create_type=False,
)


class User(Base):
    __tablename__ = "users"

    id_user: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    firstname: Mapped[str] = mapped_column(String, nullable=False)
    lastname: Mapped[str] = mapped_column(String, nullable=False)
    nickname: Mapped[str | None] = mapped_column(String, unique=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column("password", String, nullable=False)
    tel: Mapped[str | None] = mapped_column(String)
    active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")
    status: Mapped[str] = mapped_column(
        account_status_type, nullable=False, default="Enable", server_default="Enable"
    )
    is_email_enable: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default="true"
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
