import { evalPath, evalScale, fitSamples, smoothAnchor, splitAt, splice } from "./bezier.js";

const $ = id => document.getElementById(id);
const stage = $("stage"), ctx = stage.getContext("2d");
const tl = $("timeline"), tctx = tl.getContext("2d");
const bg = $("bg"), face = $("face");

const projName = new URLSearchParams(location.search).get("project") || "meine";
const projDir = `/projects/${projName}`;
const project = await (await fetch(`${projDir}/project.json`)).json();
const layer = project.layers.find(l => l.path);
const [W, H] = project.size;
const fps = project.fps;
let pathFile, path;

bg.src = "/" + (project.background.proxy || project.background.src);
face.src = "/" + layer.src;

// ---------- state ----------
let mode = "edit";
let showOverlay = true;
let sel = -1;
let drag = null;              // {kind: 'anchor'|'hin'|'hout'|'tick'|'scrub', i, ...}
let take = null;              // samples while recording
let clock = null;             // capture clock: pointer timestamps -> media time
let mouse = [W / 2, H / 2];
let undo = [], redo = [];

// The layer renders with whichever path file it points at; switching here repoints it.
async function loadPath(rel) {
  layer.path = rel;
  pathFile = `projects/${projName}/${rel}`;
  path = { anchors: [], takes: [] };
  try {
    const r = await fetch(`/${pathFile}`);
    if (r.ok) path = Object.assign(path, await r.json());
  } catch {}
  sel = -1;
  undo = [JSON.stringify(path)];
  redo = [];
}
await loadPath(layer.path);
{
  const names = await (await fetch(`/api/ls?dir=projects/${projName}/paths`)).json();
  const cur = layer.path.replace(/^paths\//, "");
  if (!names.includes(cur)) names.unshift(cur);
  $("pathsel").innerHTML = names.map(n => `<option${n === cur ? " selected" : ""}>${n}</option>`).join("");
  $("pathsel").onchange = async () => {
    await loadPath("paths/" + $("pathsel").value);
    scheduleSave();
  };
}

const status = msg => { $("status").textContent = msg; };

// ---------- persistence ----------
let saveTimer = null;
async function post(file, data) {
  const r = await fetch(`/api/save?path=${encodeURIComponent(file)}`, { method: "POST", body: JSON.stringify(data) });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
}
function scheduleSave() {
  clearTimeout(saveTimer);
  status("unsaved");
  saveTimer = setTimeout(async () => {
    try {
      await post(pathFile, path);
      await post(`projects/${projName}/project.json`, project);
      status(`saved ${path.anchors.length} anchors · ${path.takes.length} takes`);
    } catch (e) { status("SAVE FAILED: " + e.message); }
  }, 300);
}
function commit() {
  undo.push(JSON.stringify(path));
  if (undo.length > 200) undo.shift();
  redo = [];
  scheduleSave();
}
function restore(s) { path = JSON.parse(s); sel = Math.min(sel, path.anchors.length - 1); scheduleSave(); }

// ---------- geometry ----------
let scale = 1;
function layout() {
  const wrap = $("wrap"), dpr = devicePixelRatio || 1;
  const avail = [wrap.clientWidth - 16, wrap.clientHeight - 16];
  const cssW = Math.max(100, Math.min(avail[0], avail[1] * W / H));
  stage.style.width = cssW + "px";
  stage.style.height = cssW * H / W + "px";
  stage.width = Math.round(cssW * dpr);
  stage.height = Math.round(cssW * H / W * dpr);
  scale = stage.width / W;
  tl.width = tl.clientWidth * dpr;
  tl.height = tl.clientHeight * dpr;
}
addEventListener("resize", layout);
layout();

const toProj = e => {
  const r = stage.getBoundingClientRect();
  return [(e.clientX - r.left) / r.width * W, (e.clientY - r.top) / r.height * H];
};
const now = () => bg.currentTime;
const add = (a, b) => [a[0] + b[0], a[1] + b[1]];

// ---------- face mask (same formula as the renderer) ----------
const [FW, FH] = layer.size;
const faceBuf = new OffscreenCanvas(FW, FH), fctx = faceBuf.getContext("2d");
const maskCanvas = new OffscreenCanvas(FW, FH);
{
  const m = maskCanvas.getContext("2d"), img = m.createImageData(FW, FH);
  const feather = layer.mask.feather;
  for (let y = 0; y < FH; y++) for (let x = 0; x < FW; x++) {
    const r = Math.hypot((x + 0.5 - FW / 2) / (FW / 2), (y + 0.5 - FH / 2) / (FH / 2));
    const a = Math.min(1, Math.max(0, (1 - r) / feather));
    img.data[(y * FW + x) * 4 + 3] = Math.round(a * 255);
  }
  m.putImageData(img, 0, 0);
}

// ---------- playback ----------
function setRate(r) {
  $("rate").value = String(r);
  bg.playbackRate = face.playbackRate = r;
}
function play() { bg.playbackRate = face.playbackRate = +$("rate").value; bg.play().catch(() => {}); }  // rejects if paused before it starts
function pause() { bg.pause(); face.pause(); }
function seek(t) { bg.currentTime = Math.max(0, Math.min(t, bg.duration || t)); }

function syncFace() {
  const local = now() - layer.start;
  const inside = local >= 0 && local < (face.duration || 0);
  face.volume = Math.min(1, layer.gain);
  bg.volume = Math.min(1, project.background.gain);
  if (!bg.paused && inside) {
    if (face.paused) { face.currentTime = local; face.play().catch(() => {}); }
    else if (Math.abs(face.currentTime - local) > 0.12) face.currentTime = local;
  } else {
    if (!face.paused) face.pause();
    if (inside && !face.seeking && Math.abs(face.currentTime - local) > 0.03) face.currentTime = local;
  }
  return inside;
}

// ---------- drawing ----------
function handleVisible(i) {
  return i === sel || Math.abs(path.anchors[i].t - now()) < 2;
}

function draw() {
  const faceOn = syncFace();
  // pointer events only arrive on movement; keep sampling while the hand holds still
  if (take && clock) record(performance.now(), mouse, 0.04);

  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, stage.width, stage.height);
  ctx.setTransform(scale, 0, 0, scale, 0, 0);
  if (bg.readyState >= 2) ctx.drawImage(bg, 0, 0, W, H);

  const pos = take ? mouse : evalPath(path, now());
  if (faceOn && pos && face.readyState >= 2) {
    fctx.globalCompositeOperation = "source-over";
    fctx.drawImage(face, 0, 0, FW, FH);
    fctx.globalCompositeOperation = "destination-in";
    fctx.drawImage(maskCanvas, 0, 0);
    ctx.globalAlpha = layer.opacity;
    const sc = take ? 1 : evalScale(path, now());
    ctx.drawImage(faceBuf, pos[0] - FW * sc / 2, pos[1] - FH * sc / 2, FW * sc, FH * sc);
    ctx.globalAlpha = 1;
  }

  if (showOverlay) drawOverlay(pos);
  drawTimeline();
  $("time").textContent = now().toFixed(2) + (take ? "  ● REC" : "");
  $("play").textContent = bg.paused ? "▶" : "❚❚";
  requestAnimationFrame(draw);
}

function drawOverlay(pos) {
  const A = path.anchors, px = 1 / scale;
  ctx.lineWidth = 1.5 * px;
  if (A.length > 1) {
    const t0 = A[0].t, t1 = A[A.length - 1].t, t = now();
    ctx.beginPath();
    for (let s = t0; s <= t1 + 1e-9; s += 1 / fps) { const q = evalPath(path, s); s === t0 ? ctx.moveTo(...q) : ctx.lineTo(...q); }
    ctx.strokeStyle = "rgba(255,255,255,0.25)";
    ctx.stroke();
    ctx.beginPath();
    const a = Math.max(t0, t - 1.5), b = Math.min(t1, t + 1.5);
    for (let s = a; s <= b; s += 1 / fps / 2) { const q = evalPath(path, s); s === a ? ctx.moveTo(...q) : ctx.lineTo(...q); }
    ctx.strokeStyle = "rgba(255,106,61,0.9)";
    ctx.stroke();
  }
  A.forEach((a, i) => {
    if (handleVisible(i)) {
      for (const h of [a.hin, a.hout]) {
        if (!h[0] && !h[1]) continue;
        const q = add(a.p, h);
        ctx.beginPath(); ctx.moveTo(...a.p); ctx.lineTo(...q);
        ctx.strokeStyle = "rgba(120,200,255,0.7)"; ctx.stroke();
        ctx.beginPath(); ctx.arc(q[0], q[1], 4 * px, 0, 7);
        ctx.fillStyle = "#78c8ff"; ctx.fill();
      }
    }
    const s = (i === sel ? 6 : 4) * px;
    ctx.fillStyle = i === sel ? "#ff6a3d" : "#fff";
    ctx.fillRect(a.p[0] - s, a.p[1] - s, 2 * s, 2 * s);
  });
  if (take && take.length > 1) {
    ctx.beginPath();
    take.forEach((s, i) => (i ? ctx.lineTo(...s.p) : ctx.moveTo(...s.p)));
    ctx.strokeStyle = "rgba(255,45,85,0.9)"; ctx.lineWidth = 2 * px; ctx.stroke();
  }
  if (pos) {
    ctx.beginPath(); ctx.arc(pos[0], pos[1], 5 * px, 0, 7);
    ctx.strokeStyle = "#ff6a3d"; ctx.lineWidth = 2 * px; ctx.stroke();
  }
}

const tlDur = () => project.duration || bg.duration || 60;
const tlX = t => t / tlDur() * tl.width;
const tlT = e => { const r = tl.getBoundingClientRect(); return (e.clientX - r.left) / r.width * tlDur(); };

function drawTimeline() {
  const w = tl.width, h = tl.height, dpr = devicePixelRatio || 1;
  tctx.clearRect(0, 0, w, h);
  tctx.fillStyle = "#26262a";
  for (let s = 0; s <= tlDur(); s++) tctx.fillRect(tlX(s), 0, 1, s % 5 ? 6 * dpr : 12 * dpr);
  tctx.fillStyle = "#666"; tctx.font = `${10 * dpr}px ui-monospace, monospace`;
  for (let s = 0; s <= tlDur(); s += 5) tctx.fillText(String(s), tlX(s) + 3, 12 * dpr);
  if (face.duration) {   // the face clip's span
    tctx.fillStyle = "rgba(120,200,255,0.18)";
    tctx.fillRect(tlX(layer.start), 18 * dpr, tlX(layer.start + face.duration) - tlX(layer.start), 10 * dpr);
  }
  tctx.fillStyle = "rgba(255,45,85,0.5)";
  for (const k of path.takes) tctx.fillRect(tlX(k.t0), 32 * dpr, Math.max(1, tlX(k.t1) - tlX(k.t0)), 3 * dpr);
  path.anchors.forEach((a, i) => {
    tctx.fillStyle = i === sel ? "#ff6a3d" : "#ddd";
    tctx.fillRect(tlX(a.t) - 2 * dpr, 40 * dpr, 4 * dpr, 16 * dpr);
  });
  tctx.fillStyle = "#ff6a3d";
  tctx.fillRect(tlX(now()) - dpr, 0, 2 * dpr, h);
}

// ---------- stage interaction ----------
function hitTest(q) {
  const r = 9 / scale * (devicePixelRatio || 1), A = path.anchors;
  const near = p => Math.hypot(p[0] - q[0], p[1] - q[1]) < r;
  for (let i = A.length - 1; i >= 0; i--) {
    if (!handleVisible(i)) continue;
    if ((A[i].hin[0] || A[i].hin[1]) && near(add(A[i].p, A[i].hin))) return { kind: "hin", i };
    if ((A[i].hout[0] || A[i].hout[1]) && near(add(A[i].p, A[i].hout))) return { kind: "hout", i };
  }
  for (let i = A.length - 1; i >= 0; i--) if (near(A[i].p)) return { kind: "anchor", i };
  return null;
}

// video.currentTime advances in coarse steps, so samples are stamped from the pointer
// events' own high-res timestamps, anchored to the media time when playback began.
function record(ts, p, minGap = 1e-4) {
  const t = clock.t0 + (ts - clock.ts0) / 1000 * clock.rate, last = take[take.length - 1];
  if (t > last.t + minGap) take.push({ t, p: p.slice() });
}

stage.addEventListener("pointermove", e => {
  mouse = toProj(e);
  if (take) {
    if (clock) for (const ev of e.getCoalescedEvents?.() ?? [e]) record(ev.timeStamp, toProj(ev));
    return;
  }
  if (!drag) return;
  const a = path.anchors[drag.i];
  if (drag.kind === "anchor") a.p = [drag.p0[0] + mouse[0] - drag.m0[0], drag.p0[1] + mouse[1] - drag.m0[1]];
  else {
    a[drag.kind] = [mouse[0] - a.p[0], mouse[1] - a.p[1]];
    if (!e.altKey) smoothAnchor(path.anchors, drag.i, drag.kind === "hin" ? "in" : "out");
  }
  drag.moved = true;
});

stage.addEventListener("pointerdown", e => {
  stage.setPointerCapture(e.pointerId);
  mouse = toProj(e);
  if (mode === "capture") {
    take = [{ t: now(), p: mouse.slice() }];
    clock = null;
    const startClock = () => { if (take) clock = { ts0: performance.now(), t0: bg.currentTime, rate: bg.playbackRate }; };
    if (!bg.paused && bg.readyState >= 3) startClock();   // already playing: no "playing" event will come
    else bg.addEventListener("playing", startClock, { once: true });
    play();
    return;
  }
  const hit = hitTest(mouse);
  if (hit) {
    sel = hit.i;
    drag = { ...hit, p0: path.anchors[hit.i].p.slice(), m0: mouse.slice() };
  } else sel = -1;
});

stage.addEventListener("pointerup", () => {
  if (take) {
    pause();
    const S = take; take = null; clock = null;
    if (S.length >= 2 && S[S.length - 1].t - S[0].t > 0.05) {
      const anchors = fitSamples(S, +$("tol").value);
      splice(path, anchors);
      path.takes.push({
        t0: S[0].t, t1: S[S.length - 1].t,
        samples: S.map(s => ({ t: +s.t.toFixed(4), p: [+s.p[0].toFixed(1), +s.p[1].toFixed(1)] })),
      });
      sel = -1;
      commit();
      status(`take ${S.length} samples → ${anchors.length} anchors`);
    }
    return;
  }
  if (drag?.moved) commit();
  drag = null;
});

stage.addEventListener("dblclick", e => {
  if (mode !== "edit") return;
  const q = toProj(e), t = now(), A = path.anchors;
  let i = splitAt(path, t);
  if (i < 0) {
    if (A.some(a => Math.abs(a.t - t) < 1e-3)) return;
    A.push({ t, p: q, hin: [0, 0], hout: [0, 0] });
    A.sort((a, b) => a.t - b.t);
    i = A.findIndex(a => a.t === t);
  } else A[i].p = q;
  sel = i;
  commit();
});

// ---------- timeline interaction ----------
tl.addEventListener("pointerdown", e => {
  tl.setPointerCapture(e.pointerId);
  const t = tlT(e), dpr = devicePixelRatio || 1, A = path.anchors;
  const y = (e.clientY - tl.getBoundingClientRect().top) * dpr;
  const i = y > 36 * dpr ? A.findIndex(a => Math.abs(tlX(a.t) - tlX(t)) < 5 * dpr) : -1;
  if (i >= 0) { sel = i; drag = { kind: "tick", i }; }
  else { drag = { kind: "scrub" }; seek(t); }
});
tl.addEventListener("pointermove", e => {
  if (!drag) return;
  const t = tlT(e), A = path.anchors;
  if (drag.kind === "scrub") return seek(t);
  const lo = drag.i > 0 ? A[drag.i - 1].t + 0.02 : 0;
  const hi = drag.i < A.length - 1 ? A[drag.i + 1].t - 0.02 : tlDur();
  A[drag.i].t = Math.max(lo, Math.min(hi, t));
  drag.moved = true;
});
tl.addEventListener("pointerup", () => { if (drag?.moved) commit(); drag = null; });

// ---------- toolbar ----------
function setMode(m) {
  mode = m;
  $("mode").textContent = m === "capture" ? "● CAPTURE" : "EDIT";
  $("mode").classList.toggle("capture", m === "capture");
  stage.classList.toggle("capture", m === "capture");
}
$("mode").onclick = () => setMode(mode === "edit" ? "capture" : "edit");
$("play").onclick = () => (bg.paused ? play() : pause());
$("rate").onchange = () => setRate(+$("rate").value);
$("tol").oninput = () => { $("tolv").textContent = $("tol").value; };
$("refit").onclick = () => {
  const k = path.takes[path.takes.length - 1];
  if (!k) return status("no takes yet");
  const anchors = fitSamples(k.samples, +$("tol").value);
  splice(path, anchors);
  commit();
  status(`refit → ${anchors.length} anchors`);
};
for (const [id, get, set] of [
  ["opacity", () => layer.opacity, v => (layer.opacity = v)],
  ["gbg", () => project.background.gain, v => (project.background.gain = v)],
  ["gvoice", () => layer.gain, v => (layer.gain = v)],
]) {
  $(id).value = get();
  $(id).oninput = () => { set(+$(id).value); scheduleSave(); };
}

const rates = [0.25, 0.5, 0.75, 1];
const keys = {
  " ": () => (bg.paused ? play() : pause()),
  c: () => setMode(mode === "edit" ? "capture" : "edit"),
  h: () => { showOverlay = !showOverlay; },
  ",": () => { pause(); seek(now() - 1 / fps); },
  ".": () => { pause(); seek(now() + 1 / fps); },
  ArrowLeft: () => seek(now() - 1),
  ArrowRight: () => seek(now() + 1),
  Home: () => seek(0),
  "[": () => setRate(rates[Math.max(0, rates.indexOf(+$("rate").value) - 1)]),
  "]": () => setRate(rates[Math.min(rates.length - 1, rates.indexOf(+$("rate").value) + 1)]),
  Backspace: () => { if (sel >= 0) { path.anchors.splice(sel, 1); sel = -1; commit(); } },
  a: () => { const i = splitAt(path, now()); if (i >= 0) { sel = i; commit(); } },
  s: () => { if (sel >= 0) { smoothAnchor(path.anchors, sel); commit(); } },
};
keys.Delete = keys.Backspace;

addEventListener("keydown", e => {
  if (e.target.tagName === "INPUT" && e.target.type !== "range") return;
  const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
  if (e.metaKey || e.ctrlKey) {
    if (k !== "z") return;
    e.preventDefault();
    if (e.shiftKey) { if (redo.length) { undo.push(redo.pop()); restore(undo[undo.length - 1]); } }
    else if (undo.length > 1) { redo.push(undo.pop()); restore(undo[undo.length - 1]); }
    return;
  }
  if (e.altKey || !keys[k]) return;
  // claim the key, or Firefox's type-to-search (and focused buttons on Space) also act on it
  e.preventDefault();
  keys[k]();
});

// Toolbar controls shouldn't keep keyboard focus: a focused button would also fire on
// Space, and a focused <select> or slider would eat the arrow keys.
for (const el of document.querySelectorAll("#bar button")) el.addEventListener("mousedown", e => e.preventDefault());
for (const el of document.querySelectorAll("#bar select, #bar input")) el.addEventListener("change", () => el.blur());

status(`${path.anchors.length} anchors · ${path.takes.length} takes`);
requestAnimationFrame(draw);
window.__studio = { get path() { return path; }, bg, face };  // for automated checks
