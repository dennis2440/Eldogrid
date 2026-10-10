# M2 dashboard: what each piece does (for learning)

## The big idea
The page is a **client** of the API we already built. It never touches the database. Every 5 seconds JavaScript asks the server for fresh JSON and repaints only what changed.

```
index.html  (structure: boxes with ids)
style.css   (looks)
app.js      (behaviour)
   |  fetch() every 5s
   v
/dashboard/stats   /dashboard/markers   /dashboard/alerts   /sms/outbox      <- read
/waste/upload      /climate/alert/trigger   /mock/mpesa/callback   /admin/*  <- write
```

## Files
**`static/index.html`**: the skeleton. Each number, chart and list has an `id` (for example `stat-total`) so JavaScript can find it with `document.getElementById`. Libraries load from our own `static/vendor/` folder, not a CDN.

**`static/style.css`**: plain CSS with a few variables (`--green`, `--red`). A CSS **grid** makes the layout: 6 stat cards on top, then a 2:1 split (map + charts | upload form + phone). Media queries stack everything on narrow screens.

**`static/app.js`** has three layers:
1. **Pure helpers** (no page needed, so they can be tested): `escapeHtml`, `organicColor`, `formatTime`, `markerRadius`, `aggregateByEstate`, `latestActiveAlert`, `safely`.
2. **Backend talk**: `api()` wraps `fetch` and turns `{"error": "..."}` replies into normal JavaScript errors. `postJson()` sends JSON.
3. **`startDashboard()`**: builds the map and charts, defines renderers and loaders, wires up the form, demo panel and the timer.

## Ideas worth understanding
- **Redraw only on change.** Each loader turns the response into a string (`JSON.stringify`) and compares it with the last one. Same string means do nothing. That avoids flicker and wasted work.
- **`Promise.allSettled`** runs the four loaders together and waits for all, even if one fails. The status pill shows Live, "Some data unavailable" or "Offline, retrying". A failed loader never blocks the others.
- **`safely(label, fn)`** wraps map and chart drawing in try/catch. If the map breaks, the text list and stat cards still work. Judges see a slightly reduced dashboard, never a blank page.
- **`escapeHtml`** is a security habit. We put server text (estate names, SMS text) into HTML, and `<script>` in that text must not run. Always escape before inserting.
- **UTC vs Kenya time.** The backend sends UTC like `2026-10-05T08:30:00`. We append `Z` so JavaScript knows it's UTC, then format with `timeZone: "Africa/Nairobi"`.
- **Circle size and colour.** Radius grows with the square root of kg (so a heap 4x bigger is 2x wider, not 4x), clamped to 8-28 px. Green means 70%+ organic, amber 50-69%, red below 50%.
- **Stale-request guard.** The `refreshing` flag stops new requests piling up if the network is slow.
- **Upload.** `FormData` builds the multipart request the backend expects (`image`, `estate`, `est_kg`). The result card shows a "demo result" tag when `source` is `demo`, so the page never pretends a fake classification is a live AI call.
- **Demo panel (press D).** Four buttons hit the demo endpoints: simulate rain, simulate M-Pesa payment, mark 100 kg compost ready, reset. Each shows a toast and refreshes.

## Decision: no Tailwind, no CDN
The team prompt said Tailwind via CDN. I used plain CSS and vendored Leaflet and Chart.js instead, because a CDN needs the venue Wi-Fi at the exact moment you present. Now only the map's background tiles need internet (the page shows a note if they fail, and markers still draw). If you prefer Tailwind, it's a styling swap that doesn't touch `app.js`.

## Testing
```bash
node tests/dashboard_helpers.test.js     # 13 checks on the helper functions, no install needed
python -m app.db.seed && uvicorn app.main:app --reload
# open http://localhost:8000 and check the list in the main reply
```

## Where the backend still limits the page
- `/waste/upload` is M3's stub: it returns a fixed result and doesn't save a report, so uploading shows a result but no new pin yet.
- `/climate/alert/trigger` is also a stub, so the alert banner only turns red once M3 saves an alert.
