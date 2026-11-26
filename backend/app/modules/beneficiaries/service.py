"""Logique métier du module beneficiaries."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.auth.schemas import UserOut
from app.modules.beneficiaries import repository
from app.modules.beneficiaries.schemas import (
    AidReceivedLineOut,
    AidReceivedOut,
    BeneficiaryFileDetailOut,
    BeneficiaryFileOut,
    BeneficiaryFileStatus,
    OriginRequestOut,
    SupportingDocumentOut,
)

_API_STATUS = {
    "activated": BeneficiaryFileStatus.ACTIVE,
    "Suspended": BeneficiaryFileStatus.SUSPENDED,
    "Closed": BeneficiaryFileStatus.CLOSED,
}


class BeneficiaryFileNotFoundError(LookupError):
    pass


def _status_from_database(status: str) -> BeneficiaryFileStatus:
    return _API_STATUS[status]


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
            id_ben_file=beneficiary_file.id_ben_file,
            id_user=beneficiary.id_user if beneficiary else None,
            firstname=beneficiary.firstname if beneficiary else None,
            lastname=beneficiary.lastname if beneficiary else None,
            nickname=beneficiary.nickname if beneficiary else None,
            email=beneficiary.email if beneficiary else None,
            tel=beneficiary.tel if beneficiary else None,
            image_url=beneficiary.image_url if beneficiary else None,
            created_at=beneficiary_file.created_at,
            status=_status_from_database(beneficiary_file.status),
        )
        for beneficiary_file, beneficiary in records
    ]


def get_beneficiary_file(
    session: Session,
    id_ben_file: UUID,
) -> BeneficiaryFileDetailOut:
    beneficiary_file = repository.get_beneficiary_file(session, id_ben_file)
    if beneficiary_file is None:
        raise BeneficiaryFileNotFoundError(f"Dossier bénéficiaire {id_ben_file} introuvable.")

    request = beneficiary_file.help_request
    origin_request = OriginRequestOut(
        id_help_req=request.id_help_req,
        nature_need=request.nature_need,
        address=request.address,
        request_at=request.request_at,
        status=request.status,
        reply_at=request.reply_at,
        reason=request.reason,
        help_request_type=request.help_request_type,
        denomination=request.denomination,
        registration_number=request.registration_number,
        representative_name=request.representative_name,
        representative_role=request.representative_role,
        public_support=request.public_support,
        number_of_people=request.number_of_people,
        household_composition=request.household_composition,
        employment_status=request.employment_status,
        income=request.income,
        id_user_response=request.id_user_response,
        supporting_documents=[
            SupportingDocumentOut(
                id_supp_doc=document.id_supp_doc,
                document_url=document.document_url,
                title=document.title,
            )
            for document in request.supporting_documents
        ],
    )
    received_aids = [
        AidReceivedOut(
            id_distrib=distribution.id_distrib,
            planned_at=distribution.planned_at,
            status=distribution.status,
            created_at=distribution.created_at,
            lines=[
                AidReceivedLineOut(
                    id_distrib_n=line.id_distrib_n,
                    id_stock=line.id_stock,
                    stock_title=line.stock.title,
                    quantity=line.quantity,
                )
                for line in distribution.lines
            ],
        )
        for distribution in beneficiary_file.distributions
        if distribution.status == "Delivered_confirmed"
    ]

    return BeneficiaryFileDetailOut(
        id_ben_file=beneficiary_file.id_ben_file,
        status=_status_from_database(beneficiary_file.status),
        created_at=beneficiary_file.created_at,
        beneficiary=(
            UserOut.model_validate(request.requester) if request.requester is not None else None
        ),
        origin_request=origin_request,
        received_aids=received_aids,
    )
