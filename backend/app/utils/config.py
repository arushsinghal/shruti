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
    sqlite_db: str = "sessions.db"
    data_dir: str = ""
    app_version: str = "0.1.0"
    asr_mode: str = "cloud"  # 'cloud' (Sarvam) or 'edge' (Local Whisper)
    shruti_admin_user: str = "demo"
    shruti_admin_password: str = ""


settings = Settings()
