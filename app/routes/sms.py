"""M4: SMS endpoints. /sms/outbox powers the 'fake phone' panel on the dashboard."""
from fastapi import APIRouter, Form

from app.services.sms_client import OUTBOX

router = APIRouter(prefix="/sms", tags=["sms"])


@router.get("/outbox")
def outbox():
    return OUTBOX[-20:]


@router.post("/incoming")
def incoming(from_: str = Form("", alias="from"), text: str = Form("")):
    # TODO(M4): handle keywords such as PAY
    return {"received": True, "from": from_, "text": text}
