"""M4: MOCK M-Pesa. Same shape as Daraja so a real integration can replace this file later."""
from fastapi import APIRouter

router = APIRouter(tags=["payments"])


@router.post("/payments/initiate")
def initiate(body: dict):
    # TODO(M4): create payments row (PENDING), SMS the 'enter PIN' prompt, optionally auto-confirm after N seconds
    return {"payment_id": 1, "status": "PENDING", "message": "STK push simulated"}


@router.post("/mock/mpesa/callback")
def mpesa_callback(body: dict):
    # TODO(M4): mark payment PAID, credit wallet / mark order PAID, send confirmation SMS
    return {"payment_id": 1, "status": "PAID", "receipt": body.get("MpesaReceiptNumber", "QWE1R2T3Y4")}
