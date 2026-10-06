"""M3: waste photo upload + classification."""
from fastapi import APIRouter, File, Form, UploadFile

from app import fixtures
from app.services.classifier import classify_image

router = APIRouter(prefix="/waste", tags=["waste"])


@router.post("/upload")
async def upload(image: UploadFile = File(...), estate: str = Form(...), est_kg: float = Form(...)):
    result = classify_image(await image.read())
    # TODO(M3+M1): save to waste_reports, then inventory.add_organic_waste(est_kg * organic_pct/100)
    return {"report_id": 1, "estate": estate, "est_kg": est_kg, **result}


@router.get("/reports")
def reports():
    return fixtures.MARKERS
