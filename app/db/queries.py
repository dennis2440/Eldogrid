"""ALL database reads/writes live here (M1 owns this file).
Rule for the whole team: routes and services call these functions and never write SQL themselves.
Function names/signatures are a promise to teammates; don't rename them casually.
Timestamps: SQLite stores UTC as 'YYYY-MM-DD HH:MM:SS'. We return ISO style 'YYYY-MM-DDTHH:MM:SS' (still UTC)."""
from app.db.database import get_conn

# SQL snippet: turn '2026-10-05 08:30:00' into '2026-10-05T08:30:00'
_ISO = "REPLACE(created_at, ' ', 'T') AS created_at"


# ---------------- tiny helpers (every query goes through one of these) ----------------
def _one(sql, args=()):
    conn = get_conn()
    try:
        row = conn.execute(sql, args).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _all(sql, args=()):
    conn = get_conn()
    try:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]
    finally:
        conn.close()


def _exec(sql, args=()):
    """Run a write statement; returns (lastrowid, rowcount)."""
    conn = get_conn()
    try:
        cur = conn.execute(sql, args)
        conn.commit()
        return cur.lastrowid, cur.rowcount
    finally:
        conn.close()


def _positive(amount, name="amount"):
    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError(f"{name} must be a positive number")


# ---------------- waste ----------------
def save_waste_report(estate, lat, lon, organic_pct, inorganic_pct, est_kg, image_path=None):
    rid, _ = _exec(
        "INSERT INTO waste_reports (estate, lat, lon, organic_pct, inorganic_pct, est_kg, image_path) VALUES (?,?,?,?,?,?,?)",
        (estate, lat, lon, organic_pct, inorganic_pct, est_kg, image_path),
    )
    return rid


def list_waste_reports(limit=200):
    return _all(
        f"SELECT id, estate, lat, lon, organic_pct, est_kg, {_ISO} FROM waste_reports ORDER BY id DESC LIMIT ?",
        (limit,),
    )


# ---------------- farmers & wallets ----------------
def get_farmer(phone):
    return _one("SELECT * FROM farmers WHERE phone = ?", (phone,))


def upsert_farmer(phone, name=None, crop=None, soil=None, language=None):
    """Insert or update. None means 'leave the existing value alone' (that's what COALESCE does)."""
    _exec(
        """INSERT INTO farmers (phone, name, crop, soil, language) VALUES (?,?,?,?,?)
           ON CONFLICT(phone) DO UPDATE SET
             name = COALESCE(excluded.name, name),
             crop = COALESCE(excluded.crop, crop),
             soil = COALESCE(excluded.soil, soil),
             language = COALESCE(excluded.language, language)""",
        (phone, name, crop, soil, language),
    )


def get_wallet_balance(phone):
    row = _one("SELECT balance_kes FROM wallets WHERE phone = ?", (phone,))
    return float(row["balance_kes"]) if row else 0.0


def credit_wallet(phone, amount):
    _positive(amount)
    _exec(
        """INSERT INTO wallets (phone, balance_kes) VALUES (?, ?)
           ON CONFLICT(phone) DO UPDATE SET balance_kes = balance_kes + excluded.balance_kes""",
        (phone, amount),
    )


def debit_wallet(phone, amount):
    """Returns True only if the balance was enough. The check and the subtraction happen in ONE
    statement, so two quick orders can't both spend the same money."""
    _positive(amount)
    _, n = _exec(
        "UPDATE wallets SET balance_kes = balance_kes - ? WHERE phone = ? AND balance_kes >= ?",
        (amount, phone, amount),
    )
    return n == 1


# ---------------- orders & payments ----------------
def create_order(phone, qty_kg, amount_kes):
    oid, _ = _exec("INSERT INTO orders (phone, qty_kg, amount_kes) VALUES (?,?,?)", (phone, qty_kg, amount_kes))
    return oid


def get_order(order_id):
    return _one("SELECT * FROM orders WHERE id = ?", (order_id,))


def mark_order_paid(order_id, receipt):
    _exec("UPDATE orders SET status='PAID', receipt=? WHERE id=?", (receipt, order_id))


def create_payment(phone, kind, amount_kes, order_id=None):
    pid, _ = _exec(
        "INSERT INTO payments (phone, kind, amount_kes, order_id) VALUES (?,?,?,?)",
        (phone, kind, amount_kes, order_id),
    )
    return pid


def get_payment(payment_id):
    return _one("SELECT * FROM payments WHERE id = ?", (payment_id,))


def get_latest_pending_payment(phone=None):
    if phone:
        return _one("SELECT * FROM payments WHERE status='PENDING' AND phone=? ORDER BY id DESC LIMIT 1", (phone,))
    return _one("SELECT * FROM payments WHERE status='PENDING' ORDER BY id DESC LIMIT 1")


def mark_payment_paid(payment_id, receipt):
    _exec("UPDATE payments SET status='PAID', receipt=? WHERE id=?", (receipt, payment_id))


def mark_payment_failed(payment_id):
    _exec("UPDATE payments SET status='FAILED' WHERE id=?", (payment_id,))


# ---------------- compost inventory ----------------
def get_inventory_row():
    return _one("SELECT ready_kg, pipeline_kg FROM inventory WHERE id = 1")


def add_pipeline_kg(kg):
    """New compost that is still curing."""
    _positive(kg, "kg")
    _exec("UPDATE inventory SET pipeline_kg = pipeline_kg + ? WHERE id = 1", (kg,))


def move_pipeline_to_ready(kg):
    """Curing finished: move up to `kg` from pipeline to ready. Returns how many kg actually moved."""
    _positive(kg, "kg")
    moved = min(kg, get_inventory_row()["pipeline_kg"])
    if moved > 0:
        _exec(
            "UPDATE inventory SET ready_kg = ready_kg + ?, pipeline_kg = pipeline_kg - ? WHERE id = 1",
            (moved, moved),
        )
    return moved


def deduct_ready_stock(kg):
    """A paid order takes compost off the shelf. MAX(...,0) means stock never goes negative."""
    _exec("UPDATE inventory SET ready_kg = MAX(ready_kg - ?, 0) WHERE id = 1", (kg,))


# ---------------- alerts & stats ----------------
def save_alert(level, risk_score, rain_mm_24h, message, sms_sent=0):
    aid, _ = _exec(
        "INSERT INTO climate_alerts (level, risk_score, rain_mm_24h, message, sms_sent) VALUES (?,?,?,?,?)",
        (level, risk_score, rain_mm_24h, message, sms_sent),
    )
    return aid


def list_alerts(limit=50):
    return _all(
        f"SELECT id AS alert_id, level, message, sms_sent, {_ISO} FROM climate_alerts ORDER BY id DESC LIMIT ?",
        (limit,),
    )


def get_stats():
    """One dict for the dashboard cards, in the exact shape of docs/api_contract.md."""
    waste = _one(
        "SELECT COALESCE(SUM(est_kg),0) AS total, COALESCE(SUM(est_kg*organic_pct/100.0),0) AS organic FROM waste_reports"
    )
    inv = get_inventory_row()
    paid = _one("SELECT COUNT(*) AS n FROM orders WHERE status='PAID'")["n"]
    pending = _one("SELECT COUNT(*) AS n FROM orders WHERE status='PENDING_PAYMENT'")["n"]
    alerts = _one("SELECT COUNT(*) AS n FROM climate_alerts WHERE created_at >= datetime('now','-1 day')")["n"]
    return {
        "total_waste_kg": round(waste["total"]),
        "organic_kg": round(waste["organic"]),
        "compost_ready_kg": round(inv["ready_kg"]),
        "compost_pipeline_kg": round(inv["pipeline_kg"]),
        "orders_paid": paid,
        "orders_pending": pending,
        "active_alerts": alerts,
    }
