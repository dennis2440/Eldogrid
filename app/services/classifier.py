"""M3: waste image classification (Roboflow). Falls back to canned result in DEMO_MODE or on error."""
from app import fixtures
from app.config import DEMO_MODE


def classify_image(image_bytes: bytes) -> dict:
    if DEMO_MODE:
        return dict(fixtures.CLASSIFICATION)
    # TODO(M3): call Roboflow here; on any exception return the fixture so the demo never breaks
    return dict(fixtures.CLASSIFICATION)
