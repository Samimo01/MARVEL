from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth import repository
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginRequest, RegistrationRequest


class DuplicateAccountError(ValueError):
    pass


class InvalidCredentialsError(ValueError):
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
