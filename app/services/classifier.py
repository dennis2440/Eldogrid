"""M3: waste image classification.

Sprint 1: canned FIXTURE (demo data).
Sprint 2: real Roboflow model, with the fixture kept as the safety net.

Flow:

    classify_image()
        |
        +-- DEMO_MODE=True  --------------------> fixture
        |
        +-- DEMO_MODE=False --> Roboflow
                                  |
                                  +-- success --> mapped result
                                  +-- ANY error -> fixture

Return shape comes from docs/api_contract.md:
    organic_pct, inorganic_pct, labels, source
"""

import io
import logging

from PIL import Image
from inference_sdk import InferenceConfiguration, InferenceHTTPClient

from app.config import (
    DEMO_MODE,
    ROBOFLOW_API_KEY,
    ROBOFLOW_API_URL,
    ROBOFLOW_MODEL_ID,
)

log = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 10

_FIXTURE_ORGANIC_PCT = 72
_FIXTURE_LABELS = ["vegetable_waste", "plastic_bag", "cardboard"]

# Roboflow class name -> (our label, our category)
_CLASS_MAP = {
    "dry leave (organic)": ("dry_leaf", "organic"),
    "fruit waste (organic)": ("fruit_waste", "organic"),
    "glass (inorganic)": ("glass", "inorganic"),
    "paper (inorganic)": ("paper", "inorganic"),
    "plastic bag (inorganic)": ("plastic_bag", "inorganic"),
    "plastic bottle (inorganic)": ("plastic_bottle", "inorganic"),
    "tin (inorganic)": ("tin", "inorganic"),
    "battery (b3)": ("battery", "inorganic"),
    "bugs spray (b3)": ("bugs_spray", "inorganic"),
}


def get_fixture_classification() -> dict:
    """Return the fixed demo classification used when real inference is unavailable."""
    return {
        "organic_pct": _FIXTURE_ORGANIC_PCT,
        "inorganic_pct": 100 - _FIXTURE_ORGANIC_PCT,
        "labels": list(_FIXTURE_LABELS),
        "source": "demo",
    }


def _call_roboflow(image_bytes: bytes) -> dict:
    """Send image bytes to the configured Roboflow model."""
    if not ROBOFLOW_API_KEY:
        raise ValueError("ROBOFLOW_API_KEY is not set in .env")

    if not ROBOFLOW_MODEL_ID:
        raise ValueError("ROBOFLOW_MODEL_ID is not set in .env")

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    configuration = InferenceConfiguration(
        api_key_transport="header",
    )

    client = InferenceHTTPClient(
        api_url=ROBOFLOW_API_URL,
        api_key=ROBOFLOW_API_KEY,
    )

    client.configure(configuration)


    result = client.infer(
        image,
        model_id=ROBOFLOW_MODEL_ID,
    )

    print("DEBUG: Raw Roboflow response:", result)

    return result


def _summarise_predictions(result: dict) -> dict:
    """Convert Roboflow detections into the API contract."""
    predictions = result["predictions"]

    if not isinstance(predictions, list):
        raise ValueError("'predictions' is not a list")

    area_by_category = {
        "organic": 0.0,
        "inorganic": 0.0,
    }

    area_by_label: dict[str, float] = {}

    for box in predictions:
        class_name = str(box["class"]).strip().lower()

        mapped = _CLASS_MAP.get(class_name)

        if mapped is None:
            log.info("Ignoring unmapped class: %r", box["class"])
            continue

        label, category = mapped

        area = float(box["width"]) * float(box["height"])

        area_by_category[category] += area
        area_by_label[label] = area_by_label.get(label, 0.0) + area

    total_area = sum(area_by_category.values())

    if total_area <= 0:
        raise ValueError("no usable detections in the Roboflow answer")

    organic_pct = round(
        100 * area_by_category["organic"] / total_area
    )

    labels = sorted(
        area_by_label,
        key=area_by_label.get,
        reverse=True,
    )

    return {
        "organic_pct": organic_pct,
        "inorganic_pct": 100 - organic_pct,
        "labels": labels,
        "source": "roboflow",
    }


def classify_image(image_bytes: bytes) -> dict:
    """Classify a waste image with Roboflow or fall back to the fixture."""
    if DEMO_MODE:
        return get_fixture_classification()

    try:
        result = _call_roboflow(image_bytes)
        return _summarise_predictions(result)

    except Exception as exc:
        log.warning(
            "Roboflow failed (%s: %s); using fixture",
            type(exc).__name__,
            exc,
        )
        return get_fixture_classification()