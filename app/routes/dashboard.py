"""M1: JSON for the dashboard. Real data from the database, in the shapes of docs/api_contract.md."""
from fastapi import APIRouter

from app.db import queries
from app.services.estates import ESTATES

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/markers")
def markers():
    return queries.list_waste_reports()


@router.get("/stats")
def stats():
    return queries.get_stats()


@router.get("/alerts")
def alerts():
    return queries.list_alerts()


@router.get("/estates")
def estates():
    """For the upload form's estate dropdown."""
    return [{"name": n, "lat": lat, "lon": lon} for n, (lat, lon) in ESTATES.items()]
