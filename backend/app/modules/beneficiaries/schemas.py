"""Schémas Pydantic du module beneficiaries (entrée et sortie distinctes)."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, EmailStr


class BeneficiaryFileStatus(StrEnum):
    ACTIVE = "Actif"
    SUSPENDED = "Suspendu"
    CLOSED = "Clôturé"


class BeneficiaryFileOut(BaseModel):
    id_user: UUID
    firstname: str
    lastname: str
    nickname: str | None
    email: EmailStr
    tel: str | None
    image_url: str | None
    created_at: datetime
    status: BeneficiaryFileStatus
