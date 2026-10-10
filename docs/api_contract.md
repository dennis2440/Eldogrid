# EldoGrid AI: API Contract (v1)

This is the single source of truth for request and response shapes. Frontend, telephony and AI code are built against it, so **do not change a field without telling the team**. The scaffold's stub endpoints already return these shapes.

## Conventions

- Base URL: `http://localhost:8000` locally, `PUBLIC_BASE_URL` when deployed.
- JSON in, JSON out, except `/ussd` (form in, plain text out).
- Phones are stored as `2547XXXXXXXX` (no `+`).
- Timestamps are ISO 8601 strings in **UTC**: `2026-10-05T08:30:00`. Kenya is UTC+3, so the dashboard should add 3 hours when displaying times.
- Errors: HTTP 4xx/5xx with `{"error": "short message"}`.
- Money is in KES as numbers (`450`, not `"KES 450"`).
- `DEMO_MODE=true` means every external call (Roboflow, Open-Meteo, Africa's Talking) returns canned data instead.

## Enums

| Field | Values |
|---|---|
| `orders.status` | `PENDING_PAYMENT`, `PAID`, `CANCELLED` |
| `payments.status` | `PENDING`, `PAID`, `FAILED` |
| `payments.kind` | `ORDER`, `TOPUP` |
| `risk_level` / `alert.level` | `LOW`, `MEDIUM`, `HIGH` |
| `language` | `en`, `sw` |

## 1. Waste (owner: M3)

### `POST /waste/upload`
Multipart form: `image` (file), `estate` (text), `est_kg` (number, collector's estimate of the heap weight).

Response `200`:
```json
{
  "report_id": 1,
  "estate": "Main Market",
  "est_kg": 420,
  "organic_pct": 72,
  "inorganic_pct": 28,
  "labels": ["vegetable_waste", "plastic_bag", "cardboard"],
  "source": "roboflow"
}
```
`source` is `roboflow` or `demo`. Side effects: a `waste_reports` row is saved, and organic kg × 0.4 is added to the compost **pipeline** inventory.

### `GET /waste/reports`
Response `200`: array of markers (same shape as `/dashboard/markers`).

## 2. Dashboard (owner: M1, consumed by M2)

### `GET /dashboard/markers`
```json
[
  {"id": 1, "estate": "Main Market", "lat": 0.5167, "lon": 35.2833,
   "organic_pct": 78, "est_kg": 420, "created_at": "2026-10-05T08:30:00"}
]
```

### `GET /dashboard/stats`
```json
{
  "total_waste_kg": 1170,
  "organic_kg": 790,
  "compost_ready_kg": 120,
  "compost_pipeline_kg": 670,
  "orders_paid": 14,
  "orders_pending": 2,
  "active_alerts": 1
}
```
`compost_ready_kg` is what can be ordered now. `compost_pipeline_kg` is still curing.

### `GET /dashboard/estates`
For the upload form's estate dropdown.
```json
[{"name": "Langas", "lat": 0.5, "lon": 35.29}]
```

### `GET /dashboard/alerts`
Array of alerts (same shape as the alert object in section 3).

## 3. Climate (owner: M3)

### `GET /climate/risk`
```json
{
  "risk_level": "HIGH",
  "risk_score": 0.82,
  "rain_mm_24h": 63.0,
  "rain_mm_next_48h": 88.0,
  "source": "open-meteo"
}
```
`risk_score` is a 0 to 1 index, not a calibrated flood probability. Do not describe it as one on stage.

### `POST /climate/alert/trigger`
Admin/demo endpoint: computes risk, stores an alert, sends SMS to officers and registered farmers.
```json
{
  "alert_id": 1,
  "level": "HIGH",
  "message": "Heavy rain expected in Uasin Gishu within 24h. Clear drains. Delay fertilizer top-dressing.",
  "sms_sent": 12,
  "created_at": "2026-10-05T11:00:00"
}
```

### `GET /climate/alerts`
Array of alert objects as above, newest first.

## 4. USSD (owner: M4)

### `POST /ussd`
Form fields from Africa's Talking: `sessionId`, `serviceCode`, `phoneNumber`, `text`.
Response: `text/plain`, always starting with `CON ` (continue) or `END ` (finish). Keep each screen under about 160 characters.

`text` is the accumulated choices joined with `*`. Examples:

| `text` | Meaning |
|---|---|
| `` (empty) | Show main menu |
| `1` | Farm advice (asks crop and soil only the first time) |
| `1*1*2` | First-time advice: crop option 1 (maize), soil option 2 (clay) |
| `2` | Order compost: asks for kg |
| `2*50` | 50 kg chosen: asks payment method |
| `2*50*1` | Pay from wallet |
| `2*50*2` | Pay via M-Pesa (mock) |
| `3*500` | Top up wallet with KES 500 |
| `4` | Check balance |
| `5*2` | Switch language to Kiswahili (`5*1` = English) |

Main menu:
```
CON Welcome to EldoGrid
1. Farm advice
2. Order compost
3. Top up wallet
4. Check balance
5. Language
```
Farm advice must include the rain check: if `rain_mm_next_48h >= 50`, add "Heavy rain in 48h: delay top-dressing."

## 5. SMS (owner: M4)

### `GET /sms/outbox`
Last 20 messages sent. Powers the "fake phone" panel on the dashboard. `sent_at` is UTC like every other timestamp.
```json
[{"to": "254700000001", "message": "Order confirmed. Receipt QWE1R2T3Y4", "sent_at": "2026-10-05T11:02:10", "mode": "demo"}]
```

### `POST /sms/incoming`
Form fields from Africa's Talking: `from`, `text`. Keyword `PAY` confirms the farmer's latest pending payment.

SMS templates (keep under 160 characters):
- Payment prompt: `Pay KES {amount} for {qty}kg compost. Enter M-Pesa PIN.`
- Confirmation: `Order confirmed. {qty}kg compost. Receipt {receipt}.`
- Flood alert: `EldoGrid ALERT: heavy rain expected within 24h. Clear drains. Delay fertilizer top-dressing.`

## 6. Payments: mock M-Pesa (owner: M4)

A simulated layer shaped like Daraja, so a real integration can replace one file later.

### `POST /payments/initiate`
Request:
```json
{"phone": "254700000001", "kind": "ORDER", "amount_kes": 450, "order_id": 7}
```
`kind` is `TOPUP` for wallet top-ups (no `order_id`).

Response:
```json
{"payment_id": 1, "status": "PENDING", "message": "STK push simulated"}
```

### `POST /mock/mpesa/callback`
Called by the dashboard "Simulate M-Pesa payment" button, the `PAY` SMS keyword, or the auto-confirm timer.
Request:
```json
{"payment_id": 1, "ResultCode": 0, "MpesaReceiptNumber": "QWE1R2T3Y4", "Amount": 450, "PhoneNumber": "254700000001"}
```
Response:
```json
{"payment_id": 1, "status": "PAID", "receipt": "QWE1R2T3Y4"}
```
Side effects: order becomes `PAID` or the wallet is credited, and a confirmation SMS is sent.

## 7. Demo controls (owner: M2 + M5)

Hidden panel on the dashboard (toggle with a key such as `D`), with buttons:

- **Simulate rain** calls `POST /climate/alert/trigger`
- **Simulate M-Pesa payment** calls `POST /mock/mpesa/callback` for the latest pending payment
- **Reset demo data** calls `POST /admin/reset`
- **Mark compost ready** calls `POST /admin/mark-ready` with `{"kg": 100}`

## 8. Admin / demo controls (owner: M1)

Not secured (prototype only).

### `POST /admin/mark-ready`
Pretend curing finished. Request: `{"kg": 100}`. Response:
```json
{"moved_kg": 100, "ready_kg": 220.0, "pipeline_kg": 570.0}
```
`moved_kg` can be less than requested if the pipeline holds less. Invalid input returns `400 {"error": "..."}`.

### `POST /admin/reset`
Re-seeds the database and clears the SMS outbox. Response: `{"status": "reset"}`

## Changing this contract

1. Message the team with what changes and why.
2. Update this file in the same pull request as the code change.
3. After the hour 18 freeze, no contract changes.
