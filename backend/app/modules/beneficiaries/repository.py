"""Accès aux données du module beneficiaries."""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.auth.models import User
from app.modules.beneficiaries.models import BeneficiaryFile, HelpRequest
from app.modules.beneficiaries.schemas import BeneficiaryFileStatus
from app.modules.distributions.models import Distribution, DistributionLine

_DATABASE_STATUS = {
    BeneficiaryFileStatus.ACTIVE: "activated",
    BeneficiaryFileStatus.SUSPENDED: "Suspended",
    BeneficiaryFileStatus.CLOSED: "Closed",
}


def list_beneficiary_files(
    session: Session,
    *,
    search: str | None,
    status: BeneficiaryFileStatus | None,
    limit: int,
    offset: int,
) -> list[tuple[BeneficiaryFile, User | None]]:
    statement = (
        select(BeneficiaryFile, User)
        .join(HelpRequest, HelpRequest.id_help_req == BeneficiaryFile.id_help_req)
        .outerjoin(User, User.id_user == HelpRequest.id_user_request)
    )

    if search and search.strip():
        pattern = f"%{search.strip()}%"
        full_name = User.firstname + " " + User.lastname
        statement = statement.where(
            or_(
                User.firstname.ilike(pattern),
                User.lastname.ilike(pattern),
                full_name.ilike(pattern),
                User.email.ilike(pattern),
                User.nickname.ilike(pattern),
            )
        )

    if status is not None:
        statement = statement.where(BeneficiaryFile.status == _DATABASE_STATUS[status])

    statement = (
        statement.order_by(
            BeneficiaryFile.created_at.desc(),
            BeneficiaryFile.id_ben_file,
        )
        .limit(limit)
        .offset(offset)
    )
    return list(session.execute(statement))


def get_beneficiary_file(session: Session, id_ben_file: UUID) -> BeneficiaryFile | None:
    statement = (
        select(BeneficiaryFile)
        .options(
            selectinload(BeneficiaryFile.help_request).options(
                selectinload(HelpRequest.supporting_documents),
                joinedload(HelpRequest.requester),
            ),
            selectinload(BeneficiaryFile.distributions)
            .selectinload(Distribution.lines)
            .joinedload(DistributionLine.stock),
        )
        .where(BeneficiaryFile.id_ben_file == id_ben_file)
    )
    return session.scalar(statement)
