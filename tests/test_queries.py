"""Tests for M1's data layer. Run from the project root:  python tests/test_queries.py
Uses a throw-away database file, so your real eldogrid.db is never touched."""
import os
import pathlib
import sys

TMP = "test_tmp.db"
os.environ["DATABASE_URL"] = f"sqlite:///./{TMP}"          # must be set BEFORE importing app code
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
for ext in ("", "-wal", "-shm"):
    if os.path.exists(TMP + ext):
        os.remove(TMP + ext)

from app.db import queries                      # noqa: E402
from app.db.database import init_db             # noqa: E402
from app.services import estates, inventory     # noqa: E402

passed = 0


def check(label, condition):
    global passed
    assert condition, f"FAILED: {label}"
    passed += 1
    print(f"  ok   {label}")


init_db(); init_db()
check("init_db twice is safe", True)

s = queries.get_stats()
check("empty stats are all zero", s["total_waste_kg"] == 0 and s["orders_paid"] == 0 and s["compost_ready_kg"] == 0)

r1 = queries.save_waste_report("Langas", 0.5, 35.29, 60, 40, 200)
r2 = queries.save_waste_report("Huruma", 0.53, 35.28, 80, 20, 100)
rows = queries.list_waste_reports()
check("reports newest first", [r["id"] for r in rows] == [r2, r1])
check("timestamp is ISO with T", "T" in rows[0]["created_at"])
s = queries.get_stats()
check("total waste = 300", s["total_waste_kg"] == 300)
check("organic kg = 200*0.6 + 100*0.8 = 200", s["organic_kg"] == 200)

queries.upsert_farmer("254700000001", name="Wanjiku", crop="maize", soil="loam", language="en")
queries.upsert_farmer("254700000001", language="sw")
f = queries.get_farmer("254700000001")
check("upsert keeps crop when only language changes", f["crop"] == "maize" and f["language"] == "sw")
check("unknown farmer is None", queries.get_farmer("000") is None)

queries.credit_wallet("254700000001", 100)
check("credit works", queries.get_wallet_balance("254700000001") == 100)
check("overspend refused", queries.debit_wallet("254700000001", 150) is False)
check("balance unchanged after refused debit", queries.get_wallet_balance("254700000001") == 100)
check("valid debit works", queries.debit_wallet("254700000001", 40) is True)
check("balance is 60", queries.get_wallet_balance("254700000001") == 60)
check("debit unknown wallet refused", queries.debit_wallet("254799999999", 1) is False)
try:
    queries.credit_wallet("254700000001", -5)
    check("negative credit rejected", False)
except ValueError:
    check("negative credit rejected", True)

added = inventory.add_organic_waste(100)
check("100kg organic -> 40kg compost in pipeline", added == 40 and queries.get_inventory_row()["pipeline_kg"] == 40)
check("ready is still 0 (curing)", queries.get_inventory_row()["ready_kg"] == 0)
check("mark 30 ready moves 30", inventory.mark_pipeline_ready(30) == 30)
inv = queries.get_inventory_row()
check("ready 30 / pipeline 10", inv["ready_kg"] == 30 and inv["pipeline_kg"] == 10)
check("asking for more than pipeline moves only what exists", inventory.mark_pipeline_ready(50) == 10)
queries.deduct_ready_stock(1000)
check("stock never goes negative", queries.get_inventory_row()["ready_kg"] == 0)

oid = queries.create_order("254700000001", 50, 450)
pid = queries.create_payment("254700000001", "ORDER", 450, oid)
check("pending payment found", queries.get_latest_pending_payment("254700000001")["id"] == pid)
check("order counted as pending", queries.get_stats()["orders_pending"] == 1)
queries.mark_payment_paid(pid, "ABC123")
queries.mark_order_paid(oid, "ABC123")
check("no pending payment after paid", queries.get_latest_pending_payment() is None)
check("order counted as paid", queries.get_stats()["orders_paid"] == 1)

a1 = queries.save_alert("HIGH", 0.8, 63.0, "first", 5)
a2 = queries.save_alert("HIGH", 0.9, 70.0, "second", 6)
check("alerts newest first", [a["alert_id"] for a in queries.list_alerts()] == [a2, a1])
check("both alerts count as active", queries.get_stats()["active_alerts"] == 2)

check("estate lookup ignores case", estates.coords_for("langas") == estates.ESTATES["Langas"])
check("unknown estate -> city centre", estates.coords_for("Nowhere") == estates.CENTER)

for ext in ("", "-wal", "-shm"):
    if os.path.exists(TMP + ext):
        os.remove(TMP + ext)
print(f"\nall {passed} checks passed")
