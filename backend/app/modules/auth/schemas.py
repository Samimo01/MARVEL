from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator


class RegistrationRequest(BaseModel):
    firstname: str = Field(min_length=1, max_length=100)
    lastname: str = Field(min_length=1, max_length=100)
    nickname: str | None = Field(default=None, max_length=100)
    email: EmailStr
    password: SecretStr = Field(min_length=12, max_length=128)
    tel: str | None = Field(default=None, max_length=30)

    @field_validator("firstname", "lastname")
    @classmethod
    def strip_required_names(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Ce champ ne peut pas être vide.")
        return value

    @field_validator("nickname", "tel")
    @classmethod
    def strip_optional_values(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class RegistrationResponse(BaseModel):
    message: str
    id_user: UUID


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
