"""Telegram Bot API — sends reminder messages to the owner."""
import httpx

from app.config import settings

_API_BASE = "https://api.telegram.org"


def send_lead_reminder(brand_name: str, hours: float) -> None:
    """Send a lead-unreplied reminder to the owner's Telegram chat."""
    text = (
        f"Reminder: {brand_name} has been waiting for a reply "
        f"for {int(hours)} hour(s). Check your leads."
    )
    url = f"{_API_BASE}/bot{settings.telegram_bot_token}/sendMessage"
    httpx.post(
        url,
        json={"chat_id": settings.telegram_chat_id, "text": text},
        timeout=10,
    ).raise_for_status()
