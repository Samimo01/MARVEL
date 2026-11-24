"""Accès à la base de données du module volunteers."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import column, func, select, table
from sqlalchemy.orm import Session

from app.modules.volunteers.models import Mission, SignIn

# Références légères aux tables existantes de Supabase.
collects_table = table(
    "collects",
    column("id_collect"),
    column("place"),
)

events_table = table(
    "events",
    column("id_event"),
    column("place"),
)


# =========================
# MISSIONS
# =========================


def create_mission(db: Session, data: dict) -> Mission:
    mission = Mission(**data)
    db.add(mission)
    db.flush()
    db.refresh(mission)
    return mission


def get_mission(db: Session, mission_id: UUID) -> Mission | None:
    return db.get(Mission, mission_id)


def get_mission_for_update(
    db: Session,
    mission_id: UUID,
) -> Mission | None:
    """Verrouille la mission pendant une inscription."""
    query = select(Mission).where(Mission.id_mission == mission_id).with_for_update()
    return db.scalar(query)


def list_missions(
    db: Session,
    status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    published_only: bool = False,
) -> list[Mission]:

    query = select(Mission)

    if published_only:
        query = query.where(Mission.status == "Publish")
    elif status:
        query = query.where(Mission.status == status)

    if date_from:
        query = query.where(Mission.start_at >= date_from)

    if date_to:
        query = query.where(Mission.start_at <= date_to)

    query = query.order_by(Mission.start_at)

    return list(db.scalars(query).all())


def get_mission_place(db: Session, mission: Mission) -> str | None:
    """Récupère la localisation depuis la collecte ou l'événement."""

    if mission.id_collect:
        query = select(collects_table.c.place).where(
            collects_table.c.id_collect == mission.id_collect
        )
        return db.scalar(query)

    if mission.id_event:
        query = select(events_table.c.place).where(events_table.c.id_event == mission.id_event)
        return db.scalar(query)

    return None


def update_mission(
    db: Session,
    mission: Mission,
    data: dict,
) -> Mission:

    for key, value in data.items():
        setattr(mission, key, value)

    db.flush()
    db.refresh(mission)

    return mission


def delete_mission(db: Session, mission: Mission) -> None:
    db.delete(mission)
    db.flush()


# =========================
# INSCRIPTIONS
# =========================


def count_active_sign_ins(db: Session, mission_id: UUID) -> int:
    query = (
        select(func.count())
        .select_from(SignIn)
        .where(
            SignIn.id_mission == mission_id,
            SignIn.is_canceled.is_(False),
            SignIn.is_validated.is_(True),
        )
    )

    return db.scalar(query) or 0


def create_sign_in(db: Session, sign_in: SignIn) -> SignIn:
    db.add(sign_in)
    db.flush()
    db.refresh(sign_in)
    return sign_in


def get_sign_in(
    db: Session,
    mission_id: UUID,
    user_id: UUID,
) -> SignIn | None:
    return db.get(SignIn, (user_id, mission_id))


def list_sign_ins(db: Session, mission_id: UUID) -> list[SignIn]:
    query = select(SignIn).where(SignIn.id_mission == mission_id).order_by(SignIn.application_date)

    return list(db.scalars(query).all())


def list_user_sign_ins(
    db: Session,
    user_id: UUID,
) -> list[tuple[SignIn, Mission]]:
    """Récupère les inscriptions d'un bénévole avec leurs missions."""

    query = (
        select(SignIn, Mission)
        .join(
            Mission,
            SignIn.id_mission == Mission.id_mission,
        )
        .where(SignIn.id_user == user_id)
        .order_by(Mission.start_at.asc().nullslast())
    )

    return list(db.execute(query).all())


def update_sign_in(
    db: Session,
    sign_in: SignIn,
    data: dict,
) -> SignIn:

    for key, value in data.items():
        setattr(sign_in, key, value)

    db.flush()
    db.refresh(sign_in)

    return sign_in
