from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.auth.models import User


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(func.lower(User.email) == email.lower()))


def get_user_by_nickname(session: Session, nickname: str) -> User | None:
    return session.scalar(select(User).where(User.nickname == nickname))


def add_user(session: Session, user: User) -> None:
    session.add(user)
    session.flush()
