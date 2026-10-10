/* EldoGrid dashboard (M2). Plain JavaScript, no build step.
 *
 * How it works in one paragraph: every 5 seconds we ask the backend for fresh data
 * (/dashboard/stats, /dashboard/markers, /dashboard/alerts, /sms/outbox) and paint it on the page.
 * The upload form and the hidden demo panel POST to the backend and then refresh immediately.
 * Backend timestamps are UTC; we show them in Kenya time (UTC+3).
 */
"use strict";

const REFRESH_MS = 5000;
const ELDORET = [0.5143, 35.2698];
const DAY_MS = 24 * 60 * 60 * 1000;

/* ====================== pure helpers (no DOM, easy to test) ====================== */

/** Make text safe to put inside HTML (stops "<script>" tricks in estate names, SMS text, etc.). */
function escapeHtml(value) {
  const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  return String(value ?? "").replace(/[&<>"']/g, (c) => map[c]);
}

/** Green = good compost material, amber = mixed, red = mostly non-organic. */
function organicColor(pct) {
  const p = Number(pct) || 0;
  return p >= 70 ? "#16a34a" : p >= 50 ? "#f59e0b" : "#dc2626";
}

/** Backend sends '2026-10-05T08:30:00' meaning UTC. Add the 'Z' so JavaScript knows that. */
function parseUtc(iso) {
  if (!iso) return null;
  const hasZone = /[zZ]$|[+-]\d\d:?\d\d$/.test(iso);
  const d = new Date(hasZone ? iso : iso + "Z");
  return isNaN(d.getTime()) ? null : d;
}

function formatTime(iso) {
  const d = parseUtc(iso);
  if (!d) return "";
  return d.toLocaleString("en-KE", {
    timeZone: "Africa/Nairobi", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hour12: false,
  });
}

/** Bigger heap -> bigger circle, but kept between 8 and 28 px so nothing vanishes or covers the map. */
function markerRadius(kg) {
  return Math.max(8, Math.min(28, 8 + Math.sqrt(Number(kg) || 0) / 1.5));
}

/** Turn a list of reports into per-estate organic/inorganic kg for the bar chart. */
function aggregateByEstate(markers) {
  const totals = new Map();
  for (const m of markers) {
    const kg = Number(m.est_kg) || 0;
    const pct = Number(m.organic_pct) || 0;
    const t = totals.get(m.estate) || { organic: 0, inorganic: 0 };
    t.organic += (kg * pct) / 100;
    t.inorganic += (kg * (100 - pct)) / 100;
    totals.set(m.estate, t);
  }
  const labels = [...totals.keys()];
  return {
    labels,
    organic: labels.map((l) => Math.round(totals.get(l).organic)),
    inorganic: labels.map((l) => Math.round(totals.get(l).inorganic)),
  };
}

/** The alerts list is newest-first. Only show the newest one if it is less than 24h old. */
function latestActiveAlert(alerts, now = Date.now()) {
  if (!Array.isArray(alerts) || alerts.length === 0) return null;
  const d = parseUtc(alerts[0].created_at);
  return d && now - d.getTime() < DAY_MS ? alerts[0] : null;
}

/** Run a drawing step; if it fails (map or chart problem) log it and carry on, so one broken
 *  widget never blanks the whole dashboard in front of the judges. */
function safely(label, fn) {
  try { fn(); } catch (err) { console.error(`${label} failed:`, err); }
}

/* ====================== talking to the backend ====================== */

/** fetch + JSON, turning backend errors ({"error": "..."}) into normal JavaScript errors. */
async function api(path, options) {
  const res = await fetch(path, options);
  let data = null;
  try { data = await res.json(); } catch (_) { /* empty body */ }
  if (!res.ok) throw new Error((data && data.error) || `Request failed (${res.status})`);
  return data;
}

function postJson(path, body) {
  return api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });
}

/* ====================== the dashboard (needs a browser) ====================== */

function startDashboard() {
  const $ = (id) => document.getElementById(id);
  const last = { markers: "", alerts: "", sms: "", stats: "" };   // remember what is drawn, redraw only on change
  let refreshing = false;

  /* ---- toast (small popup message) ---- */
  let toastTimer = null;
  function toast(message) {
    const el = $("toast");
    el.textContent = message;
    el.classList.remove("hidden");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.add("hidden"), 3500);
  }

  /* ---- map ---- */
  let map = null;
  let markerLayer = null;
  try {
    map = L.map("map").setView(ELDORET, 13);
    const tiles = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19, attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);
    tiles.on("tileerror", () => $("map-note").classList.remove("hidden"));   // no internet: say so, keep markers
    markerLayer = L.layerGroup().addTo(map);
  } catch (err) {
    console.error("Map failed to start:", err);
  }

  /* ---- charts ---- */
  let wasteChart = null;
  let compostChart = null;
  try {
    Chart.defaults.font.size = 14;
    wasteChart = new Chart($("waste-chart"), {
      type: "bar",
      data: { labels: [], datasets: [
        { label: "Organic", data: [], backgroundColor: "#16a34a" },
        { label: "Inorganic", data: [], backgroundColor: "#94a3b8" },
      ] },
      options: { responsive: true, maintainAspectRatio: false, scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true } } },
    });
    compostChart = new Chart($("compost-chart"), {
      type: "doughnut",
      data: { labels: ["Ready to order", "Still curing"], datasets: [{ data: [0, 0], backgroundColor: ["#16a34a", "#f59e0b"] }] },
      options: { responsive: true, maintainAspectRatio: false },
    });
  } catch (err) {
    console.error("Charts failed to start:", err);   // the rest of the dashboard still works
  }

  /* ---- renderers: take data, update the page ---- */
  function renderStats(s) {
    $("stat-total").textContent = s.total_waste_kg;
    $("stat-organic").textContent = s.organic_kg;
    $("stat-ready").textContent = s.compost_ready_kg;
    $("stat-pipeline").textContent = s.compost_pipeline_kg;
    $("stat-orders").textContent = `${s.orders_paid} / ${s.orders_pending}`;
    $("stat-alerts").textContent = s.active_alerts;
    if (compostChart) {
      safely("Compost chart", () => {
        compostChart.data.datasets[0].data = [s.compost_ready_kg, s.compost_pipeline_kg];
        compostChart.update("none");
      });
    }
  }

  function renderMarkers(markers) {
    // 1) the text list first: it can't fail, so something useful always shows
    $("report-list").innerHTML = markers.slice(0, 5).map((m) =>
      `<li><span class="dot" style="background:${organicColor(m.organic_pct)}"></span>` +
      `<strong>${escapeHtml(m.estate)}</strong> ${Math.round(m.est_kg)} kg, ${Math.round(m.organic_pct)}% organic` +
      `<span class="when">${escapeHtml(formatTime(m.created_at))}</span></li>`
    ).join("") || '<li class="muted">No reports yet. Upload a waste photo to see the first pin.</li>';

    // 2) the map pins
    if (markerLayer) {
      safely("Map markers", () => {
        markerLayer.clearLayers();
        // markers arrive newest-first; draw oldest first so the newest circle sits on top
        for (const m of [...markers].reverse()) {
          if (typeof m.lat !== "number" || typeof m.lon !== "number") continue;
          L.circleMarker([m.lat, m.lon], {
            radius: markerRadius(m.est_kg), color: "#1f2937", weight: 1.5,
            fillColor: organicColor(m.organic_pct), fillOpacity: 0.8,
          }).bindPopup(
            `<strong>${escapeHtml(m.estate)}</strong><br>${Math.round(m.est_kg)} kg &middot; ` +
            `${Math.round(m.organic_pct)}% organic<br><small>${escapeHtml(formatTime(m.created_at))}</small>`
          ).addTo(markerLayer);
        }
      });
    }

    // 3) the bar chart
    if (wasteChart) {
      safely("Waste chart", () => {
        const agg = aggregateByEstate(markers);
        wasteChart.data.labels = agg.labels;
        wasteChart.data.datasets[0].data = agg.organic;
        wasteChart.data.datasets[1].data = agg.inorganic;
        wasteChart.update("none");
      });
    }
  }

  function renderAlert(alert) {
    const el = $("alert-banner");
    if (!alert) {
      el.className = "alert alert-none";
      el.textContent = "No active weather alerts";
      return;
    }
    const cls = alert.level === "HIGH" ? "alert-high" : alert.level === "MEDIUM" ? "alert-medium" : "alert-low";
    el.className = `alert ${cls}`;
    el.innerHTML = `<strong>${escapeHtml(alert.level)} RAIN ALERT</strong> ${escapeHtml(alert.message)} ` +
      `<span>SMS sent: ${escapeHtml(alert.sms_sent)} &middot; ${escapeHtml(formatTime(alert.created_at))}</span>`;
  }

  function renderSms(list) {
    const box = $("sms-list");
    if (!list.length) { box.innerHTML = '<p class="muted">No messages yet</p>'; return; }
    box.innerHTML = list.map((m) =>
      `<div class="bubble"><div class="bubble-to">To ${escapeHtml(m.to)} &middot; ${escapeHtml(formatTime(m.sent_at))}</div>` +
      `${escapeHtml(m.message)}</div>`).join("");
    box.scrollTop = box.scrollHeight;   // newest message in view
  }

  /* ---- loaders: fetch, then render only if something changed ---- */
  async function loadStats() {
    const s = await api("/dashboard/stats");
    const key = JSON.stringify(s);
    if (key !== last.stats) { last.stats = key; renderStats(s); }
  }
  async function loadMarkers() {
    const m = await api("/dashboard/markers");
    const key = JSON.stringify(m);
    if (key !== last.markers) { last.markers = key; renderMarkers(m); }
  }
  async function loadAlerts() {
    const a = await api("/dashboard/alerts");
    const key = JSON.stringify(a);
    if (key !== last.alerts) { last.alerts = key; renderAlert(latestActiveAlert(a)); }
  }
  async function loadSms() {
    const s = await api("/sms/outbox");
    const key = JSON.stringify(s);
    if (key !== last.sms) { last.sms = key; renderSms(s); }
  }

  function setStatus(okCount, total) {
    const pill = $("status-pill");
    if (okCount === total) { pill.className = "pill pill-ok"; pill.textContent = "Live"; }
    else if (okCount === 0) { pill.className = "pill pill-bad"; pill.textContent = "Offline, retrying..."; }
    else { pill.className = "pill pill-wait"; pill.textContent = "Some data unavailable"; }
  }

  async function refreshAll() {
    if (refreshing) return;            // don't pile up requests if the network is slow
    refreshing = true;
    try {
      const results = await Promise.allSettled([loadStats(), loadMarkers(), loadAlerts(), loadSms()]);
      results.forEach((r) => { if (r.status === "rejected") console.warn("Refresh problem:", r.reason); });
      setStatus(results.filter((r) => r.status === "fulfilled").length, results.length);
    } finally {
      refreshing = false;
    }
  }

  /* ---- estate dropdown ---- */
  async function loadEstates() {
    let estates;
    try { estates = await api("/dashboard/estates"); }
    catch (_) { estates = ["Main Market", "Langas", "Huruma", "Pioneer"].map((name) => ({ name })); }  // backup list
    $("estate").innerHTML = estates.map((e) => `<option>${escapeHtml(e.name)}</option>`).join("");
  }

  /* ---- upload form ---- */
  const photo = $("photo");
  let previewUrl = null;
  photo.addEventListener("change", () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    const file = photo.files[0];
    const img = $("preview");
    if (!file) { img.classList.add("hidden"); return; }
    previewUrl = URL.createObjectURL(file);
    img.src = previewUrl;
    img.classList.remove("hidden");
  });

  function showResult(html, isError) {
    const el = $("upload-result");
    el.className = "result" + (isError ? " error" : "");
    el.innerHTML = html;
  }

  $("upload-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = photo.files[0];
    const kg = parseFloat($("est-kg").value);
    if (!file) return showResult("Choose a photo first.", true);
    if (!(kg > 0)) return showResult("Enter the estimated weight in kg.", true);

    const form = new FormData();
    form.append("image", file);
    form.append("estate", $("estate").value);
    form.append("est_kg", String(kg));

    const btn = $("submit-btn");
    btn.disabled = true;
    btn.textContent = "Analysing...";
    try {
      const r = await api("/waste/upload", { method: "POST", body: form });
      const labels = (r.labels || []).map(escapeHtml).join(", ") || "none";
      showResult(
        `<div class="big">${Math.round(r.organic_pct)}% organic &middot; ${Math.round(r.inorganic_pct)}% inorganic</div>` +
        `<div>Detected: ${labels}</div>` +
        `<span class="tag">${r.source === "demo" ? "demo result (no live AI call)" : "AI model: " + escapeHtml(r.source)}</span>`,
        false
      );
      toast("Report added to the map");
      refreshAll();
    } catch (err) {
      showResult(escapeHtml(err.message), true);
    } finally {
      btn.disabled = false;
      btn.textContent = "Analyse waste";
    }
  });

  /* ---- hidden demo panel (press D) ---- */
  const demoActions = {
    "demo-rain": { run: () => postJson("/climate/alert/trigger"), say: (r) => `Rain alert sent (${r.sms_sent} SMS)` },
    "demo-pay": { run: () => postJson("/mock/mpesa/callback", {}), say: (r) => `Payment ${r.status}, receipt ${r.receipt}` },
    "demo-ready": { run: () => postJson("/admin/mark-ready", { kg: 100 }), say: (r) => `Moved ${r.moved_kg} kg to ready stock` },
    "demo-reset": { run: () => postJson("/admin/reset"), say: () => "Demo data reset", confirm: "Reset all demo data?" },
  };
  for (const [id, action] of Object.entries(demoActions)) {
    $(id).addEventListener("click", async () => {
      if (action.confirm && !window.confirm(action.confirm)) return;
      try { toast(action.say(await action.run())); }
      catch (err) { toast(err.message); }
      refreshAll();
    });
  }
  document.addEventListener("keydown", (e) => {
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test((e.target && e.target.tagName) || "");
    if (e.key.toLowerCase() === "d" && !typing && !e.ctrlKey && !e.metaKey && !e.altKey) {
      $("demo-panel").classList.toggle("hidden");
    }
  });

  /* ---- go ---- */
  loadEstates();
  refreshAll();
  setInterval(refreshAll, REFRESH_MS);
  window.eldogrid = { refreshAll };    // handy in the browser console while debugging
}

/* Start in a browser; export the pure helpers when loaded by Node (for tests). */
if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", startDashboard);
}
if (typeof module !== "undefined") {
  module.exports = { safely, escapeHtml, organicColor, parseUtc, formatTime, markerRadius, aggregateByEstate, latestActiveAlert };
}
