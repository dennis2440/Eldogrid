"""M4: make every phone number look the same: 2547XXXXXXXX (no '+')."""
import re


def normalize_phone(raw: str) -> str:
    p = re.sub(r"\D", "", raw or "")          # keep digits only
    if len(p) == 10 and p.startswith("0"):     # 0712345678 -> 254712345678
        p = "254" + p[1:]
    elif len(p) == 9 and p[0] in "71":         # 712345678  -> 254712345678
        p = "254" + p
    return p
