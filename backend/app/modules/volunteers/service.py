
"""Logique métier du module volunteers."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.volunteers import repository as repo
from app.modules.volunteers.models import Mission, SignIn

# =========================
# EXCEPTIONS MÉTIER
# =========================

class MissionNotFoundError(Exception):
    pass


class SignInNotFoundError(Exception):
    pass


class InvalidMissionStatusError(Exception):
    pass


class MissionCapacityError(Exception):
    pass


class DuplicateSignInError(Exception):
    pass


class InvalidMissionDataError(Exception):
    pass


# =========================
# STATUTS
# =========================

STATUS_TO_DB = {
    "Draft": "Draft",
    "Published": "Publish",
    "Completed": "Complete",
    "Cancelled": "Canceled",
}

DB_TO_STATUS = {
    "Draft": "Draft",
    "Publish": "Published",
    "Complete": "Completed",
    "Finished": "Completed",
    "Canceled": "Cancelled",
}


def normalize_status(status: str) -> str:
    return DB_TO_STATUS.get(status, status)


def get_mission_or_raise(
    db: Session,
    mission_id: UUID,
) -> Mission:
    mission = repo.get_mission(db, mission_id)

    if mission is None:
        raise MissionNotFoundError("Mission introuvable.")

    return mission


def validate_dates(start_at, finish_at):
    if (
        start_at is not None
        and finish_at is not None
        and finish_at <= start_at
    ):
        raise InvalidMissionDataError(
            "La date de fin doit être après la date de début."
        )


# =========================
# CRÉATION ET CONSULTATION
# =========================

def create_mission(
    db: Session,
    data: dict,
) -> Mission:
    validate_dates(
        data.get("start_at"),
        data.get("finish_at"),
    )

    data["status"] = "Draft"

    mission = repo.create_mission(db, data)

    db.commit()
    db.refresh(mission)

    return mission


def list_missions(
    db: Session,
    status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    published_only: bool = False,
) -> list[Mission]:

    if status:
        status = STATUS_TO_DB.get(status, status)

    if date_from and date_to and date_from > date_to:
        raise InvalidMissionDataError(
            "La date de début doit précéder la date de fin."
        )

    return repo.list_missions(
        db,
        status=status,
        date_from=date_from,
        date_to=date_to,
        published_only=published_only,
    )


def get_mission_detail(
    db: Session,
    mission_id: UUID,
) -> dict:

    mission = get_mission_or_raise(db, mission_id)

    active_sign_ins = repo.count_active_sign_ins(
        db,
        mission_id,
    )

    remaining_seats = None

    if mission.seat_number is not None:
        remaining_seats = max(
            mission.seat_number - active_sign_ins,
            0,
        )

    place = repo.get_mission_place(db, mission)

    return {
        "mission": mission,
        "place": place,
        "remaining_seats": remaining_seats,
    }


# =========================
# MODIFICATION ET SUPPRESSION
# =========================

def update_mission(
    db: Session,
    mission_id: UUID,
    data: dict,
) -> Mission:

    mission = get_mission_or_raise(db, mission_id)

    new_start = data.get("start_at", mission.start_at)
    new_finish = data.get("finish_at", mission.finish_at)

    validate_dates(new_start, new_finish)

    repo.update_mission(db, mission, data)

    db.commit()
    db.refresh(mission)

    return mission


def delete_mission(
    db: Session,
    mission_id: UUID,
) -> None:

    mission = get_mission_or_raise(db, mission_id)

    if mission.status != "Draft":
        raise InvalidMissionStatusError(
            "Seules les missions en brouillon peuvent être supprimées."
        )

    repo.delete_mission(db, mission)
    db.commit()


# =========================
# CHANGEMENTS DE STATUT
# =========================

def publish_mission(
    db: Session,
    mission_id: UUID,
) -> Mission:

    mission = get_mission_or_raise(db, mission_id)

    if mission.status != "Draft":
        raise InvalidMissionStatusError(
            "Seule une mission en brouillon peut être publiée."
        )

    mission.status = "Publish"

    db.commit()
    db.refresh(mission)

    # TODO : envoyer les emails aux bénévoles concernés.

    return mission


def complete_mission(
    db: Session,
    mission_id: UUID,
) -> Mission:

    mission = get_mission_or_raise(db, mission_id)

    if mission.status != "Publish":
        raise InvalidMissionStatusError(
            "Seule une mission publiée peut être terminée."
        )

    mission.status = "Complete"

    db.commit()
    db.refresh(mission)

    return mission


def cancel_mission(
    db: Session,
    mission_id: UUID,
) -> Mission:

    mission = get_mission_or_raise(db, mission_id)

    if mission.status in ("Complete", "Finished", "Canceled"):
        raise InvalidMissionStatusError(
            "Cette mission ne peut plus être annulée."
        )

    mission.status = "Canceled"

    db.commit()
    db.refresh(mission)

    # TODO : envoyer les emails aux bénévoles inscrits.

    return mission


# =========================
# INSCRIPTIONS DES BÉNÉVOLES
# =========================

def register_for_mission(
    db: Session,
    mission_id: UUID,
    user_id: UUID,
) -> SignIn:

    mission = repo.get_mission_for_update(db, mission_id)

    if mission is None:
        raise MissionNotFoundError("Mission introuvable.")

    if mission.status != "Publish":
        raise InvalidMissionStatusError(
            "Cette mission n'est pas ouverte aux inscriptions."
        )

    existing = repo.get_sign_in(
        db,
        mission_id,
        user_id,
    )

    # Une inscription existante interdit toute nouvelle tentative,
    # même si elle a été refusée ou annulée.
    if existing is not None:
        raise DuplicateSignInError(
            "Vous avez déjà effectué une inscription pour cette mission."
        )

    active_count = repo.count_active_sign_ins(
        db,
        mission_id,
    )

    # Si aucune capacité maximale n'est définie, la place est disponible.
    has_available_seat = (
        mission.seat_number is None
        or active_count < mission.seat_number
    )

    now = datetime.now(UTC)

    sign_in = SignIn(
        id_user=user_id,
        id_mission=mission_id,
        is_validated=has_available_seat,
        is_canceled=False,
        validated_at=now if has_available_seat else None,
    )

    repo.create_sign_in(db, sign_in)

    db.commit()
    db.refresh(sign_in)

    return sign_in


def cancel_registration(
    db: Session,
    mission_id: UUID,
    user_id: UUID,
) -> SignIn:

    sign_in = repo.get_sign_in(
        db,
        mission_id,
        user_id,
    )

    if sign_in is None or sign_in.is_canceled:
        raise SignInNotFoundError(
            "Inscription introuvable ou déjà annulée."
        )

    sign_in.is_canceled = True
    sign_in.is_validated = False
    sign_in.canceled_at = datetime.now(UTC)
    sign_in.validated_at = None

    db.commit()
    db.refresh(sign_in)

    return sign_in


# =========================
# GESTION DES INSCRIPTIONS
# =========================

def list_mission_sign_ins(
    db: Session,
    mission_id: UUID,
) -> list[SignIn]:

    get_mission_or_raise(db, mission_id)

    return repo.list_sign_ins(db, mission_id)


def validate_sign_in(
    db: Session,
    mission_id: UUID,
    user_id: UUID,
    is_validated: bool,
) -> SignIn:

    mission = repo.get_mission_for_update(db, mission_id)

    if mission is None:
        raise MissionNotFoundError("Mission introuvable.")

    sign_in = repo.get_sign_in(
        db,
        mission_id,
        user_id,
    )

    if sign_in is None or sign_in.is_canceled:
        raise SignInNotFoundError(
            "Inscription introuvable ou annulée."
        )

    # Une validation manuelle ne peut pas dépasser la capacité.
    if is_validated and not sign_in.is_validated:
        active_count = repo.count_active_sign_ins(
            db,
            mission_id,
        )

        if (
            mission.seat_number is not None
            and active_count >= mission.seat_number
        ):
            raise MissionCapacityError(
                "Impossible de valider : la mission est complète."
            )

    sign_in.is_validated = is_validated
    sign_in.validated_at = (
        datetime.now(UTC) if is_validated else None
    )

    repo.update_sign_in(db, sign_in, {})

    db.commit()
    db.refresh(sign_in)

    return sign_in


# =========================
# PLANNING
# =========================

def get_planning(
    db: Session,
    date_from: datetime,
    date_to: datetime,
) -> list[dict]:

    if date_from > date_to:
        raise InvalidMissionDataError(
            "La date de début doit précéder la date de fin."
        )

    missions = repo.list_missions(
        db,
        date_from=date_from,
        date_to=date_to,
    )

    planning = []

    for mission in missions:
        sign_ins = repo.list_sign_ins(
            db,
            mission.id_mission,
        )

        planning.append({
            "mission": mission,
            "place": repo.get_mission_place(db, mission),
            "sign_ins": sign_ins,
            "remaining_seats": (
                max(
                    mission.seat_number
                    - repo.count_active_sign_ins(
                        db,
                        mission.id_mission,
                    ),
                    0,
                )
                if mission.seat_number is not None
                else None
            ),
        })

    return planning


# =========================
# ESPACE PERSONNEL DU BÉNÉVOLE
# MIS-14 ET MIS-15
# =========================

def get_my_sign_ins(
    db: Session,
    user_id: UUID,
) -> list[dict]:
    """Retourne toutes les inscriptions du bénévole avec les missions."""

    rows = repo.list_user_sign_ins(db, user_id)

    result = []

    for sign_in, mission in rows:
        result.append({
            "sign_in": sign_in,
            "mission": mission,
            "place": repo.get_mission_place(db, mission),
        })

    return result


def get_my_space(
    db: Session,
    user_id: UUID,
) -> dict:
    """Construit le tableau de bord personnel du bénévole."""

    registrations = get_my_sign_ins(db, user_id)
    now = datetime.now(UTC)

    upcoming_missions = []
    history = []

    for registration in registrations:
        sign_in = registration["sign_in"]
        mission = registration["mission"]
        mission_start = mission.start_at

        if mission_start is not None:
            if mission_start.tzinfo is None:
                mission_start = mission_start.replace(
                    tzinfo=UTC
                )
            else:
                mission_start = mission_start.astimezone(UTC)

        is_upcoming = (
            sign_in.is_validated
            and not sign_in.is_canceled
            and mission.status == "Publish"
            and mission.start_at is not None
            and mission_start >= now
        )

        if is_upcoming:
            upcoming_missions.append(registration)

        elif (
            sign_in.is_canceled
            or (
                mission.start_at is not None
                and mission_start < now
            )
            or mission.status in ("Complete", "Finished", "Canceled")
        ):
            history.append(registration)

    return {
        "upcoming_missions": upcoming_missions,
        "history": history,
        # Aucun système de notifications persistantes n'est encore intégré.
        "notifications": [],
    }
