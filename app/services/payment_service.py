"""M4: MOCK M-Pesa. Same flow as the real one (prompt -> PIN -> callback) but SIMULATED.
Replacing this file with Daraja STK Push is how a real version would work."""
import random
import string
import threading

from app.config import MOCK_MPESA_AUTO_CONFIRM_SECONDS
from app.db import queries
from app.services.sms_client import send_sms


def make_receipt(prefix: str = "") -> str:
    """Looks like a real M-Pesa receipt, e.g. SK3F9A2B1C."""
    body = "".join(random.choices(string.ascii_uppercase + string.digits, k=10 - len(prefix)))
    return (prefix + body)[:10]


def initiate_payment(phone: str, kind: str, amount_kes: float, order_id: int | None = None) -> int:
    """Create a PENDING payment, send the 'enter PIN' SMS, optionally auto-confirm."""
    payment_id = queries.create_payment(phone, kind, amount_kes, order_id)
    if kind == "ORDER" and order_id:
        order = queries.get_order(order_id)
        send_sms(phone, f"Pay KES {amount_kes:g} for {order['qty_kg']:g}kg compost. Enter M-Pesa PIN.")
    else:
        send_sms(phone, f"Top up KES {amount_kes:g}. Enter M-Pesa PIN.")
    if MOCK_MPESA_AUTO_CONFIRM_SECONDS > 0:
        threading.Timer(MOCK_MPESA_AUTO_CONFIRM_SECONDS, confirm_payment, args=(payment_id,)).start()
    return payment_id


def start_order_mpesa(phone: str, qty_kg: float, amount_kes: float) -> int:
    order_id = queries.create_order(phone, qty_kg, amount_kes)
    return initiate_payment(phone, "ORDER", amount_kes, order_id)


def pay_order_from_wallet(phone: str, qty_kg: float, amount_kes: float) -> str | None:
    """Returns the receipt, or None if the wallet balance was too low."""
    if not queries.debit_wallet(phone, amount_kes):
        return None
    receipt = make_receipt("WL")
    order_id = queries.create_order(phone, qty_kg, amount_kes)
    queries.mark_order_paid(order_id, receipt)
    queries.deduct_ready_stock(qty_kg)
    send_sms(phone, f"Order confirmed. {qty_kg:g}kg compost. Receipt {receipt}.")
    return receipt


def confirm_payment(payment_id: int, receipt: str | None = None, result_code: int = 0) -> dict | None:
    """What the M-Pesa callback does. Safe to call twice (second call changes nothing)."""
    payment = queries.get_payment(payment_id)
    if payment is None:
        return None
    if payment["status"] != "PENDING":                      # already handled
        return {"payment_id": payment_id, "status": payment["status"], "receipt": payment["receipt"]}
    if result_code != 0:                                     # customer cancelled / wrong PIN
        queries.mark_payment_failed(payment_id)
        send_sms(payment["phone"], "Payment was not completed. Please try again.")
        return {"payment_id": payment_id, "status": "FAILED", "receipt": None}

    receipt = receipt or make_receipt()
    queries.mark_payment_paid(payment_id, receipt)
    phone, amount = payment["phone"], payment["amount_kes"]

    if payment["kind"] == "TOPUP":
        queries.credit_wallet(phone, amount)
        bal = queries.get_wallet_balance(phone)
        send_sms(phone, f"Top-up of KES {amount:g} received. Balance KES {bal:g}. Receipt {receipt}.")
    else:  # ORDER
        order = queries.get_order(payment["order_id"])
        queries.mark_order_paid(order["id"], receipt)
        queries.deduct_ready_stock(order["qty_kg"])
        send_sms(phone, f"Order confirmed. {order['qty_kg']:g}kg compost. Receipt {receipt}.")
    return {"payment_id": payment_id, "status": "PAID", "receipt": receipt}
