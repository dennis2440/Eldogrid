"""Canned data matching docs/api_contract.md (M5 owns). Used in DEMO_MODE and as mock responses."""

MARKERS = [
    {"id": 1, "estate": "Main Market", "lat": 0.5195, "lon": 35.2745, "organic_pct": 78, "est_kg": 420, "created_at": "2026-10-05T08:30:00"},
    {"id": 2, "estate": "Langas", "lat": 0.4890, "lon": 35.2650, "organic_pct": 64, "est_kg": 260, "created_at": "2026-10-05T09:10:00"},
    {"id": 3, "estate": "Huruma", "lat": 0.5300, "lon": 35.2550, "organic_pct": 55, "est_kg": 310, "created_at": "2026-10-05T09:45:00"},
    {"id": 4, "estate": "Pioneer", "lat": 0.5198, "lon": 35.2715, "organic_pct": 70, "est_kg": 380, "created_at": "2026-10-05T10:15:00"}
];

STATS = {
    "total_waste_kg": 1170,
    "organic_kg": 790,
    "compost_ready_kg": 120,
    "compost_pipeline_kg": 670,
    "orders_paid": 14,
    "orders_pending": 2,
    "active_alerts": 1,
}

CLASSIFICATION = {
    "organic_pct": 72,
    "inorganic_pct": 28,
    "labels": ["vegetable_waste", "plastic_bag", "cardboard"],
    "source": "demo",
}

RISK = {
    "risk_level": "HIGH",
    "risk_score": 0.82,
    "rain_mm_24h": 63.0,
    "rain_mm_next_48h": 88.0,
    "source": "demo",
}

ALERT = {
    "alert_id": 1,
    "level": "HIGH",
    "message": "Heavy rain expected in Uasin Gishu within 24h. Clear drains. Delay fertilizer top-dressing.",
    "sms_sent": 12,
    "created_at": "2026-10-05T11:00:00",
}
