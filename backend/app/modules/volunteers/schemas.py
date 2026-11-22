"""Schémas Pydantic du module volunteers (entrée et sortie distinctes)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

# =========================
# MISSIONS
# =========================

class MissionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    start_at: datetime | None = None
    finish_at: datetime | None = None
    seat_number: int | None = Field(default=None, ge=1)
    required_skills: list[str] = Field(default_factory=list)
    id_collect: UUID | None = None
    id_event: UUID | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.start_at is not None
            and self.finish_at is not None
            and self.finish_at <= self.start_at
        ):
            raise ValueError(
                "La date de fin doit être après la date de début."
            )
        return self


class MissionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    start_at: datetime | None = None
    finish_at: datetime | None = None
    seat_number: int | None = Field(default=None, ge=1)
    required_skills: list[str] | None = None
    id_collect: UUID | None = None
    id_event: UUID | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        start = self.start_at
        finish = self.finish_at

        if (
            start is not None
            and finish is not None
            and finish <= start
        ):
            raise ValueError(
                "La date de fin doit être après la date de début."
            )
        return self


class MissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_mission: UUID
    title: str
    start_at: datetime | None
    finish_at: datetime | None
    seat_number: int | None
    required_skills: list[str]
    status: str
    id_collect: UUID | None
    id_event: UUID | None
    place: str | None = None


class MissionDetailResponse(MissionResponse):
    remaining_seats: int | None


# =========================
# INSCRIPTIONS
# =========================

class SignInResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_user: UUID
    id_mission: UUID
    application_date: datetime
    is_validated: bool
    is_canceled: bool
    canceled_at: datetime | None
    validated_at: datetime | None


class SignInValidation(BaseModel):
    is_validated: bool


class MissionRegistrationResponse(BaseModel):
    message: str
    sign_in: SignInResponse


# =========================
# ESPACE PERSONNEL DU BÉNÉVOLE
# MIS-14
# =========================

class MySignInResponse(BaseModel):
    """Une inscription accompagnée des informations de sa mission."""

    sign_in: SignInResponse
    mission: MissionResponse
    place: str | None = None


# =========================
# TABLEAU DE BORD DU BÉNÉVOLE
# MIS-15
# =========================

class VolunteerSpaceResponse(BaseModel):
    """Données du tableau de bord personnel du bénévole."""

    upcoming_missions: list[MySignInResponse]
    history: list[MySignInResponse]
    notifications: list[dict] = Field(default_factory=list)
