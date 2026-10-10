"""M4: every USSD screen in one place. CON = keep session open, END = close it.
Swahili strings: have a Swahili speaker on the team check them before the demo."""

TEXT = {
    "en": {
        "menu": "CON Welcome to EldoGrid\n1. Farm advice\n2. Order compost\n3. Top up wallet\n4. Check balance\n5. Language",
        "crop": "CON Select your crop:\n1. Maize\n2. Wheat",
        "soil": "CON Select your soil:\n1. Loam\n2. Clay\n3. Sandy",
        "qty": "CON Compost KES {price}/kg. In stock: {stock}kg.\nEnter kg ({min}-{max}):",
        "pay_menu": "CON {qty}kg = KES {amount}\n1. Pay from wallet (KES {bal})\n2. Pay via M-Pesa",
        "order_ok": "END Order confirmed: {qty}kg compost, KES {amount}. Receipt {receipt}. SMS sent.",
        "mpesa_sent": "END M-Pesa prompt sent for KES {amount}. Enter your PIN to complete.",
        "wallet_low": "END Wallet too low (KES {bal}). Top up or pay via M-Pesa.",
        "out_of_stock": "END Sorry, compost is out of stock. Try again soon.",
        "bad_qty": "END Enter a whole number between {min} and {max} kg. Dial again.",
        "topup_prompt": "CON Enter top-up amount (KES {min}-{max}):",
        "bad_amount": "END Enter a whole number between {min} and {max}. Dial again.",
        "balance": "END Wallet balance: KES {bal}",
        "lang_menu": "CON Choose language:\n1. English\n2. Kiswahili",
        "lang_set": "END Language set to English.",
        "invalid": "END Invalid choice. Please dial again.",
        "error": "END Sorry, please try again.",
    },
    "sw": {
        "menu": "CON Karibu EldoGrid\n1. Ushauri wa shamba\n2. Agiza mboji\n3. Weka pesa\n4. Angalia salio\n5. Lugha",
        "crop": "CON Chagua zao:\n1. Mahindi\n2. Ngano",
        "soil": "CON Chagua udongo:\n1. Tifutifu\n2. Mfinyanzi\n3. Mchanga",
        "qty": "CON Mboji KES {price}/kg. Iliyopo: {stock}kg.\nWeka kg ({min}-{max}):",
        "pay_menu": "CON {qty}kg = KES {amount}\n1. Lipa kwa wallet (KES {bal})\n2. Lipa kwa M-Pesa",
        "order_ok": "END Oda imekubaliwa: mboji {qty}kg, KES {amount}. Risiti {receipt}. SMS imetumwa.",
        "mpesa_sent": "END Ombi la M-Pesa limetumwa kwa KES {amount}. Weka PIN kukamilisha.",
        "wallet_low": "END Salio halitoshi (KES {bal}). Weka pesa au lipa kwa M-Pesa.",
        "out_of_stock": "END Samahani, mboji imeisha. Jaribu tena baadaye.",
        "bad_qty": "END Weka nambari kamili kati ya {min} na {max} kg. Piga tena.",
        "topup_prompt": "CON Weka kiasi cha kuweka (KES {min}-{max}):",
        "bad_amount": "END Weka nambari kamili kati ya {min} na {max}. Piga tena.",
        "balance": "END Salio la wallet: KES {bal}",
        "lang_menu": "CON Chagua lugha:\n1. English\n2. Kiswahili",
        "lang_set": "END Lugha imewekwa Kiswahili.",
        "invalid": "END Chaguo si sahihi. Tafadhali piga tena.",
        "error": "END Samahani, tafadhali jaribu tena.",
    },
}


def t(lang: str, key: str, **kw) -> str:
    """Look up a screen; falls back to English."""
    return TEXT.get(lang, TEXT["en"])[key].format(**kw)
