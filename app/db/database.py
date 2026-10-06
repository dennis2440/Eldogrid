"""SQLite helpers (M1)."""
import pathlib
import sqlite3

from app.config import DATABASE_PATH

SCHEMA = pathlib.Path(__file__).with_name("schema.sql")


def get_conn():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA.read_text())
    conn.commit()
    conn.close()
