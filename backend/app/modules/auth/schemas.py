import re
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)

from app.modules.campaigns.schemas import CampaignOut
from app.modules.financial_donations.schemas import FinancialDonOut
from app.modules.natural_donations.schemas import (
    CollectOut,
    NaturalDonWithItemsOut,
)
from app.modules.treasury.schemas import FundOut
from app.modules.volunteers.schemas import MySignInResponse

PHONE_RE = re.compile(r"^0[567]\d{8}$")
ALLOWED_EMAIL_DOMAINS = frozenset({"gmail.com", "example.com"})


def validate_email_domain(value: EmailStr) -> EmailStr:
    domain = str(value).rsplit("@", maxsplit=1)[-1].lower()
    if domain not in ALLOWED_EMAIL_DOMAINS:
        raise ValueError("L'adresse email doit utiliser @gmail.com ou @example.com.")
    return value


class RegistrationRequest(BaseModel):
    firstname: str = Field(min_length=2, max_length=100)
    lastname: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=128)
    tel: str = Field(min_length=10, max_length=10)

    @field_validator("email")
    @classmethod
    def require_allowed_email_domain(cls, value: EmailStr) -> EmailStr:
        return validate_email_domain(value)

    @field_validator("firstname", "lastname")
    @classmethod
    def strip_required_names(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Ce champ doit contenir au moins 2 caractères.")
        return value

    @field_validator("tel")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip()
        if not PHONE_RE.match(value):
            raise ValueError(
                "Le téléphone doit commencer par 05, 06 ou 07 et contenir 10 chiffres."
            )
        return value


class RegistrationResponse(BaseModel):
    message: str
    id_user: UUID
    nickname: str | None = None
    image_url: str | None = None


class AuthResponse(BaseModel):
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(min_length=1)
    remember_me: bool = False


class UserProfileUpdate(BaseModel):
    firstname: str | None = Field(default=None, min_length=2, max_length=100)
    lastname: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    tel: str | None = Field(default=None, min_length=10, max_length=10)

    @field_validator("firstname", "lastname")
    @classmethod
    def normalize_profile_name(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Ce champ ne peut pas être vide.")
        value = value.strip()
        if not 2 <= len(value) <= 100:
            raise ValueError("Ce champ doit contenir entre 2 et 100 caractères.")
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_profile_email(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("L'adresse email ne peut pas être vide.")
        return str(value).strip().lower()

    @field_validator("email")
    @classmethod
    def require_allowed_email_domain(cls, value: EmailStr) -> EmailStr:
        return validate_email_domain(value)

    @field_validator("tel")
    @classmethod
    def validate_profile_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not PHONE_RE.fullmatch(value):
            raise ValueError(
                "Le téléphone doit commencer par 05, 06 ou 07 et contenir 10 chiffres."
            )
        return value

    @model_validator(mode="after")
    def require_at_least_one_change(self) -> "UserProfileUpdate":
        if not self.model_fields_set:
            raise ValueError("Au moins un champ doit être renseigné.")
        return self


class UserActivationUpdate(BaseModel):
    active: bool


class PasswordChangeRequest(BaseModel):
    current_password: SecretStr = Field(min_length=1)
    new_password: SecretStr = Field(min_length=8, max_length=128)
    confirm_new_password: SecretStr = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_new_password_confirmation(self) -> "PasswordChangeRequest":
        if self.new_password.get_secret_value() != self.confirm_new_password.get_secret_value():
            raise ValueError("La confirmation du nouveau mot de passe ne correspond pas.")
        return self


class LogoutResponse(BaseModel):
    message: str


class RoleName(StrEnum):
    VOLUNTEER = "Volunteer"
    COLLECTION_MANAGER = "Collection_Manager"
    STOCK_MANAGER = "Stock_Manager"
    TREASURER = "Treasurer"
    ADMINISTRATOR = "Administrator"


class UserOut(BaseModel):
    id_user: UUID
    firstname: str
    lastname: str
    nickname: str | None = None
    email: EmailStr
    tel: str | None = None
    image_url: str | None = None
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthSessionResponse(BaseModel):
    id_user: UUID
    user: UserOut
    roles: list[RoleName] = Field(default_factory=list)


class RoleAssignmentStatus(StrEnum):
    ASSIGNED = "assigned"
    REVOKED = "revoked"


class RoleAssignmentRequest(BaseModel):
    assignment_type: RoleAssignmentStatus


class RoleAssignmentResponse(BaseModel):
    id_role_assignment: UUID
    id_user: UUID
    id_role: UUID
    role_name: RoleName
    assignment_type: RoleAssignmentStatus
    created_at: datetime


class RoleRevocationResponse(BaseModel):
    id_role_assignment: UUID
    id_user: UUID
    id_role: UUID
    role_name: str
    assignment_type: RoleAssignmentStatus
    created_at: datetime


class UserDetailOut(UserOut):
    is_email_enable: bool
    locked_until: datetime | None
    updated_at: datetime
    role_assignments: list[RoleAssignmentResponse] = Field(default_factory=list)
    campaigns: list[CampaignOut] = Field(default_factory=list)
    mission_sign_ins: list[MySignInResponse] = Field(default_factory=list)
    financial_donations: list[FinancialDonOut] = Field(default_factory=list)
    natural_donations: list[NaturalDonWithItemsOut] = Field(default_factory=list)
    collections: list[CollectOut] = Field(default_factory=list)
    treasury_operations: list[FundOut] = Field(default_factory=list)
