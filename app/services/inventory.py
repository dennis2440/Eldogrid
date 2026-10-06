"""M1: compost inventory math. Organic waste goes to the PIPELINE; it becomes READY after curing."""
from app.db.database import get_conn

KG_COMPOST_PER_KG_ORGANIC = 0.4   # assumption - state it as an assumption on stage


def add_organic_waste(organic_kg: float) -> None:
    conn = get_conn()
    conn.execute("UPDATE inventory SET pipeline_kg = pipeline_kg + ? WHERE id = 1",
                 (organic_kg * KG_COMPOST_PER_KG_ORGANIC,))
    conn.commit()
    conn.close()


def get_inventory() -> dict:
    conn = get_conn()
    row = conn.execute("SELECT ready_kg, pipeline_kg FROM inventory WHERE id = 1").fetchone()
    conn.close()
    return dict(row)
