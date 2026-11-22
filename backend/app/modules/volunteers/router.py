"""Routes REST du module volunteers."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    require_campaign_editor,
    require_volunteer,
)
from app.database import get_db
from app.modules.auth import repository as auth_repo
from app.modules.auth.models import User
from app.modules.volunteers import service
from app.modules.volunteers.schemas import (
    MissionCreate,
    MissionDetailResponse,
    MissionRegistrationResponse,
    MissionResponse,
    MissionUpdate,
    MySignInResponse,
    SignInResponse,
    SignInValidation,
    VolunteerSpaceResponse,
)

router = APIRouter(tags=["Missions"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
CampaignEditor = Annotated[User, Depends(require_campaign_editor)]
Volunteer = Annotated[User, Depends(require_volunteer)]


def has_active_role(session: Session, user: User, role: str) -> bool:
    assignment = auth_repo.get_latest_role_assignment(
        session,
        user.id_user,
        role,
    )
    return (
        assignment is not None
        and assignment.assignment_type == "assigned"
    )


def require_mission_reader(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    """Autorise Volunteer, Collection_Manager et Administrator."""
    for role in ("Volunteer", "Collection_Manager", "Administrator"):
        if has_active_role(session, user, role):
            return user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Rôle requis : Volunteer, Collection_Manager ou Administrator.",
    )


MissionReader = Annotated[User, Depends(require_mission_reader)]


def mission_response(db: Session, mission) -> dict:
    result = MissionResponse.model_validate(mission).model_dump()
    result["place"] = service.repo.get_mission_place(db, mission)
    result["status"] = service.normalize_status(mission.status)
    return result


def my_sign_in_response(db: Session, registration: dict) -> dict:
    return {
        "sign_in": registration["sign_in"],
        "mission": mission_response(db, registration["mission"]),
        "place": registration["place"],
    }


def handle_service_error(exc: Exception):
    if isinstance(exc, service.MissionNotFoundError):
        raise HTTPException(404, str(exc))
    if isinstance(exc, service.SignInNotFoundError):
        raise HTTPException(404, str(exc))
    if isinstance(exc, service.InvalidMissionStatusError):
        raise HTTPException(409, str(exc))
    if isinstance(exc, service.MissionCapacityError):
        raise HTTPException(409, str(exc))
    if isinstance(exc, service.DuplicateSignInError):
        raise HTTPException(409, str(exc))
    if isinstance(exc, service.InvalidMissionDataError):
        raise HTTPException(400, str(exc))
    raise exc


@router.post(
    "/missions",
    summary="Mis01  Créer une mission",
    description="Créer une mission avec le statut initial Brouillon.",
    response_model=MissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_mission(
    payload: MissionCreate,
    db: DbSession,
    user: CampaignEditor,
):
    try:
        mission = service.create_mission(db, payload.model_dump())
        return mission_response(db, mission)
    except Exception as exc:
        db.rollback()
        handle_service_error(exc)


@router.get(
    "/missions",
    summary="Mis02  Consulter les missions",
    description="Consulter les missions avec filtres par statut et dates.",
    response_model=list[MissionResponse],
)
def list_missions(
    db: DbSession,
    user: MissionReader,
    mission_status: Annotated[str | None, Query(alias="status")] = None,
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
):
    try:
        is_staff = (
            has_active_role(db, user, "Collection_Manager")
            or has_active_role(db, user, "Administrator")
        )
        missions = service.list_missions(
            db,
            status=mission_status,
            date_from=date_from,
            date_to=date_to,
            published_only=not is_staff,
        )
        return [mission_response(db, mission) for mission in missions]
    except Exception as exc:
        handle_service_error(exc)


@router.get(
    "/missions/{mission_id}",
    summary="Mis03  Consulter les détails d'une mission",
    response_model=MissionDetailResponse,
)
def get_mission(
    mission_id: UUID,
    db: DbSession,
    user: MissionReader,
):
    try:
        result = service.get_mission_detail(db, mission_id)
        mission_data = mission_response(db, result["mission"])
        mission_data["remaining_seats"] = result["remaining_seats"]
        return mission_data
    except Exception as exc:
        handle_service_error(exc)


@router.put(
    "/missions/{mission_id}",
    summary="Mis04  Modifier une mission",
    response_model=MissionResponse,
)
def update_mission(
    mission_id: UUID,
    payload: MissionUpdate,
    db: DbSession,
    user: CampaignEditor,
):
    try:
        mission = service.update_mission(
            db,
            mission_id,
            payload.model_dump(exclude_unset=True),
        )
        return mission_response(db, mission)
    except Exception as exc:
        db.rollback()
        handle_service_error(exc)


@router.delete(
    "/missions/{mission_id}",
    summary="Mis05  Supprimer une mission",
    description="Supprimer uniquement une mission en brouillon.",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_mission(
    mission_id: UUID,
    db: DbSession,
    user: CampaignEditor,
):
    try:
        service.delete_mission(db, mission_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as exc:
        db.rollback()
        handle_service_error(exc)


@router.post(
    "/missions/{mission_id}/publish",
    summary="Mis06  Publier une mission",
    description="Publier une mission initialement en brouillon.",
    response_model=MissionResponse,
)
def publish_mission(
    mission_id: UUID,
    db: DbSession,
    user: CampaignEditor,
):
    try:
        mission = service.publish_mission(db, mission_id)
        return mission_response(db, mission)
    except Exception as exc:
        db.rollback()
        handle_service_error(exc)


@router.post(
    "/missions/{mission_id}/complete",
    summary="Mis07  Terminer une mission",
    response_model=MissionResponse,
)
def complete_mission(
    mission_id: UUID,
    db: DbSession,
    user: CampaignEditor,
):
    try:
        mission = service.complete_mission(db, mission_id)
        return mission_response(db, mission)
    except Exception as exc:
        db.rollback()
        handle_service_error(exc)


@router.post(
    "/missions/{mission_id}/cancel",
    summary="Mis08  Annuler une mission",
    response_model=MissionResponse,
)
def cancel_mission(
    mission_id: UUID,
    db: DbSession,
    user: CampaignEditor,
):
    try:
        mission = service.cancel_mission(db, mission_id)
        return mission_response(db, mission)
    except Exception as exc:
        db.rollback()
        handle_service_error(exc)


@router.get(
    "/planning",
    summary="Mis09  Consulter le planning des missions",
)
def get_planning(
    db: DbSession,
    user: CampaignEditor,
    date_from: Annotated[datetime, Query(alias="from")],
    date_to: Annotated[datetime, Query(alias="to")],
):
    try:
        results = service.get_planning(db, date_from, date_to)

        planning = []
        for item in results:
            mission_data = mission_response(db, item["mission"])
            planning.append({
                **mission_data,
                "remaining_seats": item["remaining_seats"],
                "sign_ins": [
                    SignInResponse.model_validate(sign_in).model_dump()
                    for sign_in in item["sign_ins"]
                ],
            })
        return planning
    except Exception as exc:
        handle_service_error(exc)


@router.get(
    "/missions/{mission_id}/sign-ins",
    summary="Mis10  Consulter les inscriptions d'une mission",
    response_model=list[SignInResponse],
)
def list_sign_ins(
    mission_id: UUID,
    db: DbSession,
    user: CampaignEditor,
):
    try:
        return service.list_mission_sign_ins(db, mission_id)
    except Exception as exc:
        handle_service_error(exc)


@router.patch(
    "/missions/{mission_id}/sign-ins/{user_id}/validation",
    summary="Mis11  Modifier la validation d'une inscription",
    description="Modifier le booléen is_validated d'une inscription.",
    response_model=SignInResponse,
)
def validate_sign_in(
    mission_id: UUID,
    user_id: UUID,
    payload: SignInValidation,
    db: DbSession,
    user: CampaignEditor,
):
    try:
        return service.validate_sign_in(
            db,
            mission_id,
            user_id,
            payload.is_validated,
        )
    except Exception as exc:
        db.rollback()
        handle_service_error(exc)


@router.post(
    "/missions/{mission_id}/sign-ins",
    summary="Mis12  S'inscrire à une mission",
    description=(
        "Inscription automatique : True si une place est disponible, "
        "False si la mission est complète."
    ),
    response_model=MissionRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_for_mission(
    mission_id: UUID,
    db: DbSession,
    user: Volunteer,
):
    try:
        sign_in = service.register_for_mission(
            db,
            mission_id,
            user.id_user,
        )
        message = (
            "Votre inscription est acceptée."
            if sign_in.is_validated
            else "La mission est complète. Votre inscription est refusée."
        )
        return {
            "message": message,
            "sign_in": sign_in,
        }
    except Exception as exc:
        db.rollback()
        handle_service_error(exc)


@router.delete(
    "/missions/{mission_id}/sign-ins/me",
    summary="Mis13  Annuler sa propre inscription",
    response_model=SignInResponse,
)
def cancel_my_registration(
    mission_id: UUID,
    db: DbSession,
    user: Volunteer,
):
    try:
        return service.cancel_registration(db, mission_id, user.id_user)
    except Exception as exc:
        db.rollback()
        handle_service_error(exc)


@router.get(
    "/volunteers/me/sign-ins",
    summary="Mis14  Consulter mes inscriptions",
    description=(
        "Afficher toutes les inscriptions du bénévole, "
        "avec les informations des missions et leur validation."
    ),
    response_model=list[MySignInResponse],
)
def get_my_sign_ins(
    db: DbSession,
    user: Volunteer,
):
    try:
        registrations = service.get_my_sign_ins(db, user.id_user)
        return [
            my_sign_in_response(db, registration)
            for registration in registrations
        ]
    except Exception as exc:
        handle_service_error(exc)


@router.get(
    "/volunteers/me/space",
    summary="Mis15  Consulter mon espace bénévole",
    description=(
        "Afficher les missions à venir, l'historique "
        "et les notifications disponibles."
    ),
    response_model=VolunteerSpaceResponse,
)
def get_my_space(
    db: DbSession,
    user: Volunteer,
):
    try:
        result = service.get_my_space(db, user.id_user)
        return {
            "upcoming_missions": [
                my_sign_in_response(db, registration)
                for registration in result["upcoming_missions"]
            ],
            "history": [
                my_sign_in_response(db, registration)
                for registration in result["history"]
            ],
            "notifications": result["notifications"],
        }
    except Exception as exc:
        handle_service_error(exc)