"""M3: flood/heavy-rain risk index (Open-Meteo forecast + 3-day antecedent rainfall)."""
from app import fixtures
from app.config import DEMO_MODE


def get_risk() -> dict:
    if DEMO_MODE:
        return dict(fixtures.RISK)
    # TODO(M3): fetch forecast from Open-Meteo, compute risk_score and level
    return dict(fixtures.RISK)
