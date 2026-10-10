"""M3: fertilizer advice rules (crop, soil, rain forecast).

Agronomic rates and thresholds below are illustrative assumptions for the
hackathon demo, not verified agricultural recommendations. Confirm locally
with an agricultural extension officer before real-world use.
"""

# ASSUMPTION: These are demo compost quantities in tonnes per acre, not
# validated recommendations. Values vary by soil condition and local guidance.
COMPOST_RATE_TONNES_PER_ACRE = {
    ("maize", "loam"): 2.0,
    ("maize", "clay"): 1.5,
    ("maize", "sandy"): 2.5,
    ("wheat", "loam"): 1.5,
    ("wheat", "clay"): 1.5,
    ("wheat", "sandy"): 2.0,
}

# ASSUMPTION: 50 mm over the next 48 hours is a demo threshold for a heavy-rain
# warning; it is not a locally calibrated agronomic or flood threshold.
HEAVY_RAIN_THRESHOLD_MM_48H = 50.0


def get_advice(crop: str, soil: str, rain_mm_next_48h: float = 0) -> str:
    crop_key = crop.strip().lower()
    soil_key = soil.strip().lower()

    rate = COMPOST_RATE_TONNES_PER_ACRE.get((crop_key, soil_key))
    if rate is None:
        supported_soils = sorted(
            soil_name
            for crop_name, soil_name in COMPOST_RATE_TONNES_PER_ACRE
            if crop_name == crop_key
        )
        if not supported_soils:
            supported_crops = sorted(
                {crop_name for crop_name, _ in COMPOST_RATE_TONNES_PER_ACRE}
            )
            return (
                f"No advice rule for crop '{crop}'. Supported crops: "
                f"{', '.join(supported_crops)}."
            )
        return (
            f"No advice rule for {crop_key.title()} on {soil_key} soil. "
            f"Supported soil types: {', '.join(supported_soils)}."
        )

    advice = (
        f"{crop_key.title()} on {soil_key} soil: as a demo assumption, "
        f"apply {rate:g} tonnes of compost per acre before planting. "
        "Confirm the rate with local agricultural guidance."
    )

    if rain_mm_next_48h >= HEAVY_RAIN_THRESHOLD_MM_48H:
        advice += (
            " Heavy rain is forecast in the next 48 hours: consider delaying "
            "top-dressing to reduce runoff risk."
        )
    else:
        advice += (
            " No heavy-rain warning is triggered by the current demo threshold."
        )

    return advice
