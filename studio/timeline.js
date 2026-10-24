// Read-only timeline viewer: a composition's layers as tracks over Meine's musical structure,
// synced to the rendered preview. Spec: render/TIMELINE.md.
import { makeEval, describe } from "./tlsignal.js";

const $ = id => document.getElementById(id);
const video = $("video"), base = $("base"), over = $("over"), wrap = $("tlwrap"), tip = $("tip");
const bctx = base.getContext("2d"), octx = over.getContext("2d");
const qs = new URLSearchParams(location.search);

const ub = (a, x) => { let lo = 0, hi = a.length; while (lo < hi) { const m = (lo + hi) >> 1; if (a[m] <= x) lo = m + 1; else hi = m; } return lo; };
const lb = (a, x) => { let lo = 0, hi = a.length; while (lo < hi) { const m = (lo + hi) >> 1; if (a[m] < x) lo = m + 1; else hi = m; } return lo; };
const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));
const HIT_TOL = 0.030;   // a hit is "on the beat" within this many seconds
const status = (msg, flash) => {
  const s = $("status"); s.textContent = msg; s.classList.toggle("flash", !!flash);
  if (flash) setTimeout(() => s.classList.remove("flash"), 1500);
};
const mmss = t => { const s = Math.max(0, t), m = Math.floor(s / 60); return `${m}:${(s - m * 60).toFixed(2).padStart(5, "0")}`; };
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const getText = async url => { const r = await fetch(url, { cache: "no-store" }); if (!r.ok) throw new Error(`${r.status} ${url}`); return r.text(); };

// ---------- which timeline ----------
let tlPath = qs.get("tl");
const DEFAULT_DIR = "projects/meine/comps/out";
const tlDir = tlPath ? tlPath.slice(0, tlPath.lastIndexOf("/")) : DEFAULT_DIR;
const listing = (await (await fetch(`/api/ls?dir=${encodeURIComponent(tlDir)}`)).json()).filter(n => n.endsWith(".timeline.json"));
if (!tlPath) {
  const pick = listing.find(n => !n.startsWith("fixture")) || listing[0];
  if (!pick) { status(`no *.timeline.json in ${tlDir}`); throw new Error("no timeline"); }
  tlPath = `${tlDir}/${pick}`;
  history.replaceState(null, "", `?tl=${tlPath}`);
}
{
  const cur = tlPath.slice(tlPath.lastIndexOf("/") + 1);
  const names = listing.includes(cur) ? listing : [cur, ...listing];
  $("pick").innerHTML = names.map(n => `<option${n === cur ? " selected" : ""}>${esc(n)}</option>`).join("");
  $("pick").onchange = () => {
    const p = new URLSearchParams({ tl: `${tlDir}/${$("pick").value}` });
    location.search = p.toString().replace(/%2F/g, "/");
  };
}
const vidPath = qs.get("video") || tlPath.replace(/\.timeline\.json$/, "").replace(/\.json$/, "") + ".mp4";
document.title = `timeline · ${tlPath.split("/").pop()}`;

// ---------- data ----------
let TL, TLtext;
try { TLtext = await getText(`/${tlPath}`); TL = JSON.parse(TLtext); }
catch (e) { status(`can't load ${tlPath}: ${e.message}`); throw e; }
const proj = TL.project || "meine";
const music = JSON.parse(await getText(`/projects/${proj}/analysis/beats.json`));
const B = music.beats, D = music.downbeats, ON = music.onsets, INT = music.intensity;
const ONT = ON.map(o => o[0]);
const sigEval = makeEval(music);

// bar / beat-in-bar for every beat (bar 1 starts on the first downbeat)
const beatBar = new Int32Array(B.length), beatPos = new Int32Array(B.length);
{
  let bar = 0, pos = 0;
  for (let i = 0; i < B.length; i++) {
    const n = ub(D, B[i] + 0.03);
    if (n !== bar) { bar = n; pos = 1; } else pos++;
    beatBar[i] = bar; beatPos[i] = pos;
  }
}
const nearestBeat = t => {
  const i = lb(B, t);
  let j = i;
  if (i >= B.length || (i > 0 && t - B[i - 1] < B[i] - t)) j = i - 1;
  return { i: j, dt: t - B[j] };
};
const barBeat = t => {
  const i = ub(B, t + 1e-6) - 1;
  return i < 0 ? "—" : `${beatBar[i]}.${beatPos[i]}`;
};

// rant words, one lane per resolved sync file
const wordLanes = [];
try {
  const names = (await (await fetch(`/api/ls?dir=projects/${proj}/sync`)).json()).filter(n => n.endsWith(".resolved.json"));
  for (const n of names) {
    const j = JSON.parse(await getText(`/projects/${proj}/sync/${n}`));
    wordLanes.push({ name: n.replace(/\.resolved\.json$/, ""), words: (j.words || []).filter(w => w.end > w.start) });
  }
} catch (e) { console.warn("words:", e); }
const isMissile = w => (w.key || w.w.toLowerCase()).startsWith("missile");

// footage catalogs, loaded on demand: name -> Map(clipId -> clip)
const catalogs = {};
async function catalog(name) {
  if (!(name in catalogs)) {
    catalogs[name] = fetch(`/projects/${proj}/footage/${name}.json`, { cache: "no-store" })
      .then(r => r.ok ? r.json() : { clips: [] }).then(j => new Map(j.clips.map(c => [c.id, c])))
      .catch(() => new Map());
  }
  return catalogs[name];
}

// ---------- layout model ----------
const FIXED = { bg: "#70747e", face: "#ff6a3d", head: "#ff5fa2", weapons: "#e8534a", ground: "#d9a441" };
const colorCache = {};
const colorOf = key => colorCache[key] ??= FIXED[key] || (() => {
  let h = 0; for (const c of key) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return `hsl(${(h * 137.5) % 360}, 55%, 60%)`;
})();
const withAlpha = (css, a) => {  // css colour (#rrggbb or hsl()) at alpha a
  if (css[0] === "#") return css + Math.round(a * 255).toString(16).padStart(2, "0");
  return css.replace("hsl(", "hsla(").replace(")", `, ${a})`);
};

let R0, R1, groups = [], allHits = [], collapsed = new Set(), selId = null, hoverId = null;
const collapseKey = `tlv-collapsed:${tlPath}`;
try { collapsed = new Set(JSON.parse(sessionStorage.getItem(collapseKey) || "[]")); } catch {}

function applyTimeline(tl) {
  TL = tl;
  [R0, R1] = tl.range || [0, music.beats[music.beats.length - 1] || 60];
  const byName = new Map();
  allHits = [];
  for (const [idx, L] of (tl.layers || []).entries()) {
    const g = (L.tags && L.tags[0]) || "(untagged)";
    if (!byName.has(g)) byName.set(g, []);
    const hits = ((L.meta && L.meta.hits_song) || []).map(t => {
      const nb = nearestBeat(t);
      return { t, dt: nb.dt, beat: nb.i, on: Math.abs(nb.dt) <= HIT_TOL };
    });
    const op = L.opacity ?? 1;
    const item = { L, idx, id: L.id ?? `#${idx}`, t0: L.t0 ?? R0, t1: L.t1 ?? R1, hits, group: g,
      color: colorOf((L.meta && L.meta.catalog) || g), constOp: typeof op === "number" ? op : null,
      opKnown: sigEval(op, L.t0 ?? R0) != null };
    byName.get(g).push(item);
    for (const h of hits) allHits.push({ ...h, item });
  }
  allHits.sort((a, b) => a.t - b.t);
  groups = [...byName].map(([name, items]) => {
    items.sort((a, b) => a.t0 - b.t0 || a.idx - b.idx);
    const ends = [], rows = [];
    for (const it of items) {  // greedy interval packing: first row that's free
      let r = ends.findIndex(e => e <= it.t0 + 1e-9);
      if (r < 0) { r = ends.length; ends.push(0); rows.push([]); }
      ends[r] = it.t1; rows[r].push(it); it.row = r;
    }
    return { name, items, rows };
  });
  const on = allHits.filter(h => h.on).length;
  $("sync").innerHTML = allHits.length
    ? `hits <b class="on">${on} on beat</b> · <b class="off">${allHits.length - on} off-grid</b>` : "no hits";
  relayout();
  if (selId != null && !findItem(selId)) selId = null;
  showInspector();
}
const findItem = id => { for (const g of groups) for (const it of g.items) if (it.id === id) return it; return null; };

// ---------- geometry ----------
const GUT = 150, RULER = 38, INTH = 44, ONH = 22, HITH = 20, WORDH = 20, ROWH = 20, GRPH = 20, SBH = 12;
const FONT = "11px ui-monospace, Menlo, monospace";
let W = 0, H = 0, dpr = 1, yInt, yOn, yHit, yWords, yTracks, tracksH = 0, contentH = 0;
let rowsLayout = [];   // [{kind: 'group'|'row', g, r, y, h}] in content coords (0 = top of track area)
const view = { t0: 0, pps: 1, scrollY: 0 };

function relayout() {
  yInt = RULER; yOn = yInt + INTH; yHit = yOn + ONH; yWords = yHit + HITH;
  yTracks = yWords + WORDH * wordLanes.length + 4;
  rowsLayout = [];
  let y = 0;
  for (const g of groups) {
    rowsLayout.push({ kind: "group", g, y, h: GRPH }); y += GRPH;
    if (collapsed.has(g.name)) continue;
    for (let r = 0; r < g.rows.length; r++) { rowsLayout.push({ kind: "row", g, r, y, h: ROWH }); y += ROWH; }
  }
  contentH = y + 8;
  tracksH = Math.max(0, H - SBH - yTracks);
  view.scrollY = clamp(view.scrollY, 0, Math.max(0, contentH - tracksH));
  dirty = true;
}
function resize() {
  dpr = devicePixelRatio || 1;
  W = wrap.clientWidth; H = wrap.clientHeight;
  for (const c of [base, over]) { c.width = Math.round(W * dpr); c.height = Math.round(H * dpr); }
  relayout();
  clampView();
}
const trackW = () => Math.max(50, W - GUT);
const X = t => GUT + (t - view.t0) * view.pps;
const T = x => view.t0 + (x - GUT) / view.pps;
const minPps = () => trackW() / ((R1 - R0) * 1.02 || 1);
function clampView() {
  view.pps = clamp(view.pps, minPps(), 2000);
  const vis = trackW() / view.pps, pad = (R1 - R0) * 0.01;
  view.t0 = clamp(view.t0, R0 - pad, Math.max(R0 - pad, R1 + pad - vis));
  dirty = true;
}
function fit() { view.pps = minPps(); view.t0 = R0 - (R1 - R0) * 0.01; clampView(); }
function zoomAt(f, x) { const t = T(x); view.pps *= f; clampView(); view.t0 = t - (x - GUT) / view.pps; clampView(); }

// pixel snapping: every line is a fillRect on whole device pixels
const sn = v => Math.round(v * dpr) / dpr;
function vline(c, x, y0, y1, w = 1) { c.fillRect(sn(x), y0, Math.max(1, Math.round(w * dpr)) / dpr, y1 - y0); }
function hline(c, x0, x1, y, w = 1) { c.fillRect(x0, sn(y), x1 - x0, Math.max(1, Math.round(w * dpr)) / dpr); }

// pick a step from `steps` so that consecutive marks are at least `minPx` apart
const stepFor = (unitPx, steps, minPx) => steps.find(s => s * unitPx >= minPx) ?? steps[steps.length - 1];

// ---------- base drawing (everything but playhead / hover / selection) ----------
let dirty = true;
function drawBase() {
  dirty = false;
  const c = bctx;
  c.setTransform(dpr, 0, 0, dpr, 0, 0);
  c.fillStyle = "#111"; c.fillRect(0, 0, W, H);
  c.font = FONT; c.textBaseline = "middle";
  const tA = T(GUT) - 0.5, tB = T(W) + 0.5;
  const beatPx = (B.length > 1 ? (B[B.length - 1] - B[0]) / (B.length - 1) : 0.5) * view.pps;
  const barPx = beatPx * 4;
  const barStepLine = stepFor(barPx, [1, 2, 4, 8, 16, 32, 64], 7);
  const barStepLabel = stepFor(barPx, [1, 2, 4, 8, 16, 32, 64], 34);
  const showBeats = beatPx >= 7;
  const i0 = Math.max(0, lb(B, tA)), i1 = Math.min(B.length, ub(B, tB));

  c.save(); c.beginPath(); c.rect(GUT, 0, W - GUT, H); c.clip();
  // grid behind lanes and tracks
  for (let i = i0; i < i1; i++) {
    const down = beatPos[i] === 1 && beatBar[i] > 0;
    if (down && (beatBar[i] - 1) % barStepLine === 0) {
      const big = (beatBar[i] - 1) % (barStepLine * 4) === 0;
      c.fillStyle = big ? "#34343b" : "#27272c";
      vline(c, X(B[i]), RULER, H - SBH);
    } else if (showBeats) { c.fillStyle = "#1c1c20"; vline(c, X(B[i]), yTracks, H - SBH); }
  }
  // range ends
  c.fillStyle = "#0008";
  if (X(R0) > GUT) c.fillRect(GUT, 0, X(R0) - GUT, H);
  if (X(R1) < W) c.fillRect(X(R1), 0, W - X(R1), H);

  // ruler
  c.fillStyle = "#1b1b1d"; c.fillRect(GUT, 0, W - GUT, RULER);
  for (let i = i0; i < i1; i++) {
    const x = X(B[i]), down = beatPos[i] === 1 && beatBar[i] > 0;
    if (down && (beatBar[i] - 1) % barStepLabel === 0) {
      c.fillStyle = "#cfcfcf"; vline(c, x, 2, 20);
      c.fillText(String(beatBar[i]), x + 3, 9);
    } else if (down && (beatBar[i] - 1) % barStepLine === 0) { c.fillStyle = "#666"; vline(c, x, 10, 20); }
    else if (showBeats) { c.fillStyle = "#4a4a50"; vline(c, x, 15, 20); }
  }
  const secStep = stepFor(view.pps, [0.04, 0.1, 0.2, 0.5, 1, 2, 5, 10, 15, 30, 60, 120], 70);
  c.fillStyle = "#888";
  for (let s = Math.ceil(tA / secStep) * secStep; s <= tB; s += secStep) {
    const x = X(s); vline(c, x, 24, RULER);
    c.fillText(secStep < 1 ? mmss(s) : mmss(s).replace(/\.00$/, ""), x + 3, 30);
  }
  c.fillStyle = "#2a2a2e"; hline(c, GUT, W, RULER - 1);

  // intensity: filled area
  {
    const v = INT.values, dt = INT.dt, y0 = yInt + INTH - 3, hh = INTH - 6;
    const a = clamp(Math.floor(tA / dt), 0, v.length - 1), b = clamp(Math.ceil(tB / dt), 0, v.length - 1);
    c.beginPath(); c.moveTo(X(a * dt), y0);
    for (let k = a; k <= b; k++) c.lineTo(X(k * dt), y0 - v[k] * hh);
    c.lineTo(X(b * dt), y0); c.closePath();
    const grad = c.createLinearGradient(0, y0 - hh, 0, y0);
    grad.addColorStop(0, "#ff6a3dcc"); grad.addColorStop(1, "#ff6a3d22");
    c.fillStyle = grad; c.fill();
    c.beginPath();
    for (let k = a; k <= b; k++) c[k === a ? "moveTo" : "lineTo"](X(k * dt), y0 - v[k] * hh);
    c.strokeStyle = "#ff8a5d"; c.lineWidth = 1; c.stroke();
  }
  // onsets: ticks scaled by strength
  {
    const y0 = yOn + ONH - 2, hh = ONH - 4;
    const a = lb(ONT, tA), b = ub(ONT, tB);
    for (let k = a; k < b; k++) {
      const s = ON[k][1];
      c.fillStyle = `rgba(190,200,215,${0.25 + 0.6 * s})`;
      vline(c, X(ON[k][0]), y0 - Math.max(2, s * hh), y0);
    }
  }
  // all hits, one lane
  for (const h of allHits) {
    if (h.t < tA || h.t > tB) continue;
    c.fillStyle = h.on ? "#5dffa0" : "#ff2d55";
    vline(c, X(h.t), yHit + 3, yHit + HITH - 3, 2);
  }
  // words
  for (const [li, lane] of wordLanes.entries()) {
    const y = yWords + li * WORDH, ws = lane.words;
    for (let k = 0; k < ws.length; k++) {
      const w = ws[k];
      if (w.end < tA || w.start > tB) continue;
      const x0 = X(w.start), x1 = Math.max(x0 + 1, X(w.end)), m = isMissile(w);
      c.fillStyle = m ? "#ff2d55" : "#3a3a44";
      c.fillRect(sn(x0), y + 3, Math.max(1 / dpr, sn(x1) - sn(x0)), WORDH - 6);
      if (m) { c.fillStyle = "#ff2d5540"; vline(c, x0, yHit, yHit + HITH); }
      const room = (k + 1 < ws.length ? X(ws[k + 1].start) : W) - x0 - 4;
      const tw = c.measureText(w.w).width;
      if (room > 14) {
        c.save(); c.beginPath(); c.rect(x0, y, room, WORDH); c.clip();
        c.fillStyle = m ? "#fff" : (tw > x1 - x0 ? "#9a9aa4" : "#ddd");
        c.fillText(w.w, x0 + 2, y + WORDH / 2 + 0.5);
        c.restore();
      }
    }
  }
  c.restore();

  // tracks
  c.save(); c.beginPath(); c.rect(0, yTracks, W, tracksH); c.clip();
  c.fillStyle = "#2a2a2e"; hline(c, 0, W, yTracks - 1);
  const top = view.scrollY, bot = view.scrollY + tracksH;
  for (const row of rowsLayout) {
    if (row.y + row.h < top || row.y > bot) continue;
    const y = yTracks + row.y - view.scrollY;
    if (row.kind === "group") {
      c.fillStyle = "#18181b"; c.fillRect(0, y, W, row.h);
      c.fillStyle = "#26262b"; hline(c, 0, W, y);
      if (collapsed.has(row.g.name)) {  // collapsed: everything overlapped in the header row
        c.save(); c.beginPath(); c.rect(GUT, y, W - GUT, row.h); c.clip();
        for (const it of row.g.items) drawItem(c, it, y, row.h, tA, tB, true);
        c.restore();
      }
    } else {
      c.save(); c.beginPath(); c.rect(GUT, y, W - GUT, row.h); c.clip();
      for (const it of row.g.rows[row.r]) drawItem(c, it, y, row.h, tA, tB, false);
      c.restore();
    }
  }
  c.restore();

  // gutter labels
  c.fillStyle = "#1b1b1d"; c.fillRect(0, 0, GUT, H);
  c.fillStyle = "#2a2a2e"; vline(c, GUT - 1, 0, H);
  c.fillStyle = "#888";
  const lab = (s, y) => c.fillText(s, 8, y);
  lab(`bar · ${(TL.layers || []).length} layers`, 10); lab("mm:ss", 30);
  lab("intensity", yInt + INTH / 2); lab("onsets", yOn + ONH / 2); lab("hits", yHit + HITH / 2);
  for (const [li, lane] of wordLanes.entries()) lab(lane.name.slice(0, 19), yWords + li * WORDH + WORDH / 2);
  c.save(); c.beginPath(); c.rect(0, yTracks, GUT, tracksH); c.clip();
  for (const row of rowsLayout) {
    if (row.kind !== "group" || row.y + row.h < top || row.y > bot) continue;
    const y = yTracks + row.y - view.scrollY, g = row.g, on = g.items.reduce((n, it) => n + it.hits.filter(h => h.on).length, 0);
    const nh = g.items.reduce((n, it) => n + it.hits.length, 0);
    c.fillStyle = "#18181b"; c.fillRect(0, y, GUT - 1, row.h);
    c.fillStyle = colorOf(g.name === "(untagged)" ? g.name : (g.items[0].L.meta?.catalog || g.name));
    c.fillRect(0, y + 3, 3, row.h - 6);
    c.fillStyle = "#ddd";
    c.fillText(`${collapsed.has(g.name) ? "▸" : "▾"} ${g.name.slice(0, 11)} ${g.items.length}`, 8, y + row.h / 2 + 0.5);
    if (nh) { c.fillStyle = on === nh ? "#5dffa0" : "#ff2d55"; c.textAlign = "right"; c.fillText(`${on}/${nh}`, GUT - 6, y + row.h / 2 + 0.5); c.textAlign = "left"; }
  }
  c.restore();

  // horizontal scrollbar
  const sy = H - SBH;
  c.fillStyle = "#18181b"; c.fillRect(0, sy, W, SBH);
  const sb = scrollbar();
  c.fillStyle = "#3a3a40"; c.fillRect(sb.x, sy + 2, sb.w, SBH - 4);
  // vertical position hint
  if (contentH > tracksH) {
    const h = tracksH * tracksH / contentH, y = yTracks + view.scrollY / contentH * tracksH;
    c.fillStyle = "#3a3a40"; c.fillRect(W - 4, y, 3, h);
  }
}
const scrollbar = () => {
  const span = R1 - R0 || 1, vis = trackW() / view.pps;
  const x = GUT + clamp((view.t0 - R0) / span, 0, 1) * trackW(), w = Math.max(16, Math.min(1, vis / span) * trackW());
  return { x: Math.min(x, W - w), w };
};

const BLEND_ABBR = { screen: "scr", add: "add", multiply: "mul", difference: "dif", lighten: "lit", darken: "drk", overlay: "ovl" };
function drawItem(c, it, y, h, tA, tB, ghost) {
  if (it.t1 < tA || it.t0 > tB) return;
  const L = it.L, x0 = Math.max(GUT - 2, X(it.t0)), x1 = Math.min(W + 2, X(it.t1));
  const w = Math.max(1 / dpr, x1 - x0), yb = y + 2, hb = h - 4;
  c.fillStyle = withAlpha(it.color, ghost ? 0.12 : 0.18);
  c.fillRect(sn(x0), yb, sn(x1) - sn(x0) || 1 / dpr, hb);
  // opacity x fade envelope as a filled curve (a hint: how present the layer is)
  const fadeIn = L.fade?.in || 0, fadeOut = L.fade?.out || 0;
  const env = t => {
    let o = it.constOp ?? (sigEval(L.opacity, t) ?? 1);
    if (fadeIn > 0) o *= clamp((t - it.t0) / fadeIn, 0, 1);
    if (fadeOut > 0) o *= clamp((it.t1 - t) / fadeOut, 0, 1);
    return clamp(o, 0, 1);
  };
  c.fillStyle = withAlpha(it.color, ghost ? 0.3 : 0.55);
  if (w < 6) c.fillRect(sn(x0), yb + hb * (1 - env((it.t0 + it.t1) / 2)), w, hb * env((it.t0 + it.t1) / 2));
  else {
    const step = 2, xa = Math.max(x0, GUT), xb = Math.min(x1, W);
    c.beginPath(); c.moveTo(xa, yb + hb);
    for (let x = xa; x <= xb + step; x += step) { const xx = Math.min(x, xb); c.lineTo(xx, yb + hb * (1 - env(T(xx)))); }
    c.lineTo(xb, yb + hb); c.closePath(); c.fill();
  }
  if (!ghost) {
    c.fillStyle = it.color; c.fillRect(sn(X(it.t0)), yb, Math.max(1, Math.round(2 * dpr)) / dpr, hb);
    if (w > 26) {
      const blend = L.blend && L.blend !== "normal" ? ` ${BLEND_ABBR[L.blend] || L.blend}` : "";
      const op = it.constOp != null ? (it.constOp < 1 ? ` ${Math.round(it.constOp * 100)}%` : "") : (it.opKnown ? " ~" : " ?");
      c.save(); c.beginPath(); c.rect(x0, y, w - 2, h); c.clip();
      c.fillStyle = "#eee"; c.fillText(it.id, Math.max(x0, GUT) + 5, y + h / 2 + 0.5);
      if (blend || op) {
        const tx = Math.max(x0, GUT) + 9 + c.measureText(it.id).width;
        c.fillStyle = "#aab"; c.fillText(blend + op, tx, y + h / 2 + 0.5);
      }
      c.restore();
    }
  }
  for (const hit of it.hits) {
    if (hit.t < tA || hit.t > tB) continue;
    const x = X(hit.t);
    c.fillStyle = hit.on ? "#5dffa0" : "#ff2d55";
    vline(c, x - 1, y + 1, y + h - 1, 2);
    if (!ghost) {
      if (hit.on) {  // a little cap: on the grid
        c.beginPath(); c.moveTo(x - 3.5, y + 1); c.lineTo(x + 3.5, y + 1); c.lineTo(x, y + 5); c.closePath(); c.fill();
      } else if (view.pps > 120) {
        c.font = "9px ui-monospace, Menlo, monospace";
        c.fillText(`${hit.dt > 0 ? "+" : ""}${Math.round(hit.dt * 1000)}`, x + 3, y + 6);
        c.font = FONT;
      }
    }
  }
}

// ---------- overlay: playhead, hover, selection ----------
let lastOver = "";
function drawOver() {
  const t = clock.t(), key = `${t}|${hoverId}|${selId}|${hoverX}|${W}|${H}|${view.t0}|${view.pps}|${view.scrollY}`;
  if (key === lastOver) return;
  lastOver = key;
  const c = octx;
  c.setTransform(dpr, 0, 0, dpr, 0, 0);
  c.clearRect(0, 0, W, H);
  c.save(); c.beginPath(); c.rect(GUT, 0, W - GUT, H - SBH); c.clip();
  for (const [id, col, lw] of [[hoverId, "#ffffff70", 1], [selId, "#fff", 2]]) {
    if (id == null) continue;
    const it = findItem(id), r = it && itemRect(it);
    if (!r) continue;
    c.save(); c.beginPath(); c.rect(0, yTracks, W, tracksH); c.clip();
    c.strokeStyle = col; c.lineWidth = lw;
    c.strokeRect(sn(r.x) + lw / 2, r.y + lw / 2, Math.max(2, sn(r.w) - lw), r.h - lw);
    c.restore();
  }
  if (hoverX != null && hoverX > GUT) { c.fillStyle = "#ffffff22"; vline(c, hoverX, 0, H - SBH); }
  const x = X(t);
  c.fillStyle = "#ff6a3d"; vline(c, x, 0, H - SBH, 1.5);
  c.beginPath(); c.moveTo(x - 5, 0); c.lineTo(x + 5, 0); c.lineTo(x, 7); c.closePath(); c.fill();
  c.restore();
  // video time readout in the toolbar too
  $("time").textContent = `${mmss(t)} · bar ${barBeat(t)}`;
}
function itemRect(it) {
  const g = groups.find(g => g.name === it.group);
  const row = rowsLayout.find(r => r.g === g && (collapsed.has(g.name) ? r.kind === "group" : r.kind === "row" && r.r === it.row));
  if (!row) return null;
  const x0 = X(it.t0), x1 = X(it.t1);
  return { x: x0, w: Math.max(2, x1 - x0), y: yTracks + row.y - view.scrollY + 1, h: row.h - 2 };
}

// ---------- hit testing ----------
function rowAt(y) {
  if (y < yTracks || y > yTracks + tracksH) return null;
  const cy = y - yTracks + view.scrollY;
  return rowsLayout.find(r => cy >= r.y && cy < r.y + r.h) || null;
}
function itemAt(x, y) {
  const row = rowAt(y);
  if (!row || x < GUT) return null;
  const t = T(x), slop = 3 / view.pps;
  const list = row.kind === "group" ? (collapsed.has(row.g.name) ? row.g.items : []) : row.g.rows[row.r];
  let best = null;
  for (const it of list) if (t >= it.t0 - slop && t <= it.t1 + slop) best = it;  // last = latest start
  return best;
}
function hitAt(x, y) {  // a hit tick under the pointer: [hit, item]
  const row = rowAt(y), inLane = y >= yHit && y < yHit + HITH;
  const cands = inLane ? allHits.map(h => [h, h.item]) : row ? (row.kind === "row" ? row.g.rows[row.r] : collapsed.has(row.g.name) ? row.g.items : []).flatMap(it => it.hits.map(h => [h, it])) : [];
  let best = null, bd = 4;
  for (const [h, it] of cands) { const d = Math.abs(X(h.t) - x); if (d < bd) { bd = d; best = [h, it]; } }
  return best;
}
function wordAt(x, y) {
  if (y < yWords || y >= yWords + WORDH * wordLanes.length) return null;
  const lane = wordLanes[Math.floor((y - yWords) / WORDH)], t = T(x);
  return lane && lane.words.find(w => t >= w.start - 2 / view.pps && t <= w.end + 2 / view.pps);
}

// ---------- clock: the video when there is one, else a virtual clock ----------
let videoOK = false, vClock = { t: 0, playing: false, at: 0 };
const clock = {
  t() {
    if (videoOK) return R0 + video.currentTime;
    if (vClock.playing) { const n = performance.now(); vClock.t += (n - vClock.at) / 1000; vClock.at = n; if (vClock.t >= R1) { vClock.t = R1; vClock.playing = false; } }
    return vClock.t;
  },
  seek(t) {
    t = clamp(t, R0, R1);
    vClock.t = t;
    if (videoOK) video.currentTime = clamp(t - R0, 0, video.duration || 1e9);
  },
  playing: () => (videoOK ? !video.paused : vClock.playing),
  play() { if (videoOK) video.play().catch(e => status("play: " + e.message)); else { vClock.playing = true; vClock.at = performance.now(); } },
  pause() { if (videoOK) video.pause(); vClock.playing = false; },
  toggle() { clock.playing() ? clock.pause() : clock.play(); },
};
video.addEventListener("play", () => ($("play").textContent = "❚❚"));
video.addEventListener("pause", () => ($("play").textContent = "▶"));
video.addEventListener("click", () => clock.toggle());

let vidSig = null, vidPending = null, vidStable = 0;
let hasStat = true;
async function videoSig() {
  if (hasStat) try {
    const r = await fetch(`/api/stat?path=${encodeURIComponent(vidPath)}`, { cache: "no-store" });
    if (r.ok) { const s = await r.json(); return s ? `${s.mtime}|${s.size}` : "missing"; }
    hasStat = false;  // an older server.py without /api/stat: fall back to HEAD
  } catch { hasStat = false; }
  try {
    const r = await fetch(`/${vidPath}`, { method: "HEAD", cache: "no-store" });
    return r.ok ? `${r.headers.get("Last-Modified")}|${r.headers.get("Content-Length")}` : "missing";
  } catch { return "missing"; }
}
function loadVideo(sig) {
  const t = clock.t(), wasPlaying = clock.playing();
  vidSig = sig;
  if (sig === "missing") {
    videoOK = false; video.removeAttribute("src"); video.load();
    $("novideo").style.display = "block";
    $("novideo").textContent = `no preview at ${vidPath} yet; it will load when it appears`;
    return;
  }
  $("novideo").style.display = "none";
  video.src = `/${vidPath}?v=${encodeURIComponent(sig)}`;
  video.addEventListener("loadedmetadata", () => {
    videoOK = true;
    video.currentTime = clamp(t - R0, 0, video.duration);
    if (wasPlaying) video.play().catch(() => {});
  }, { once: true });
  video.addEventListener("error", () => { videoOK = false; status(`video error: ${vidPath}`); }, { once: true });
}

// ---------- live reload ----------
async function poll() {
  try {
    const txt = await getText(`/${tlPath}`);
    if (txt !== TLtext) {
      let j = null;
      try { j = JSON.parse(txt); } catch { status("timeline changed but doesn't parse yet (mid-write?)"); }
      if (j) { TLtext = txt; applyTimeline(j); status(`reloaded ${new Date().toLocaleTimeString()} · ${(j.layers || []).length} layers`, true); }
    }
  } catch (e) { status(`poll: ${e.message}`); }
  const s = await videoSig();
  if (s !== vidSig) {  // reload only once it has stopped changing (the renderer may still be writing)
    if (s === vidPending) vidStable++; else { vidPending = s; vidStable = 1; }
    if (vidStable >= 2) { loadVideo(s); if (s !== "missing") status(`video reloaded ${new Date().toLocaleTimeString()}`, true); }
  } else vidPending = null;
  setTimeout(poll, 1500);
}

// ---------- inspector ----------
async function showInspector() {
  const el = $("insp"), it = selId != null ? findItem(selId) : null;
  if (!it) {
    const n = (TL.layers || []).length;
    el.innerHTML = `<h3>${esc(tlPath.split("/").pop())}</h3><div class="kv">
      <span>project</span><span>${esc(proj)}</span><span>size</span><span>${esc((TL.size || []).join("×"))} @ ${esc(TL.fps)} fps</span>
      <span>range</span><span>${mmss(R0)} – ${mmss(R1)} (${(R1 - R0).toFixed(2)} s)</span><span>layers</span><span>${n} in ${groups.length} groups</span>
      <span>music</span><span>${esc(TL.music?.src ?? "—")}</span><span>video</span><span>${esc(vidPath)}</span>
      <span>tempo</span><span>${(+music.tempo).toFixed(2)} BPM · ${B.length} beats · ${D.length} bars</span></div>
      <pre>${esc(JSON.stringify({ post: TL.post || [] }, null, 1))}</pre><p class="prov">click a layer to inspect it</p>`;
    return;
  }
  const L = it.L, m = L.meta;
  const beats = (it.t1 - it.t0) / ((B[B.length - 1] - B[0]) / (B.length - 1));
  let html = `<h3>${esc(it.id)}</h3><div class="kv">
    <span>span</span><span>${it.t0.toFixed(3)} – ${it.t1.toFixed(3)} (${(it.t1 - it.t0).toFixed(2)} s, ${beats.toFixed(1)} beats)</span>
    <span>bars</span><span>${barBeat(it.t0)} → ${barBeat(it.t1)}</span>
    <span>tags</span><span>${(L.tags || []).map(t => `<span class="tag">${esc(t)}</span>`).join("")}</span>
    <span>opacity</span><span>${esc(describe(L.opacity ?? 1))}</span><span>blend</span><span>${esc(L.blend || "normal")}</span></div>`;
  if (it.hits.length) {
    html += `<div class="kv"><span>hits</span><span>${it.hits.map(h =>
      `<span class="${h.on ? "on" : "off"}">${h.t.toFixed(3)} ${h.on ? "✓" : "✗"} ${h.dt >= 0 ? "+" : ""}${Math.round(h.dt * 1000)}ms @${barBeat(B[h.beat])}</span>`).join("<br>")}</span></div>`;
  }
  let segHtml = "";
  if (m && m.catalog) {
    segHtml = `<p class="prov">loading catalog ${esc(m.catalog)}…</p>`;
    catalog(m.catalog).then(cat => {
      if (selId !== it.id) return;
      const clip = cat.get(m.clip), seg = clip && clip.segments && clip.segments[m.seg];
      const box = $("segbox");
      if (!box) return;
      if (!clip) { box.innerHTML = `<p class="off">clip ${esc(m.clip)} not in ${esc(m.catalog)}.json</p>`; return; }
      box.innerHTML = `<div class="kv"><span>clip</span><span>${esc(clip.id)}${seg ? ` · seg ${m.seg} [${seg.in}–${seg.out}]` : ""}</span>
        <span>publisher</span><span>${esc(clip.publisher || "—")}</span><span>date</span><span>${esc(clip.date || "—")}</span>
        ${seg ? `<span>graphic</span><span>${esc(seg.graphic ?? "—")} · intensity ${esc(seg.intensity ?? "—")}${seg.identifiable_victims ? ' · <span class="off">identifiable victims</span>' : ""}</span>
        <span>tags</span><span>${(seg.tags || []).map(t => `<span class="tag">${esc(t)}</span>`).join("")}</span>` : `<span>seg</span><span class="off">seg ${esc(m.seg)} missing</span>`}
        ${clip.license ? `<span>license</span><span>${esc(clip.license)}</span>` : ""}
        ${clip.source_url ? `<span>source</span><span><a href="${esc(clip.source_url)}" target="_blank" rel="noopener">${esc(clip.source_url.replace(/^https?:\/\//, "").slice(0, 48))}</a></span>` : ""}</div>
        ${seg ? `<p class="desc">${esc(seg.desc || "")}</p>` : ""}
        ${seg?.notes ? `<p class="prov">notes: ${esc(seg.notes)}</p>` : ""}
        <p class="prov">${esc(clip.provenance || "")}</p>
        ${seg?.hits?.length ? `<div class="kv"><span>src hits</span><span>${seg.hits.map(h => `${h.t} ${esc(h.kind)}${h.note ? ` (${esc(h.note)})` : ""}`).join("<br>")}</span></div>` : ""}`;
    });
  }
  el.innerHTML = html + `<div id="segbox">${segHtml}</div><pre>${esc(JSON.stringify(L, null, 1))}</pre>`;
}

// ---------- pointer ----------
let drag = null, hoverX = null;
const pos = e => { const r = over.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
over.addEventListener("pointerdown", e => {
  const [x, y] = pos(e);
  over.setPointerCapture(e.pointerId);
  if (y >= H - SBH) {
    const sb = scrollbar();
    if (x >= sb.x && x <= sb.x + sb.w) drag = { kind: "sb", x, t0: view.t0 };
    else { view.t0 = R0 + (x - GUT) / trackW() * (R1 - R0) - trackW() / view.pps / 2; clampView(); drag = { kind: "sb", x, t0: view.t0 }; }
    return;
  }
  if (x < GUT) {
    const row = rowAt(y);
    if (row && row.kind === "group") {
      collapsed.has(row.g.name) ? collapsed.delete(row.g.name) : collapsed.add(row.g.name);
      try { sessionStorage.setItem(collapseKey, JSON.stringify([...collapsed])); } catch {}
      relayout();
    }
    drag = { kind: "vscroll", y, sy: view.scrollY };
    return;
  }
  if (y < yTracks) { drag = { kind: "scrub" }; clock.seek(T(x)); return; }
  const it = itemAt(x, y);
  drag = { kind: "pan", x, y, t0: view.t0, sy: view.scrollY, moved: false, it };
});
over.addEventListener("pointermove", e => {
  const [x, y] = pos(e);
  hoverX = x;
  if (drag) {
    tip.style.display = "none";
    if (drag.kind === "scrub") clock.seek(T(x));
    else if (drag.kind === "sb") { view.t0 = drag.t0 + (x - drag.x) / trackW() * (R1 - R0); clampView(); }
    else if (drag.kind === "vscroll") { view.scrollY = clamp(drag.sy - (y - drag.y), 0, Math.max(0, contentH - tracksH)); dirty = true; }
    else if (drag.kind === "pan") {
      if (Math.abs(x - drag.x) + Math.abs(y - drag.y) > 3) drag.moved = true;
      if (drag.moved) {
        view.t0 = drag.t0 - (x - drag.x) / view.pps; clampView();
        view.scrollY = clamp(drag.sy - (y - drag.y), 0, Math.max(0, contentH - tracksH)); dirty = true;
      }
    }
    return;
  }
  const it = itemAt(x, y);
  hoverId = it ? it.id : null;
  over.style.cursor = y >= H - SBH ? "default" : y < yTracks && x > GUT ? "ew-resize" : it ? "pointer" : x < GUT ? "default" : "grab";
  showTip(e, x, y, it);
});
over.addEventListener("pointerup", e => {
  if (drag && drag.kind === "pan" && !drag.moved) {
    if (drag.it) { selId = drag.it.id; showInspector(); }
    else { const [x] = pos(e); clock.seek(T(x)); }
  }
  drag = null;
});
over.addEventListener("pointerleave", () => { hoverX = null; hoverId = null; tip.style.display = "none"; });
over.addEventListener("dblclick", e => { const [x, y] = pos(e), it = itemAt(x, y); if (it) clock.seek(it.t0); });
over.addEventListener("wheel", e => {
  e.preventDefault();
  const [x, y] = pos(e);
  const px = e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? H : 1;
  const dx = e.deltaX * px, dy = e.deltaY * px;
  if (e.altKey || (x < GUT && y >= yTracks)) {
    view.scrollY = clamp(view.scrollY + (dy || dx), 0, Math.max(0, contentH - tracksH)); dirty = true;
  } else if (e.shiftKey && !e.ctrlKey) {
    view.t0 += (dy || dx) / view.pps; clampView();
  } else {
    if (dx && Math.abs(dx) > Math.abs(dy)) { view.t0 += dx / view.pps; clampView(); }
    else if (dy) zoomAt(Math.exp(-dy * (e.ctrlKey ? 0.01 : 0.0025)), Math.max(GUT, x));
  }
  tip.style.display = "none";
}, { passive: false });

function showTip(e, x, y, it) {
  let s = null;
  const hw = hitAt(x, y), w = wordAt(x, y);
  if (hw) {
    const [h, hi] = hw, nb = B[h.beat];
    const oi = ub(ONT, h.t), on = [ONT[oi - 1], ONT[oi]].filter(v => v != null).sort((a, b) => Math.abs(a - h.t) - Math.abs(b - h.t))[0];
    s = `${h.on ? "✓ on beat" : "✗ OFF-GRID"}  ${h.dt >= 0 ? "+" : ""}${Math.round(h.dt * 1000)} ms vs beat ${barBeat(nb)} (${nb.toFixed(3)})\n` +
        `hit ${h.t.toFixed(3)} · ${hi.id}` + (on != null ? `\nnearest onset ${on.toFixed(3)} (${Math.round((h.t - on) * 1000)} ms)` : "");
  } else if (w) s = `"${w.w}"  ${w.start.toFixed(3)} – ${w.end.toFixed(3)} · bar ${barBeat(w.start)}`;
  else if (it) {
    const L = it.L;
    s = `${it.id}  [${(L.tags || []).join(", ")}]\n${it.t0.toFixed(2)} – ${it.t1.toFixed(2)} · bar ${barBeat(it.t0)} → ${barBeat(it.t1)}\n` +
        `opacity ${describe(L.opacity ?? 1)} · ${L.blend || "normal"}` + (L.fx?.length ? ` · fx ${L.fx.map(f => f.op).join(" ")}` : "") +
        (it.hits.length ? `\nhits ${it.hits.filter(h => h.on).length}/${it.hits.length} on beat` : "");
    const m = L.meta, cat = m && catalogs[m.catalog];
    if (cat) cat.then(map => {
      const seg = map.get(m.clip)?.segments?.[m.seg];
      if (seg && hoverId === it.id && tip.style.display === "block" && !tip.dataset.seg) { tip.dataset.seg = "1"; tip.textContent += `\n— ${seg.desc}`; }
    });
    else if (m && m.catalog) catalog(m.catalog);
  } else if (y < yTracks && x > GUT) s = `${mmss(T(x))} · bar ${barBeat(T(x))}`;
  if (!s) { tip.style.display = "none"; return; }
  if (tip.textContent !== s && !(tip.dataset.seg && tip.textContent.startsWith(s))) { tip.textContent = s; delete tip.dataset.seg; }
  tip.style.display = "block";
  const r = tip.getBoundingClientRect();
  tip.style.left = Math.min(innerWidth - r.width - 6, e.clientX + 14) + "px";
  tip.style.top = (e.clientY + 18 + r.height > innerHeight ? e.clientY - r.height - 10 : e.clientY + 18) + "px";
}

// ---------- splitter ----------
{
  const top = $("top");
  let sd = null;
  $("split").addEventListener("pointerdown", e => { $("split").setPointerCapture(e.pointerId); sd = { y: e.clientY, h: top.offsetHeight }; });
  $("split").addEventListener("pointermove", e => { if (sd) top.style.height = clamp(sd.h + e.clientY - sd.y, 80, innerHeight - 200) + "px"; });
  $("split").addEventListener("pointerup", () => { sd = null; });
}

// ---------- keys ----------
const fps = () => TL.fps || 25;
function step(arr, dir) {
  const t = clock.t();
  const i = dir > 0 ? ub(arr, t + 0.005) : lb(arr, t - 0.005) - 1;
  if (i >= 0 && i < arr.length) clock.seek(arr[i]);
}
function nextOff(dir) {
  const t = clock.t(), off = allHits.filter(h => !h.on);
  if (!off.length) return status("no off-grid hits");
  const h = dir > 0 ? off.find(h => h.t > t + 0.01) || off[0] : [...off].reverse().find(h => h.t < t - 0.01) || off[off.length - 1];
  clock.pause(); clock.seek(h.t);
  selId = h.item.id; showInspector();
  const vis = trackW() / view.pps;
  if (h.t < view.t0 || h.t > view.t0 + vis) { view.t0 = h.t - vis / 2; clampView(); }
  // scroll the selected row into view
  const r = itemRect(h.item);
  if (r && (r.y < yTracks || r.y + r.h > yTracks + tracksH)) { view.scrollY = clamp(r.y - yTracks + view.scrollY - tracksH / 2, 0, Math.max(0, contentH - tracksH)); dirty = true; }
  status(`off-grid hit ${h.t.toFixed(3)} (${h.dt >= 0 ? "+" : ""}${Math.round(h.dt * 1000)} ms) in ${h.item.id}`);
}
const keys = {
  " ": () => clock.toggle(),
  ArrowRight: e => step(e.shiftKey ? D : B, 1),
  ArrowLeft: e => step(e.shiftKey ? D : B, -1),
  ",": () => { clock.pause(); clock.seek(clock.t() - 1 / fps()); },
  ".": () => { clock.pause(); clock.seek(clock.t() + 1 / fps()); },
  f: () => fit(),
  "=": () => zoomAt(1.5, X(clock.t())), "+": () => zoomAt(1.5, X(clock.t())),
  "-": () => zoomAt(1 / 1.5, X(clock.t())),
  n: e => nextOff(e.shiftKey ? -1 : 1),
  Home: () => clock.seek(R0), End: () => clock.seek(R1),
  Escape: () => { selId = null; showInspector(); },
};
addEventListener("keydown", e => {
  if (e.target.tagName === "INPUT" && e.target.type === "text") return;
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
  if (!keys[k]) return;
  // claim the key, or Firefox's type-to-search (and focused buttons on Space) also act on it
  e.preventDefault();
  e.stopPropagation();
  keys[k](e);
}, true);

$("play").onclick = () => clock.toggle();
$("fit").onclick = () => fit();
$("nextoff").onclick = () => nextOff(1);
for (const el of document.querySelectorAll("#bar button, #bar input")) el.addEventListener("mousedown", e => e.preventDefault());
for (const el of document.querySelectorAll("#bar select, #bar input")) el.addEventListener("change", () => el.blur());

// ---------- frame loop ----------
function frame() {
  if (clock.playing() && $("follow").checked && !drag) {
    const t = clock.t(), vis = trackW() / view.pps;
    if (t > view.t0 + vis * 0.95 || t < view.t0) { view.t0 = t - vis * 0.05; clampView(); }
  }
  if (!videoOK) $("play").textContent = vClock.playing ? "❚❚" : "▶";
  if (dirty) { drawBase(); lastOver = ""; }
  drawOver();
  requestAnimationFrame(frame);
}

applyTimeline(TL);
new ResizeObserver(() => { resize(); }).observe(wrap);
resize();
fit();
loadVideo(await videoSig());
clock.seek(R0);
status(`${(TL.layers || []).length} layers · ${allHits.length} hits`);
requestAnimationFrame(frame);
setTimeout(poll, 1500);
window.__tlv = { get view() { return view; }, get groups() { return groups; }, clock, video, get videoOK() { return videoOK; }, select: id => { selId = id; showInspector(); },
  setView: (t0, pps) => { view.t0 = t0; view.pps = pps; clampView(); } };
