
"""Seed realistic, repeatable demo data.

Run from the project root:
    python -m app.db.seed

Estate coordinates in app/fixtures.py are approximate and should be
verified before the demo.
"""

from app import fixtures
from app.db.database import get_conn, init_db


def main():
    init_db()
    conn = get_conn()

    try:
        with conn:
            c = conn.cursor()

            # Clear dependent and transactional demo data first.
            for table in (
                "payments",
                "orders",
                "climate_alerts",
                "wallets",
                "farmers",
                "waste_reports",
            ):
                c.execute(f"DELETE FROM {table}")

            # Seed estate waste markers.
            for marker in fixtures.MARKERS:
                c.execute(
                    """
                    INSERT INTO waste_reports
                    (estate, lat, lon, organic_pct, inorganic_pct,
                     est_kg, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        marker["estate"],
                        marker["lat"],
                        marker["lon"],
                        marker["organic_pct"],
                        100 - marker["organic_pct"],
                        marker["est_kg"],
                        marker["created_at"],
                    ),
                )

            # Seed three farmers and their wallets.
            farmers = [
                ("254700000001", "Demo Farmer 1", "maize", "loam", "en"),
                ("254700000002", "Demo Farmer 2", "wheat", "clay", "sw"),
                ("254700000003", "Demo Farmer 3", "maize", "sandy", "en"),
            ]

            for farmer in farmers:
                phone, name, crop, soil, language = farmer

                c.execute(
                    """
                    INSERT INTO farmers (phone, name, crop, soil, language)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (phone, name, crop, soil, language),
                )

                c.execute(
                    """
                    INSERT INTO wallets (phone, balance_kes)
                    VALUES (?, ?)
                    """,
                    (phone, 500),
                )

            # Reset the existing inventory row to known demo quantities.
            c.execute(
                """
                UPDATE inventory
                SET ready_kg = ?, pipeline_kg = ?
                WHERE id = 1
                """,
                (120, 670),
            )

            if c.rowcount != 1:
                raise RuntimeError(
                    "Expected exactly one inventory row with id = 1."
                )

        print("Seeded demo data successfully.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
