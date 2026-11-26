import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.image_utils import convert_image_to_webp
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    token_revocation_id,
    verify_password,
)
from app.core.supabase_client import USERS_BUCKET, supabase_admin
from app.modules.auth import repository
from app.modules.auth.models import RefreshToken, RevokedToken, Role, RoleAssignment, User
from app.modules.auth.schemas import (
    LoginRequest,
    RegistrationRequest,
    RoleAssignmentRequest,
    RoleAssignmentResponse,
    RoleAssignmentStatus,
    RoleName,
    UserProfileUpdate,
)


class DuplicateAccountError(ValueError):
    pass


class InvalidCredentialsError(ValueError):
    pass


class InvalidRefreshTokenError(ValueError):
    pass


@dataclass(frozen=True)
class AuthTokens:
    access_token: str
    refresh_token: str
    persistent: bool


class ManagedUserNotFoundError(LookupError):
    pass


class CannotRevokeLastAdministratorError(ValueError):
    pass


def _hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _issue_refresh_token(
    session: Session,
    *,
    user_id: UUID,
    persistent: bool,
    family_id: UUID | None = None,
) -> str:
    if settings.refresh_token_expire_days <= 0:
        raise RuntimeError("REFRESH_TOKEN_EXPIRE_DAYS doit être supérieur à zéro.")

    now = datetime.now(UTC)
    session.execute(
        delete(RefreshToken)
        .where(RefreshToken.expires_at <= now)
        .execution_options(synchronize_session=False)
    )
    token = secrets.token_urlsafe(64)
    session.add(
        RefreshToken(
            token_hash=_hash_refresh_token(token),
            family_id=family_id or uuid4(),
            id_user=user_id,
            persistent=persistent,
            expires_at=now + timedelta(days=settings.refresh_token_expire_days),
        )
    )
    return token


def _issue_auth_tokens(
    session: Session,
    *,
    user_id: UUID,
    persistent: bool,
    family_id: UUID | None = None,
) -> AuthTokens:
    return AuthTokens(
        access_token=create_access_token(str(user_id)),
        refresh_token=_issue_refresh_token(
            session,
            user_id=user_id,
            persistent=persistent,
            family_id=family_id,
        ),
        persistent=persistent,
    )


def authenticate_user(session: Session, payload: LoginRequest) -> AuthTokens:
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

    tokens = _issue_auth_tokens(
        session,
        user_id=user.id_user,
        persistent=payload.remember_me,
    )
    session.commit()
    return tokens


def rotate_refresh_token(session: Session, token: str) -> AuthTokens:
    now = datetime.now(UTC)
    token_record = session.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == _hash_refresh_token(token))
        .with_for_update()
    )
    if token_record is None:
        raise InvalidRefreshTokenError

    if token_record.revoked_at is not None:
        _revoke_refresh_family(session, token_record.family_id, now)
        session.commit()
        raise InvalidRefreshTokenError

    expires_at = token_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= now:
        token_record.revoked_at = now
        session.commit()
        raise InvalidRefreshTokenError

    user = session.get(User, token_record.id_user)
    if user is None or not user.active:
        _revoke_refresh_family(session, token_record.family_id, now)
        session.commit()
        raise InvalidRefreshTokenError

    token_record.revoked_at = now
    tokens = _issue_auth_tokens(
        session,
        user_id=user.id_user,
        persistent=token_record.persistent,
        family_id=token_record.family_id,
    )
    session.commit()
    return tokens


def _revoke_refresh_family(session: Session, family_id: UUID, now: datetime) -> None:
    session.execute(
        update(RefreshToken)
        .where(
            RefreshToken.family_id == family_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )


def revoke_refresh_token(session: Session, *, token: str, user_id: UUID) -> None:
    token_record = session.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == _hash_refresh_token(token))
        .with_for_update()
    )
    if token_record is None or token_record.id_user != user_id:
        return

    _revoke_refresh_family(session, token_record.family_id, datetime.now(UTC))
    session.commit()


def revoke_access_token(session: Session, *, token: str, user_id: UUID) -> None:
    payload = decode_token(token)
    if payload.get("sub") != str(user_id):
        raise InvalidCredentialsError("Token invalide.")

    expires_at = payload.get("exp")
    if not isinstance(expires_at, (int, float)):
        raise InvalidCredentialsError("Le token n'a pas de date d'expiration valide.")

    now = datetime.now(UTC)
    session.execute(delete(RevokedToken).where(RevokedToken.expires_at <= now))
    session.add(
        RevokedToken(
            token_id=token_revocation_id(token, payload),
            id_user=user_id,
            expires_at=datetime.fromtimestamp(expires_at, UTC),
        )
    )
    session.commit()


def register_user(
    session: Session,
    payload: RegistrationRequest,
    *,
    image_bytes: bytes | None = None,
) -> tuple[User, AuthTokens]:
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
        tokens = _issue_auth_tokens(
            session,
            user_id=user.id_user,
            persistent=True,
        )
        if image_bytes is not None:
            user.image_url = _upload_user_image(
                user.id_user,
                image_bytes,
                replace=False,
            )
        session.commit()
        session.refresh(user)
        return user, tokens
    except IntegrityError as exc:
        session.rollback()
        raise DuplicateAccountError("L'adresse e-mail ou le pseudonyme est déjà utilisé.") from exc
    except DuplicateAccountError:
        session.rollback()
        raise


def update_user_profile(
    session: Session,
    *,
    user: User,
    payload: UserProfileUpdate,
) -> User:
    changes = payload.model_dump(exclude_unset=True)
    if "email" in changes:
        email = str(changes["email"]).strip().lower()
        existing_user = repository.get_user_by_email(session, email)
        if existing_user is not None and existing_user.id_user != user.id_user:
            raise DuplicateAccountError("Un compte utilise déjà cette adresse e-mail.")
        changes["email"] = email

    for field, value in changes.items():
        setattr(user, field, value)
    user.updated_at = datetime.now(UTC)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise DuplicateAccountError("Un compte utilise déjà cette adresse e-mail.") from exc

    session.refresh(user)
    return user


def list_user_role_assignments(session: Session, user_id: UUID) -> list[RoleAssignmentResponse]:
    if session.get(User, user_id) is None:
        raise ManagedUserNotFoundError(f"Utilisateur {user_id} introuvable.")

    latest_by_role: dict[str, RoleAssignmentResponse] = {}
    for assignment, role_name in repository.list_role_assignments_for_user(session, user_id):
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


def list_active_user_roles(session: Session, user_id: UUID) -> list[RoleName]:
    return [
        assignment.role_name
        for assignment in list_user_role_assignments(session, user_id)
        if assignment.assignment_type == RoleAssignmentStatus.ASSIGNED
    ]


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

    current_assignment = repository.get_latest_role_assignment(session, user_id, role_name.value)
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


# ============================================================
# Exceptions images
# ============================================================
class UserNotFoundError(LookupError):
    pass


class ImageAlreadyExistsError(ValueError):
    pass


class UnauthorizedImageActionError(PermissionError):
    pass


# ============================================================
# Helper interne
# ============================================================
def _upload_user_image(
    id_user: UUID,
    image_bytes: bytes,
    *,
    replace: bool = False,
) -> str:
    """Convertit en WebP, upload vers Supabase, retourne l'URL publique."""
    webp_bytes = convert_image_to_webp(image_bytes, quality=85, max_width=800)
    path = f"{id_user}/avatar.webp"

    supabase_admin.storage.from_(USERS_BUCKET).upload(
        path=path,
        file=webp_bytes,
        file_options={
            "content-type": "image/webp",
            "upsert": "true" if replace else "false",
        },
    )
    return supabase_admin.storage.from_(USERS_BUCKET).get_public_url(path)


def _is_administrator(session: Session, user_id: UUID) -> bool:
    """Vérifie si l'utilisateur a un rôle Administrator actif."""
    assignment = repository.get_latest_role_assignment(session, user_id, "Administrator")
    return assignment is not None and assignment.assignment_type == "assigned"


# ============================================================
# AUT-09 : Upload public (pendant l'inscription)
# ============================================================
def upload_user_image(
    session: Session,
    *,
    id_user: UUID,
    image_bytes: bytes,
) -> User:
    """AUT-09 : Upload public de la photo d'un utilisateur (avant connexion)."""
    user = repository.get_user_by_id(session, id_user)
    if user is None:
        raise UserNotFoundError(f"Utilisateur {id_user} introuvable.")

    if user.image_url:
        raise ImageAlreadyExistsError("Une image existe déjà. Utilisez PATCH /auth/{id}/image.")

    url = _upload_user_image(id_user, image_bytes, replace=False)
    user.image_url = url
    session.commit()
    session.refresh(user)
    return user


# ============================================================
# AUT-10 : Remplacement authentifié (self ou admin)
# ============================================================
def replace_user_image(
    session: Session,
    *,
    current_user: User,
    id_user: UUID,
    image_bytes: bytes,
) -> User:
    """AUT-10 : Remplace la photo d'un utilisateur (self ou admin)."""
    target = repository.get_user_by_id(session, id_user)
    if target is None:
        raise UserNotFoundError(f"Utilisateur {id_user} introuvable.")

    is_self = current_user.id_user == target.id_user
    is_admin = _is_administrator(session, current_user.id_user)

    if not is_self and not is_admin:
        raise UnauthorizedImageActionError("Vous ne pouvez remplacer que votre propre photo.")

    url = _upload_user_image(id_user, image_bytes, replace=True)
    target.image_url = url
    session.commit()
    session.refresh(target)
    return target
