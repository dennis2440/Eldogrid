"""M4: USSD callback from Africa's Talking.

USSD is STATELESS: every request carries the whole history in `text`, joined by '*'.
   text = ""      -> user just dialled      -> show main menu
   text = "2"     -> chose 'Order compost'  -> ask for kg
   text = "2*50"  -> typed 50               -> ask payment method
   text = "2*50*1"-> chose wallet           -> place the order
So we rebuild "where is the user?" from len(steps) each time.
Responses are plain text starting with CON (continue) or END (finish)."""
from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse

from app.db import queries
from app.services import advice, inventory, payment_service, risk_model
from app.services.phone import normalize_phone
from app.services.ussd_text import t

router = APIRouter(tags=["ussd"])

PRICE_PER_KG_KES = 9          # ASSUMPTION: placeholder price, agree a real one with the team
MIN_KG, MAX_KG = 10, 200
MIN_TOPUP, MAX_TOPUP = 50, 5000
CROPS = {"1": "maize", "2": "wheat"}
SOILS = {"1": "loam", "2": "clay", "3": "sandy"}


def _advice_screen(crop: str, soil: str) -> str:
    rain = risk_model.get_risk().get("rain_mm_next_48h", 0)   # rain-aware advice (M3's functions)
    return ("END " + advice.get_advice(crop, soil, rain))[:160]  # USSD screens are short


def _advice_flow(phone, lang, farmer, steps):
    known = farmer and farmer.get("crop") and farmer.get("soil")
    if known:
        return _advice_screen(farmer["crop"], farmer["soil"]) if len(steps) == 1 else t(lang, "invalid")
    if len(steps) == 1:
        return t(lang, "crop")
    crop = CROPS.get(steps[1])
    if not crop:
        return t(lang, "invalid")
    if len(steps) == 2:
        return t(lang, "soil")
    soil = SOILS.get(steps[2])
    if not soil or len(steps) > 3:
        return t(lang, "invalid")
    queries.upsert_farmer(phone, crop=crop, soil=soil, language=lang)   # remember for next time
    return _advice_screen(crop, soil)


def _order_flow(phone, lang, steps):
    stock = int(inventory.get_inventory()["ready_kg"])
    if stock < MIN_KG:
        return t(lang, "out_of_stock")
    max_kg = min(MAX_KG, stock)
    if len(steps) == 1:
        return t(lang, "qty", price=PRICE_PER_KG_KES, stock=stock, min=MIN_KG, max=max_kg)
    if not steps[1].isdigit() or not (MIN_KG <= int(steps[1]) <= max_kg):
        return t(lang, "bad_qty", min=MIN_KG, max=max_kg)
    qty = int(steps[1])
    amount = qty * PRICE_PER_KG_KES
    bal = queries.get_wallet_balance(phone)
    if len(steps) == 2:
        return t(lang, "pay_menu", qty=qty, amount=amount, bal=f"{bal:g}")
    if len(steps) > 3 or steps[2] not in ("1", "2"):
        return t(lang, "invalid")
    if steps[2] == "1":                                   # pay from wallet
        if bal < amount:
            return t(lang, "wallet_low", bal=f"{bal:g}")
        receipt = payment_service.pay_order_from_wallet(phone, qty, amount)
        if receipt is None:
            return t(lang, "wallet_low", bal=f"{bal:g}")
        return t(lang, "order_ok", qty=qty, amount=amount, receipt=receipt)
    payment_service.start_order_mpesa(phone, qty, amount)  # pay via (mock) M-Pesa
    return t(lang, "mpesa_sent", amount=amount)


def _topup_flow(phone, lang, steps):
    if len(steps) == 1:
        return t(lang, "topup_prompt", min=MIN_TOPUP, max=MAX_TOPUP)
    if len(steps) > 2 or not steps[1].isdigit() or not (MIN_TOPUP <= int(steps[1]) <= MAX_TOPUP):
        return t(lang, "bad_amount", min=MIN_TOPUP, max=MAX_TOPUP)
    amount = int(steps[1])
    payment_service.initiate_payment(phone, "TOPUP", amount)
    return t(lang, "mpesa_sent", amount=amount)


def _language_flow(phone, lang, steps):
    if len(steps) == 1:
        return t(lang, "lang_menu")
    new = {"1": "en", "2": "sw"}.get(steps[1])
    if not new or len(steps) > 2:
        return t(lang, "invalid")
    queries.upsert_farmer(phone, language=new)
    return t(new, "lang_set")


def handle(phone: str, steps: list[str]) -> str:
    farmer = queries.get_farmer(phone)
    lang = (farmer or {}).get("language") or "en"
    if not steps:
        return t(lang, "menu")
    choice = steps[0]
    if choice == "1":
        return _advice_flow(phone, lang, farmer, steps)
    if choice == "2":
        return _order_flow(phone, lang, steps)
    if choice == "3":
        return _topup_flow(phone, lang, steps)
    if choice == "4":
        return t(lang, "balance", bal=f"{queries.get_wallet_balance(phone):g}")
    if choice == "5":
        return _language_flow(phone, lang, steps)
    return t(lang, "invalid")


@router.post("/ussd", response_class=PlainTextResponse)
def ussd(
    sessionId: str = Form(""),
    serviceCode: str = Form(""),
    phoneNumber: str = Form(""),
    text: str = Form(""),
):
    try:
        steps = text.split("*") if text else []
        return handle(normalize_phone(phoneNumber), steps)
    except Exception as exc:  # noqa: BLE001  never show a stack trace to a farmer
        print(f"[ussd] error: {exc}")
        return "END Sorry, please try again."
