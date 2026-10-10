"""M1: compost inventory rules (business logic). The SQL itself lives in queries.py.
Two buckets: PIPELINE (still curing, can't be sold) and READY (can be ordered). Orders only draw from READY."""
from app.db import queries

KG_COMPOST_PER_KG_ORGANIC = 0.4   # ASSUMPTION: 1 kg of organic waste gives ~0.4 kg compost. Say so on stage.


def add_organic_waste(organic_kg: float) -> float:
    """Called after a waste photo is classified. Returns the compost kg added to the pipeline."""
    compost_kg = organic_kg * KG_COMPOST_PER_KG_ORGANIC
    if compost_kg > 0:
        queries.add_pipeline_kg(compost_kg)
    return compost_kg


def mark_pipeline_ready(kg: float) -> float:
    """Admin/demo action: curing finished. Returns kg moved to READY."""
    return queries.move_pipeline_to_ready(kg)


def get_inventory() -> dict:
    return queries.get_inventory_row()
