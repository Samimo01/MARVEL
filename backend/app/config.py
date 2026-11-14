from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  


class Settings(BaseSettings):
  

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Projet Devops - API"
    api_prefix: str = "/api/v1"

    SUPABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/DevopsProject"
    )
    cors_origins: str = "http://localhost:5173,http://localhost:5174"

    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()