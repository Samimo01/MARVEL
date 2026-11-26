"""Accès à la base de données du module beneficiaries (requêtes SQLAlchemy uniquement)."""

from sqlalchemy import case, or_, select
from sqlalchemy.orm import Session

from app.modules.auth.models import Role, RoleAssignment, User
from app.modules.beneficiaries.schemas import BeneficiaryFileStatus


def list_beneficiary_files(
    session: Session,
    *,
    search: str | None,
    status: BeneficiaryFileStatus | None,
    limit: int,
    offset: int,
) -> list[tuple[User, str]]:
    latest_assignment = (
        select(RoleAssignment.assignment_type)
        .join(Role, Role.id_role == RoleAssignment.id_role)
        .where(
            RoleAssignment.id_user == User.id_user,
            Role.role_name == "Beneficiary",
        )
        .order_by(
            RoleAssignment.created_at.desc(),
            RoleAssignment.id_role_assignment.desc(),
        )
        .limit(1)
        .correlate(User)
        .scalar_subquery()
    )
    file_status = case(
        (latest_assignment == "revoked", BeneficiaryFileStatus.CLOSED.value),
        (User.active.is_(False), BeneficiaryFileStatus.SUSPENDED.value),
        else_=BeneficiaryFileStatus.ACTIVE.value,
    )
    statement = select(User, file_status.label("status")).where(latest_assignment.is_not(None))

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
        statement = statement.where(file_status == status.value)

    statement = statement.order_by(User.created_at.desc(), User.id_user).limit(limit).offset(offset)
    return [(user, file_status) for user, file_status in session.execute(statement)]
