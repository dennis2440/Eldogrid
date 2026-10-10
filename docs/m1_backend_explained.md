# M1 backend: what each piece does (for learning)

## The big idea: layers
```
Browser / phone / Africa's Talking
        |
   routes/        receive HTTP requests, check input, return JSON      (dashboard.py, admin.py ...)
        |
   services/      business rules: "what does this mean?"              (inventory.py, estates.py ...)
        |
   db/queries.py  the ONLY place SQL is written                        (INSERT / SELECT / UPDATE)
        |
   SQLite file    eldogrid.db
```
Why bother? If M1 ever swaps SQLite for Firebase, only `queries.py` changes. Routes and services never notice. It also means a bug in money handling has exactly one place to look.

## Files
**`app/db/database.py`**: `get_conn()` opens the database. Three details worth knowing:
- `timeout=10` waits instead of crashing if two writers collide (our payment timer runs in its own thread, so this really can happen).
- `row_factory = sqlite3.Row` lets us read columns by name.
- `journal_mode=WAL` lets reads continue while a write happens.
`init_db()` runs `schema.sql`; every table uses `CREATE TABLE IF NOT EXISTS`, so running it at every startup is safe.

**`app/db/queries.py`**: every database action as a named function.
- Helpers `_one`, `_all`, `_exec` open a connection, run one query, and always close it (the `finally` block).
- `?` placeholders keep user input out of the SQL text. This prevents SQL injection, a classic attack where text like `'; DROP TABLE` becomes a command.
- `upsert_farmer` uses `INSERT ... ON CONFLICT DO UPDATE` ("insert, or update if it exists") and `COALESCE(new, old)` ("use the new value unless it's NULL"). That is why changing language doesn't erase the crop.
- `debit_wallet` is a single `UPDATE ... WHERE balance >= amount`. The check and the subtraction are one step, so two simultaneous orders can't spend the same money. It returns True only if one row changed.
- `deduct_ready_stock` uses `MAX(x, 0)` so stock can't go negative.
- `move_pipeline_to_ready` moves compost from "curing" to "sellable". All the expressions in one UPDATE read the OLD values, which is why both columns can be updated safely in one statement.
- `get_stats` builds the dashboard cards using `SUM`, `COUNT` and `COALESCE(...,0)` (so an empty table gives 0, not NULL).
- Times: SQLite stores UTC as `2026-10-05 08:30:00`. `REPLACE(created_at,' ','T')` makes it ISO. The dashboard adds 3 hours for Kenya.

**`app/services/inventory.py`**: the compost rules. Organic waste x 0.4 goes to the pipeline (assumption: say so on stage). Only READY compost can be ordered.

**`app/services/estates.py`**: estate name -> coordinates, so a waste report only needs "Langas" to get a map pin. Coordinates are approximate; verify them.

**`app/routes/dashboard.py`**: `/dashboard/markers`, `/stats`, `/alerts`, `/estates`. Each is one line because the work lives in `queries.py`.

**`app/routes/admin.py`**: `/admin/mark-ready` (pretend curing finished) and `/admin/reset` (clean demo state). Not password-protected. A judge may ask: answer "prototype only; production needs authentication."

**`app/main.py`**: now also registers the admin router.

## How to test
```bash
python tests/test_queries.py        # 29 checks on a throw-away database
python -m app.db.seed
uvicorn app.main:app --reload
curl localhost:8000/dashboard/stats
curl -X POST localhost:8000/admin/mark-ready -H "Content-Type: application/json" -d '{"kg":100}'
curl -X POST localhost:8000/admin/reset
```

## Things to watch
- `seed.py` clears rows with DELETE, so ids keep counting up after a reset (harmless).
- `reset` while a payment timer is pending is safe: the timer finds nothing and stops.
- If M3 saves waste reports, they must call `estates.coords_for(estate)` for lat/lon and `inventory.add_organic_waste(...)` for the pipeline.
