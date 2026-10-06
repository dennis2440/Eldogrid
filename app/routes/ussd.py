"""M4: USSD callback from Africa's Talking. Stateless: rebuild state from `text` (e.g. '2*1*50')."""
from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["ussd"])

MAIN_MENU = "CON Welcome to EldoGrid\n1. Farm advice\n2. Order compost\n3. Top up wallet\n4. Check balance"


@router.post("/ussd", response_class=PlainTextResponse)
def ussd(
    sessionId: str = Form(""),
    serviceCode: str = Form(""),
    phoneNumber: str = Form(""),
    text: str = Form(""),
):
    steps = text.split("*") if text else []
    if not steps:
        return MAIN_MENU
    # TODO(M4): build the menu state machine here. Responses must start with CON or END.
    return "END Coming soon."
