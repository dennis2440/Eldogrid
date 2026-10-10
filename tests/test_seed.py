import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def temporary_database(tmp_path):
    """Create an isolated SQLite database for seed tests."""
    db_path = tmp_path / "test_eldogrid.db"

    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    return db_path, env


def run_seed(env):
    """Run the seed module in a separate Python process."""
    return subprocess.run(
        [sys.executable, "-m", "app.db.seed"],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def query_database(db_path, sql, parameters=()):
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in connection.execute(sql, parameters).fetchall()
        ]


def test_seed_runs_successfully_twice(temporary_database):
    db_path, env = temporary_database

    first = run_seed(env)
    assert first.returncode == 0, first.stdout + first.stderr
    assert "Seeded demo data successfully." in first.stdout

    first_markers = query_database(
        db_path,
        "SELECT estate, lat, lon, organic_pct, est_kg "
        "FROM waste_reports ORDER BY estate",
    )

    second = run_seed(env)
    assert second.returncode == 0, second.stdout + second.stderr
    assert "Seeded demo data successfully." in second.stdout

    second_markers = query_database(
        db_path,
        "SELECT estate, lat, lon, organic_pct, est_kg "
        "FROM waste_reports ORDER BY estate",
    )

    assert second_markers == first_markers
    assert len(second_markers) == 4


def test_seed_creates_expected_farmers_and_wallets(temporary_database):
    db_path, env = temporary_database

    result = run_seed(env)
    assert result.returncode == 0, result.stdout + result.stderr

    farmers = query_database(
        db_path,
        "SELECT phone, name FROM farmers ORDER BY phone",
    )
    wallets = query_database(
        db_path,
        "SELECT phone, balance_kes FROM wallets ORDER BY phone",
    )

    assert len(farmers) == 3
    assert len(wallets) == 3
    assert {wallet["phone"] for wallet in wallets} == {
        farmer["phone"] for farmer in farmers
    }
    assert all(wallet["balance_kes"] == 500 for wallet in wallets)


def test_seed_resets_inventory_to_demo_quantities(temporary_database):
    db_path, env = temporary_database

    result = run_seed(env)
    assert result.returncode == 0, result.stdout + result.stderr

    inventory = query_database(
        db_path,
        "SELECT ready_kg, pipeline_kg FROM inventory WHERE id = 1",
    )

    assert inventory == [{"ready_kg": 120.0, "pipeline_kg": 670.0}]


def test_seeded_markers_match_fixture_estates(temporary_database):
    db_path, env = temporary_database

    result = run_seed(env)
    assert result.returncode == 0, result.stdout + result.stderr

    seeded_estates = query_database(
        db_path,
        "SELECT estate FROM waste_reports ORDER BY estate",
    )

    expected_estates = sorted(
        ["Main Market", "Langas", "Huruma", "Pioneer"]
    )

    assert [row["estate"] for row in seeded_estates] == expected_estates
