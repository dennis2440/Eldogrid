"""M4: send SMS. In DEMO_MODE messages go to an in-memory OUTBOX that the dashboard shows as a 'phone screen'."""
from datetime import datetime

from app.config import DEMO_MODE

OUTBOX: list[dict] = []


def send_sms(to: str, message: str) -> dict:
    entry = {"to": to, "message": message, "sent_at": datetime.now().isoformat(timespec="seconds"), "mode": "demo" if DEMO_MODE else "live"}
    OUTBOX.append(entry)
    if not DEMO_MODE:
        pass  # TODO(M4): africastalking SMS send; keep the OUTBOX append so the demo screen still works
    return entry
