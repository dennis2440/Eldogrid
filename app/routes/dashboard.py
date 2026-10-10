"""M1 dashboard JSON endpoints, integrated with M3 database records.

Markers and alerts use live database rows when available. Existing fixture
responses remain as a fallback when the relevant table has no rows.
The stats endpoint is intentionally unchanged.
"""
from fastapi import APIRouter

from app import fixtures
from app.db.database import get_conn

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/markers")
def markers():
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT id, estate, lat, lon, organic_pct, est_kg, created_at
            FROM waste_reports
            ORDER BY id DESC
            """
        ).fetchall()

        if rows:
            return [dict(row) for row in rows]

        return fixtures.MARKERS
    finally:
        conn.close()


@router.get("/stats")
def stats():
    return fixtures.STATS  # TODO(M1): compute from DB


@router.get("/alerts")
def alerts():
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT
                id AS alert_id,
                level,
                message,
                sms_sent,
                created_at
            FROM climate_alerts
            ORDER BY id DESC
            """
        ).fetchall()

        if rows:
            return [dict(row) for row in rows]

        return [fixtures.ALERT]
    finally:
        conn.close()
