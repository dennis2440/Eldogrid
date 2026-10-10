
"""M3: waste photo upload + classification."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.db.database import get_conn
from app.services.classifier import classify_image
from app.services.inventory import add_organic_waste

router = APIRouter(prefix="/waste", tags=["waste"])


@router.post("/upload")
async def upload(
    image: UploadFile = File(...),
    estate: str = Form(...),
    est_kg: float = Form(...),
):
    if est_kg <= 0:
        raise HTTPException(
            status_code=400,
            detail="est_kg must be greater than zero",
        )

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    result = classify_image(image_bytes)
    organic_pct = float(result["organic_pct"])
    inorganic_pct = float(result["inorganic_pct"])

    organic_kg = est_kg * organic_pct / 100

    conn = get_conn()
    try:
        cursor = conn.execute(
            """
            INSERT INTO waste_reports
                (estate, organic_pct, inorganic_pct, est_kg, image_path)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                estate,
                organic_pct,
                inorganic_pct,
                est_kg,
                image.filename,
            ),
        )

        report_id = cursor.lastrowid

        # One transaction: save the report and update compost pipeline.
        conn.execute(
            """
            UPDATE inventory
            SET pipeline_kg = pipeline_kg + ?
            WHERE id = 1
            """,
            (organic_kg * 0.4,),
        )

        conn.commit()

        return {
            "report_id": report_id,
            "estate": estate,
            "est_kg": est_kg,
            **result,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@router.get("/reports")
def reports():
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT id, estate, lat, lon, organic_pct, inorganic_pct,
                   est_kg, created_at
            FROM waste_reports
            ORDER BY id DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()