from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=["../.env", ".env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = ""
    sarvam_api_key: str = ""
    # Named distinctly to avoid collision with DATABASE_URL in any existing .env
    sqlite_db: str = "./lipi.db"
    data_dir: str = ""
    app_version: str = "0.1.0"
    asr_mode: str = "cloud"  # 'cloud' (Sarvam) or 'edge' (Local Whisper)
    shruti_admin_user: str = "demo"
    shruti_admin_password: str = ""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000"
    allowed_origins: list[str] = []

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def validate_allowed_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        if isinstance(v, list):
            return [str(o).strip() for o in v if str(o).strip()]
        return v

    @model_validator(mode="after")
    def populate_allowed_origins(self) -> "Settings":
        if not self.allowed_origins and self.cors_origins:
            if isinstance(self.cors_origins, str):
                self.allowed_origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
            elif isinstance(self.cors_origins, list):
                self.allowed_origins = [str(o).strip() for o in self.cors_origins if str(o).strip()]
        return self


settings = Settings()

