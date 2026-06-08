"""WhatsApp Cloud API — sends template messages to the owner."""
import httpx

from app.config import settings

_GRAPH_URL = "https://graph.facebook.com/v21.0"


def send_lead_reminder(brand_name: str, hours: float) -> None:
    """Send a lead_unreplied reminder template to the owner's WhatsApp number."""
    url = f"{_GRAPH_URL}/{settings.whatsapp_phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": settings.whatsapp_owner_number,
        "type": "template",
        "template": {
            "name": settings.whatsapp_template_name,
            "language": {"code": "en_US"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": brand_name},
                        {"type": "text", "text": str(int(hours))},
                    ],
                }
            ],
        },
    }
    headers = {"Authorization": f"Bearer {settings.whatsapp_access_token}"}
    httpx.post(url, json=payload, headers=headers, timeout=10).raise_for_status()
