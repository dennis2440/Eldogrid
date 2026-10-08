"""M4: SMS endpoints. /sms/outbox powers the 'fake phone' panel on the dashboard."""
from fastapi import APIRouter, Form

from app.db import queries
from app.services import payment_service
from app.services.phone import normalize_phone
from app.services.sms_client import OUTBOX, send_sms

router = APIRouter(prefix="/sms", tags=["sms"])


@router.get("/outbox")
def outbox():
    return OUTBOX[-20:]


@router.post("/incoming")
def incoming(from_: str = Form("", alias="from"), text: str = Form("")):
    """Africa's Talking calls this when someone texts our shortcode.
    Keyword PAY confirms that phone's latest pending payment."""
    phone = normalize_phone(from_)
    word = text.strip().upper()
    if word == "PAY":
        pending = queries.get_latest_pending_payment(phone)
        if pending:
            payment_service.confirm_payment(pending["id"])
        else:
            send_sms(phone, "No pending payment found.")
    return {"received": True, "from": phone, "text": text}
