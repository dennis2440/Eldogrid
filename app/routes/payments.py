"""M4: MOCK M-Pesa endpoints (shapes in docs/api_contract.md)."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.db import queries
from app.services import payment_service
from app.services.phone import normalize_phone

router = APIRouter(tags=["payments"])


@router.post("/payments/initiate")
def initiate(body: dict):
    phone = normalize_phone(str(body.get("phone", "")))
    kind = body.get("kind")
    amount = body.get("amount_kes")
    order_id = body.get("order_id")
    if not phone or kind not in ("ORDER", "TOPUP") or not isinstance(amount, (int, float)) or amount <= 0:
        return JSONResponse({"error": "need phone, kind (ORDER|TOPUP) and amount_kes > 0"}, status_code=400)
    if kind == "ORDER" and not (order_id and queries.get_order(order_id)):
        return JSONResponse({"error": "ORDER payments need a valid order_id"}, status_code=400)
    payment_id = payment_service.initiate_payment(phone, kind, amount, order_id)
    return {"payment_id": payment_id, "status": "PENDING", "message": "STK push simulated"}


@router.post("/mock/mpesa/callback")
def mpesa_callback(body: dict):
    """Called by the dashboard button, the PAY SMS keyword, or the auto-confirm timer.
    If no payment_id is given we confirm the latest pending payment."""
    payment_id = body.get("payment_id")
    if not payment_id:
        phone = normalize_phone(str(body.get("PhoneNumber", ""))) or None
        pending = queries.get_latest_pending_payment(phone) or queries.get_latest_pending_payment()
        payment_id = pending["id"] if pending else None
    if not payment_id:
        return JSONResponse({"error": "no pending payment"}, status_code=404)
    result = payment_service.confirm_payment(
        payment_id, body.get("MpesaReceiptNumber"), int(body.get("ResultCode", 0))
    )
    if result is None:
        return JSONResponse({"error": "payment not found"}, status_code=404)
    return result
