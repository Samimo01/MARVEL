from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth import repository
from app.modules.auth.models import Role, RoleAssignment, User
from app.modules.auth.schemas import (
    LoginRequest,
    RegistrationRequest,
    RoleAssignmentRequest,
    RoleAssignmentResponse,
    RoleAssignmentStatus,
    RoleName,
)


class DuplicateAccountError(ValueError):
    pass


class InvalidCredentialsError(ValueError):
    pass


class ManagedUserNotFoundError(LookupError):
    pass


class CannotRevokeLastAdministratorError(ValueError):
    pass


def authenticate_user(session: Session, payload: LoginRequest) -> str:
    email = str(payload.email).strip().lower()
    user = repository.get_user_by_email(session, email)
    if (
        user is None
        or not user.active
        or not verify_password(
            payload.password.get_secret_value(),
            user.password_hash,
        )
    ):
        raise InvalidCredentialsError("E-mail ou mot de passe incorrect.")

    return create_access_token(str(user.id_user))


def register_user(session: Session, payload: RegistrationRequest) -> tuple[User, str]:
    email = str(payload.email).strip().lower()

    try:
        if repository.get_user_by_email(session, email) is not None:
            raise DuplicateAccountError("Un compte utilise déjà cette adresse e-mail.")

        user = User(
            firstname=payload.firstname,
            lastname=payload.lastname,
            nickname=None,
            email=email,
            password_hash=hash_password(payload.password.get_secret_value()),
            tel=payload.tel,
        )
        repository.add_user(session, user)
        access_token = create_access_token(str(user.id_user))
        session.commit()
        session.refresh(user)
        return user, access_token
    except IntegrityError as exc:
        session.rollback()
        raise DuplicateAccountError("L'adresse e-mail ou le pseudonyme est déjà utilisé.") from exc
    except DuplicateAccountError:
        session.rollback()
        raise


def list_user_role_assignments(
    session: Session, user_id: UUID
) -> list[RoleAssignmentResponse]:
    if session.get(User, user_id) is None:
        raise ManagedUserNotFoundError(f"Utilisateur {user_id} introuvable.")

    latest_by_role: dict[str, RoleAssignmentResponse] = {}
    for assignment, role_name in repository.list_role_assignments_for_user(
        session, user_id
    ):
        latest_by_role.setdefault(
            role_name,
            RoleAssignmentResponse(
                id_role_assignment=assignment.id_role_assignment,
                id_user=assignment.id_user,
                id_role=assignment.id_role,
                role_name=RoleName(role_name),
                assignment_type=RoleAssignmentStatus(assignment.assignment_type),
                created_at=assignment.created_at,
            ),
        )
    return list(latest_by_role.values())


def _count_active_administrators(session: Session, role_id: UUID) -> int:
    latest_by_user: dict[UUID, str] = {}
    for assignment in repository.list_role_assignments_for_role(session, role_id):
        latest_by_user.setdefault(assignment.id_user, assignment.assignment_type)
    return sum(
        assignment_type == RoleAssignmentStatus.ASSIGNED.value
        for assignment_type in latest_by_user.values()
    )


def set_user_role_assignment(
    session: Session,
    *,
    user_id: UUID,
    role_name: RoleName,
    payload: RoleAssignmentRequest,
) -> RoleAssignmentResponse:
    if session.get(User, user_id) is None:
        raise ManagedUserNotFoundError(f"Utilisateur {user_id} introuvable.")

    role = repository.get_role_by_name(session, role_name.value)
    if role is None:
        role = Role(role_name=role_name.value)
        session.add(role)
        session.flush()

    current_assignment = repository.get_latest_role_assignment(
        session, user_id, role_name.value
    )
    if (
        current_assignment is not None
        and current_assignment.assignment_type == payload.assignment_type.value
    ):
        return RoleAssignmentResponse(
            id_role_assignment=current_assignment.id_role_assignment,
            id_user=current_assignment.id_user,
            id_role=current_assignment.id_role,
            role_name=role_name,
            assignment_type=payload.assignment_type,
            created_at=current_assignment.created_at,
        )

    if (
        role_name == RoleName.ADMINISTRATOR
        and payload.assignment_type == RoleAssignmentStatus.REVOKED
        and current_assignment is not None
        and current_assignment.assignment_type == RoleAssignmentStatus.ASSIGNED.value
        and _count_active_administrators(session, role.id_role) <= 1
    ):
        raise CannotRevokeLastAdministratorError(
            "Impossible de révoquer le dernier rôle Administrator actif."
        )

    assignment = RoleAssignment(
        id_user=user_id,
        id_role=role.id_role,
        assignment_type=payload.assignment_type.value,
        created_at=datetime.now(UTC),
    )
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return RoleAssignmentResponse(
        id_role_assignment=assignment.id_role_assignment,
        id_user=assignment.id_user,
        id_role=assignment.id_role,
        role_name=role_name,
        assignment_type=payload.assignment_type,
        created_at=assignment.created_at,
    )
