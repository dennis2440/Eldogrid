"""M4: send SMS. Every message goes to OUTBOX (the dashboard 'phone screen' reads it).
Only when DEMO_MODE=false do we ALSO send through Africa's Talking."""
from datetime import datetime

from app.config import AT_API_KEY, AT_SENDER_ID, AT_USERNAME, DEMO_MODE
from app.services.phone import normalize_phone

OUTBOX: list[dict] = []


def send_sms(to: str, message: str) -> dict:
    to = normalize_phone(to)
    entry = {
        "to": to,
        "message": message,
        "sent_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "demo" if DEMO_MODE else "live",
    }
    OUTBOX.append(entry)
    if not DEMO_MODE:
        _send_live(to, message)
    return entry


def _send_live(to: str, message: str) -> None:
    """Real send via Africa's Talking SDK. Never raises: a failed SMS must not break the demo.
    NOTE: verify the exact SDK call in the official docs when you first test this."""
    try:
        import africastalking

        africastalking.initialize(AT_USERNAME, AT_API_KEY)
        kwargs = {"sender_id": AT_SENDER_ID} if AT_SENDER_ID else {}
        africastalking.SMS.send(message, ["+" + to], **kwargs)
    except Exception as exc:  # noqa: BLE001
        print(f"[sms_client] live send failed, continuing: {exc}")
