"""Environment-driven settings. Loaded once at import time."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core — Supabase PostgreSQL connection string
    database_url: str
    reminder_interval_minutes: int = 15

    # Meta shared
    meta_verify_token: str = ""

    # Instagram (lead capture)
    instagram_access_token: str = ""

    # WhatsApp Cloud API (owner reminders)
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_owner_number: str = ""
    whatsapp_template_name: str = "lead_reminder"
    lead_keywords: str = "book,booking,shoot,photography,food shoot,rate,rates,price,pricing,available,availability,hire,quote,inquiry,package,how much,cost,interested,collaboration,project"

    # App auth
    app_secret_key: str = "change-this-in-production"
    app_username: str = "admin"
    app_password: str = "changeme"


settings = Settings()
