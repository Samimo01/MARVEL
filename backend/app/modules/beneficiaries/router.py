from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_beneficiary_file_staff
from app.database import get_db
from app.modules.auth.models import User
from app.modules.beneficiaries import service
from app.modules.beneficiaries.schemas import (
    BeneficiaryFileDetailOut,
    BeneficiaryFileOut,
    BeneficiaryFileStatus,
)
from app.modules.beneficiaries.service import BeneficiaryFileNotFoundError

router = APIRouter(prefix="/beneficiary-files", tags=["beneficiary files"])

DbSession = Annotated[Session, Depends(get_db)]
BeneficiaryFileStaff = Annotated[User, Depends(require_beneficiary_file_staff)]


@router.get("", response_model=list[BeneficiaryFileOut])
def list_beneficiary_files(
    db: DbSession,
    user: BeneficiaryFileStaff,
    search: Annotated[str | None, Query(max_length=100)] = None,
    status: BeneficiaryFileStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[BeneficiaryFileOut]:
    return service.list_beneficiary_files(
        db,
        search=search,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/{id_ben_file}", response_model=BeneficiaryFileDetailOut)
def get_beneficiary_file(
    id_ben_file: UUID,
    db: DbSession,
    user: BeneficiaryFileStaff,
) -> BeneficiaryFileDetailOut:
    try:
        return service.get_beneficiary_file(db, id_ben_file)
    except BeneficiaryFileNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
