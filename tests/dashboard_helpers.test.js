// Tests for the pure helper functions in static/app.js.  Run:  node tests/dashboard_helpers.test.js
const assert = require("assert");
const h = require("../static/app.js");
let n = 0;
const ok = (label, fn) => { fn(); n++; console.log("  ok  ", label); };

ok("escapeHtml blocks tags", () => assert.strictEqual(h.escapeHtml('<b onclick="x">&'), "&lt;b onclick=&quot;x&quot;&gt;&amp;"));
ok("escapeHtml handles null", () => assert.strictEqual(h.escapeHtml(null), ""));
ok("colour: 80% organic is green", () => assert.strictEqual(h.organicColor(80), "#16a34a"));
ok("colour: 55% is amber", () => assert.strictEqual(h.organicColor(55), "#f59e0b"));
ok("colour: 20% is red", () => assert.strictEqual(h.organicColor(20), "#dc2626"));
ok("UTC time shown as Kenya time (+3h)", () => assert.match(h.formatTime("2026-10-05T08:30:00"), /11:30/));
ok("bad time gives empty string", () => assert.strictEqual(h.formatTime("not a date"), ""));
ok("radius has a minimum", () => assert.strictEqual(h.markerRadius(0), 8));
ok("radius has a maximum", () => assert.strictEqual(h.markerRadius(1e9), 28));
ok("aggregate sums per estate", () => {
  const a = h.aggregateByEstate([
    { estate: "Langas", est_kg: 200, organic_pct: 60 },
    { estate: "Langas", est_kg: 100, organic_pct: 100 },
    { estate: "Huruma", est_kg: 100, organic_pct: 0 },
  ]);
  assert.deepStrictEqual(a.labels, ["Langas", "Huruma"]);
  assert.deepStrictEqual(a.organic, [220, 0]);
  assert.deepStrictEqual(a.inorganic, [80, 100]);
});
ok("empty alerts -> null", () => assert.strictEqual(h.latestActiveAlert([]), null));
ok("fresh alert is active", () => {
  const now = Date.parse("2026-10-05T12:00:00Z");
  assert.ok(h.latestActiveAlert([{ created_at: "2026-10-05T11:00:00" }], now));
});
ok("alert older than 24h is hidden", () => {
  const now = Date.parse("2026-10-07T12:00:00Z");
  assert.strictEqual(h.latestActiveAlert([{ created_at: "2026-10-05T11:00:00" }], now), null);
});
console.log(`\nall ${n} checks passed`);
