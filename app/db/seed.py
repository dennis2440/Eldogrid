"""Seed demo data (M5). Run:  python -m app.db.seed
Estate coordinates are APPROXIMATE - verify on Google Maps before the demo."""
from app import fixtures
from app.db.database import get_conn, init_db


def main():
    init_db()
    conn = get_conn()
    c = conn.cursor()
    for t in ("waste_reports", "farmers", "wallets", "orders", "payments", "climate_alerts"):
        c.execute(f"DELETE FROM {t}")

    for m in fixtures.MARKERS:
        c.execute(
            "INSERT INTO waste_reports (estate, lat, lon, organic_pct, inorganic_pct, est_kg, created_at) VALUES (?,?,?,?,?,?,?)",
            (m["estate"], m["lat"], m["lon"], m["organic_pct"], 100 - m["organic_pct"], m["est_kg"], m["created_at"]),
        )

    farmers = [
        ("254700000001", "Demo Farmer 1", "maize", "loam", "en"),
        ("254700000002", "Demo Farmer 2", "wheat", "clay", "sw"),
        ("254700000003", "Demo Farmer 3", "maize", "sandy", "en"),
    ]
    for f in farmers:
        c.execute("INSERT INTO farmers (phone, name, crop, soil, language) VALUES (?,?,?,?,?)", f)
        c.execute("INSERT INTO wallets (phone, balance_kes) VALUES (?, ?)", (f[0], 500))

    c.execute("UPDATE inventory SET ready_kg = 120, pipeline_kg = 670 WHERE id = 1")
    conn.commit()
    conn.close()
    print("Seeded demo data.")


if __name__ == "__main__":
    main()
