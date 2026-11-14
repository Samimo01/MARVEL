from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.auth.models import Role, RoleAssignment, User


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(func.lower(User.email) == email.lower()))


def add_user(session: Session, user: User) -> None:
    session.add(user)
    session.flush()
    session.refresh(user)


def get_role_by_name(session: Session, role_name: str) -> Role | None:
    return session.scalar(select(Role).where(Role.role_name == role_name))


def get_latest_role_assignment(
    session: Session, user_id: UUID, role_name: str
) -> RoleAssignment | None:
    statement = (
        select(RoleAssignment)
        .join(Role, Role.id_role == RoleAssignment.id_role)
        .where(
            RoleAssignment.id_user == user_id,
            Role.role_name == role_name,
        )
        .order_by(
            RoleAssignment.created_at.desc(),
            RoleAssignment.id_role_assignment.desc(),
        )
        .limit(1)
    )
    return session.scalar(statement)


def list_role_assignments_for_user(
    session: Session, user_id: UUID
) -> list[tuple[RoleAssignment, str]]:
    statement = (
        select(RoleAssignment, Role.role_name)
        .join(Role, Role.id_role == RoleAssignment.id_role)
        .where(RoleAssignment.id_user == user_id)
        .order_by(
            RoleAssignment.created_at.desc(),
            RoleAssignment.id_role_assignment.desc(),
        )
    )
    return [
        (assignment, role_name)
        for assignment, role_name in session.execute(statement)
    ]


def list_role_assignments_for_role(
    session: Session, role_id: UUID
) -> list[RoleAssignment]:
    statement = (
        select(RoleAssignment)
        .where(RoleAssignment.id_role == role_id)
        .order_by(
            RoleAssignment.id_user,
            RoleAssignment.created_at.desc(),
            RoleAssignment.id_role_assignment.desc(),
        )
    )
    return list(session.scalars(statement).all())