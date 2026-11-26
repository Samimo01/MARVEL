"""Logique métier du module beneficiaries (aucune logique métier dans le router)."""

from sqlalchemy.orm import Session

from app.modules.beneficiaries import repository
from app.modules.beneficiaries.schemas import (
    BeneficiaryFileOut,
    BeneficiaryFileStatus,
)


def list_beneficiary_files(
    session: Session,
    *,
    search: str | None,
    status: BeneficiaryFileStatus | None,
    limit: int,
    offset: int,
) -> list[BeneficiaryFileOut]:
    records = repository.list_beneficiary_files(
        session,
        search=search,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [
        BeneficiaryFileOut(
            id_user=user.id_user,
            firstname=user.firstname,
            lastname=user.lastname,
            nickname=user.nickname,
            email=user.email,
            tel=user.tel,
            image_url=user.image_url,
            created_at=user.created_at,
            status=BeneficiaryFileStatus(file_status),
        )
        for user, file_status in records
    ]
