-- M1 owns this file. Tell the team before changing a table.

CREATE TABLE IF NOT EXISTS waste_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estate TEXT NOT NULL,
    lat REAL,
    lon REAL,
    organic_pct REAL,
    inorganic_pct REAL,
    est_kg REAL,
    image_path TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS farmers (
    phone TEXT PRIMARY KEY,
    name TEXT,
    crop TEXT,
    soil TEXT,
    language TEXT DEFAULT 'en',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wallets (
    phone TEXT PRIMARY KEY,
    balance_kes REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL,
    product TEXT DEFAULT 'compost',
    qty_kg REAL,
    amount_kes REAL,
    status TEXT DEFAULT 'PENDING_PAYMENT',   -- PENDING_PAYMENT | PAID | CANCELLED
    receipt TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL,
    kind TEXT NOT NULL,                      -- ORDER | TOPUP
    amount_kes REAL NOT NULL,
    status TEXT DEFAULT 'PENDING',           -- PENDING | PAID | FAILED
    receipt TEXT,
    order_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS climate_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT,                              -- LOW | MEDIUM | HIGH
    risk_score REAL,
    rain_mm_24h REAL,
    message TEXT,
    sms_sent INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    ready_kg REAL DEFAULT 0,
    pipeline_kg REAL DEFAULT 0
);
INSERT OR IGNORE INTO inventory (id, ready_kg, pipeline_kg) VALUES (1, 0, 0);
