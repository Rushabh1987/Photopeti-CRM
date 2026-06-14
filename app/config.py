"""Environment-driven settings. Loaded once at import time."""
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core — Supabase PostgreSQL connection string
    database_url: str
    reminder_interval_minutes: int = 15

    # Meta shared
    meta_verify_token: str = ""
    meta_app_secret: str = ""  # used to verify X-Hub-Signature-256 on webhook POSTs

    # Instagram (lead capture)
    instagram_access_token: str = ""

    # Telegram Bot (owner reminders)
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    lead_keywords: str = "book,booking,shoot,photography,food shoot,rate,rates,price,pricing,available,availability,hire,quote,inquiry,package,how much,cost,interested,collaboration,project"

    # App auth
    app_secret_key: str = "change-this-in-production"
    app_username: str = "admin"
    app_password: str = "changeme"

    # Security
    session_https_only: bool = False   # set True in production (behind HTTPS)
    enable_docs: bool = False          # set True temporarily to access /docs
    max_body_size_mb: int = 1

    @model_validator(mode="after")
    def reject_insecure_defaults(self) -> "Settings":
        if self.app_secret_key == "change-this-in-production":
            raise ValueError(
                "APP_SECRET_KEY is still the default value. "
                "Generate one: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if self.app_password == "changeme":
            raise ValueError(
                "APP_PASSWORD is still the default value. Set a strong password in .env"
            )
        return self


settings = Settings()
