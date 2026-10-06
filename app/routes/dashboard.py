"""M1: JSON for the dashboard (map markers, stats, alerts)."""
from fastapi import APIRouter

from app import fixtures

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/markers")
def markers():
    return fixtures.MARKERS      # TODO(M1): read from waste_reports


@router.get("/stats")
def stats():
    return fixtures.STATS        # TODO(M1): compute from DB


@router.get("/alerts")
def alerts():
    return [fixtures.ALERT]      # TODO(M1): read from climate_alerts
