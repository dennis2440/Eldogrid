"""M1: known estates and their map coordinates, so the waste route can place a pin from just a name.
Coordinates are APPROXIMATE: verify each on Google Maps before the demo."""

CENTER = (0.5143, 35.2698)  # Eldoret

ESTATES = {
    "Main Market": (0.5167, 35.2833),
    "Langas": (0.5000, 35.2900),
    "Huruma": (0.5300, 35.2800),
    "Pioneer": (0.5200, 35.3000),
}


def coords_for(estate: str) -> tuple[float, float]:
    """(lat, lon) for an estate name, ignoring upper/lower case. Unknown names fall back to the city centre."""
    wanted = (estate or "").strip().lower()
    for name, coords in ESTATES.items():
        if name.lower() == wanted:
            return coords
    return CENTER
