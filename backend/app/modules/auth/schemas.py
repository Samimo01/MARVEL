import re
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator

PHONE_RE = re.compile(r"^0[567]\d{8}$")


class RegistrationRequest(BaseModel):
    firstname: str = Field(min_length=2, max_length=100)
    lastname: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=128)
    tel: str = Field(min_length=10, max_length=10)

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


class LoginRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"