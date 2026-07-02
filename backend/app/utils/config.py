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
    allow_stub_asr: bool = False
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = ""
    # JSON map of WhatsApp phone → user_id for demo/dev without profile setup
    # e.g. WHATSAPP_DEMO_PHONE_MAP='{"919876543210": "1"}'
    whatsapp_demo_phone_map: str = ""
    # Public base URL for review links sent via WhatsApp
    app_base_url: str = "https://lipi.app"
    public_rate_limit_max_attempts: int = 10
    public_rate_limit_window_seconds: int = 300
    # Named distinctly to avoid collision with DATABASE_URL in any existing .env
    sqlite_db: str = "./lipi.db"
    database_url: str = ""
    seed_demo_user: bool = False
    demo_username: str = "arush"
    demo_password: str = "1234"
    demo_full_name: str = "Dr. Arush"
    data_dir: str = ""
    app_version: str = "0.1.0"
    asr_mode: str = "cloud"  # 'cloud' (Sarvam) or 'edge' (Local Whisper)
    # ABDM / DSC settings (obtain from sandbox.abdm.gov.in)
    abdm_client_id: str = ""
    abdm_client_secret: str = ""
    abdm_sandbox: bool = True
    abdm_dsc_id: str = ""
    # Razorpay consultation fee settlement (create a payment page in Razorpay dashboard)
    razorpay_page_id: str = ""
    razorpay_key_id: str = ""
    razorpay_webhook_secret: str = ""
    consultation_fee_rupees: int = 0
    trial_session_limit: int = 5
    subscription_price_rupees: int = 999
    enable_gliner: bool = False
    gliner_model_path: str = ""
    # When True: WhatsApp pipeline holds notes for reviewer approval before sending sign link.
    # Leave False (default) for demo — pipeline auto-sends as before.
    hold_for_review: bool = False
    shruti_admin_user: str = "demo"
    shruti_admin_password: str = ""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60  # 60 minutes — sessions are clinic-bounded
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
