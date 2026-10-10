"""M3: climate risk + persisted alerts."""

from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.db.database import get_conn
from app.services.risk_model import get_risk
from app.services.sms_client import send_sms

router = APIRouter(prefix="/climate", tags=["climate"])


@router.get("/risk")
def risk():
    return get_risk()


@router.post("/alert/trigger")
def trigger_alert():
    try:
        risk_data = get_risk()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not calculate climate risk: {exc}",
        ) from exc

    level = str(risk_data.get("risk_level", "UNKNOWN")).upper()
    score = float(risk_data.get("risk_score", 0.0))
    rain_24h = float(risk_data.get("rain_mm_24h", 0.0))
    message = (
        f"{level} climate risk alert for EldoGrid. "
        f"Rainfall: {rain_24h:.1f} mm in the next 24 hours. "
        "Please follow local weather and safety guidance."
    )

    conn = get_conn()
    try:
        cursor = conn.execute(
            """
            INSERT INTO climate_alerts (level, risk_score, rain_mm_24h, message, sms_sent)
            VALUES (?, ?, ?, ?, 0)
            """,
            (level, score, rain_24h, message),
        )
        alert_id = cursor.lastrowid
        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Could not save climate alert: {exc}",
        ) from exc
    finally:
        conn.close()

    # The existing SMS client is a stub for live delivery until M4 implements it.
    # Send to registered farmers; no officers table exists in the current schema.
    sms_sent = 0
    sms_client_is_demo = False
    conn = get_conn()
    try:
        farmers = conn.execute("SELECT phone FROM farmers WHERE phone IS NOT NULL").fetchall()
    finally:
        conn.close()

    for farmer in farmers:
        phone = str(farmer["phone"]).strip()
        if not phone:
            continue
        try:
            send_sms(phone, message)
            # Count only demo outbox entries as successful simulated notifications.
            # In live mode the current sms_client does not actually send SMS.
            from app.config import DEMO_MODE
            if DEMO_MODE:
                sms_sent += 1
                sms_client_is_demo = True
        except Exception as exc:
            print(f"SMS notification failed for {phone}: {exc}")

    conn = get_conn()
    try:
        conn.execute(
            "UPDATE climate_alerts SET sms_sent = ? WHERE id = ?",
            (sms_sent, alert_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, level, risk_score, rain_mm_24h, message, sms_sent, created_at "
            "FROM climate_alerts WHERE id = ?",
            (alert_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        raise HTTPException(status_code=500, detail="Saved alert could not be retrieved")

    return {
        "alert_id": row["id"],
        "level": row["level"],
        "message": row["message"],
        "sms_sent": row["sms_sent"],
        "created_at": row["created_at"],
    }


@router.get("/alerts")
def alerts():
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT id, level, risk_score, rain_mm_24h, message, sms_sent, created_at
            FROM climate_alerts
            ORDER BY id DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
