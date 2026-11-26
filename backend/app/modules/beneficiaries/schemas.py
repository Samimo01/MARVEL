"""Schémas Pydantic du module beneficiaries."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.modules.auth.schemas import UserOut


class BeneficiaryFileStatus(StrEnum):
    ACTIVE = "Actif"
    SUSPENDED = "Suspendu"
    CLOSED = "Clôturé"


class BeneficiaryFileOut(BaseModel):
    id_ben_file: UUID
    id_user: UUID | None
    firstname: str | None
    lastname: str | None
    nickname: str | None
    email: str | None
    tel: str | None
    image_url: str | None
    created_at: datetime
    status: BeneficiaryFileStatus


class SupportingDocumentOut(BaseModel):
    id_supp_doc: UUID
    document_url: str
    title: str | None


class OriginRequestOut(BaseModel):
    id_help_req: UUID
    nature_need: str | None
    address: str | None
    request_at: datetime
    status: str
    reply_at: datetime | None
    reason: str | None
    help_request_type: str | None
    denomination: str | None
    registration_number: str | None
    representative_name: str | None
    representative_role: str | None
    public_support: str | None
    number_of_people: int | None
    household_composition: str | None
    employment_status: str | None
    income: Decimal | None
    id_user_response: UUID | None
    supporting_documents: list[SupportingDocumentOut]


class AidReceivedLineOut(BaseModel):
    id_distrib_n: UUID
    id_stock: UUID
    stock_title: str
    quantity: Decimal


class AidReceivedOut(BaseModel):
    id_distrib: UUID
    planned_at: datetime | None
    status: str
    created_at: datetime
    lines: list[AidReceivedLineOut]


class BeneficiaryFileDetailOut(BaseModel):
    id_ben_file: UUID
    status: BeneficiaryFileStatus
    created_at: datetime
    beneficiary: UserOut | None
    origin_request: OriginRequestOut
    received_aids: list[AidReceivedOut]
