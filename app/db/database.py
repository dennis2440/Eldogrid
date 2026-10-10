"""SQLite helpers (M1). One short-lived connection per call keeps things simple and safe."""
import pathlib
import sqlite3

from app.config import DATABASE_PATH

SCHEMA = pathlib.Path(__file__).with_name("schema.sql")


def get_conn():
    # timeout=10: if another request is writing, wait up to 10s instead of failing with "database is locked".
    # (Our mock-payment timer runs in a separate thread, so two writers CAN collide.)
    conn = sqlite3.connect(DATABASE_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row          # rows behave like dicts: row["balance_kes"]
    conn.execute("PRAGMA journal_mode=WAL")  # readers don't block the writer
    return conn


def init_db():
    """Create tables if missing. Safe to run every startup (schema uses IF NOT EXISTS)."""
    conn = get_conn()
    conn.executescript(SCHEMA.read_text())
    conn.commit()
    conn.close()
