"""M3: climate risk + alerts."""
from fastapi import APIRouter

from app import fixtures
from app.services.risk_model import get_risk

router = APIRouter(prefix="/climate", tags=["climate"])


@router.get("/risk")
def risk():
    return get_risk()


@router.post("/alert/trigger")
def trigger_alert():
    # TODO(M3+M4): compute risk, store in climate_alerts, send SMS via sms_client
    return fixtures.ALERT


@router.get("/alerts")
def alerts():
    return [fixtures.ALERT]
