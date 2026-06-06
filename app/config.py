"""Environment-driven settings. Loaded once at import time."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    database_url: str = "sqlite:///./data/crm.db"
    watch_folder: str = "./watched"
    reminder_interval_minutes: int = 15

    # Telegram (reminders to owner)
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Meta shared
    meta_verify_token: str = ""

    # Instagram
    instagram_access_token: str = ""

    # WhatsApp Cloud API
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""


settings = Settings()
