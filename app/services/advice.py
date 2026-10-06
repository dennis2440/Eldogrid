"""M3: fertilizer advice rules (crop, soil, rain forecast) - a lookup table, not magic."""


def get_advice(crop: str, soil: str, rain_mm_next_48h: float = 0) -> str:
    base = f"{crop.title()} on {soil} soil: apply compost 2 tonnes/acre before planting."  # TODO(M3): real rules
    if rain_mm_next_48h >= 50:
        base += " Heavy rain in 48h: delay top-dressing to avoid runoff."
    return base
