"""M1: demo/admin controls. NOT secured (prototype): a real product would require a login here."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.db import seed
from app.services import inventory
from app.services.sms_client import OUTBOX

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/mark-ready")
def mark_ready(body: dict):
    """Pretend curing finished: move kg from pipeline to ready stock. Body: {"kg": 100}"""
    kg = body.get("kg")
    if not isinstance(kg, (int, float)) or kg <= 0:
        return JSONResponse({"error": "kg must be a positive number"}, status_code=400)
    moved = inventory.mark_pipeline_ready(kg)
    return {"moved_kg": moved, **inventory.get_inventory()}


@router.post("/reset")
def reset():
    """Back to a clean demo state: re-seed the database and clear the SMS outbox."""
    seed.main()
    OUTBOX.clear()
    return {"status": "reset"}
