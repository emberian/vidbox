// Turn the preacher's own head motion (media/derived/face_track.json) into a layer path.
//
// usage: node tools/selfmotion.mjs [--project meine] [--mode amplify|hybrid|gaze|drift] [--gain G]
//                                  [--smooth FRAMES] [--tol PX] [--out paths/NAME.json]
//   --sync sync/NAME.resolved.json  follow a retimed rant (tools/retime.py): his motion is
//                                   read at clip time and placed at the retimed song time
//   hybrid extras: [--base G] [--every BARS] [--pct SPEED_PERCENTILE] [--hbias H]
//
//   amplify  his offset from his average position, scaled by G, soft-clamped to the picture
//   hybrid   amplify, plus beat-timed hops: launched on downbeats when his head moves hard,
//            hitting a picture edge exactly on a beat, ricocheting, skidding to rest
//   gaze     he travels where he's looking (head turn/tilt + eyes, from face_pose.json),
//            accelerating while he keeps looking; eye contact makes him grow
//            extras: [--gain ACCEL] [--drag D] [--dead ZONE] [--zone EYE_CONTACT_ZONE]
//                    [--grow G] [--shrink S] [--smax MAX]
//   drift    his frame-to-frame velocity pushes the head (G = push strength); it coasts with
//            damping, a faint spring toward center, and bounces off the picture edges
//
// The result is fitted with the studio's own fitter, so it opens and edits like a capture.
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { fitSamples } from "../studio/bezier.js";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const opt = { project: "meine", mode: "amplify", smooth: 5, tol: 5 };
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i += 2) opt[argv[i].replace(/^--/, "")] = argv[i + 1];
const gain = +(opt.gain ?? (opt.mode === "drift" ? 1.6 : 4));

const pdir = join(ROOT, "projects", opt.project);
const project = JSON.parse(readFileSync(join(pdir, "project.json")));
const layer = project.layers.find(l => l.id === "face");
const track = JSON.parse(readFileSync(join(ROOT, "media/derived/face_track.json")));
const [W] = project.size;
const [FW, FH] = layer.size;
// picture area inside the letterbox (see analysis/STRUCTURE.md)
const pic = { x0: 0, x1: W, y0: 158, y1: 922 };
const center = [(pic.x0 + pic.x1) / 2, (pic.y0 + pic.y1) / 2];
// how far the head's center may roam: keep most of the oval on the picture
const reach = [(pic.x1 - pic.x0) / 2 - FW * 0.3, (pic.y1 - pic.y0) / 2 - FH * 0.3];

// --- clean the track: drop detections that aren't his face, fill gaps, smooth ---
const F = track.frames, n = F.length;
const median = a => { const s = [...a].sort((x, y) => x - y); return s[s.length >> 1]; };
const fs = median(F.filter(Boolean).map(d => d[2]));
const ok = F.map(d => d && d[2] > fs * 0.7 && d[2] < fs * 1.4);
for (let i = 0; i < n; i++) {   // also reject jumps far from the local median
  if (!ok[i]) continue;
  const win = [];
  for (let j = Math.max(0, i - 7); j <= Math.min(n - 1, i + 7); j++) if (ok[j]) win.push(F[j]);
  const mx = median(win.map(d => d[0])), my = median(win.map(d => d[1]));
  if (Math.hypot(F[i][0] - mx, F[i][1] - my) > fs * 0.35) ok[i] = false;
}
const good = [...Array(n).keys()].filter(i => ok[i]);
const fill = k => Array.from({ length: n }, (_, i) => {
  let a = good.findLast(g => g <= i), b = good.find(g => g >= i);
  if (a === undefined) return F[b][k];
  if (b === undefined || a === b) return F[a][k];
  return F[a][k] + (F[b][k] - F[a][k]) * (i - a) / (b - a);
});
const smooth = (xs, w) => xs.map((_, i) => {
  let s = 0, c = 0;
  for (let j = Math.max(0, i - w); j <= Math.min(n - 1, i + w); j++) { s += xs[j]; c++; }
  return s / c;
});
const sw = +opt.smooth;
const fx = smooth(fill(0), sw), fy = smooth(fill(1), sw);
console.error(`track: ${n} frames, kept ${good.length} detections, face ~${fs}px`);

// --- clip time -> song time: 1:1 from layer.start, or through a retime sync sheet's map ---
const interp = (x, xs, ys) => {
  if (x <= xs[0]) return ys[0] + (x - xs[0]);
  if (x >= xs[xs.length - 1]) return ys[ys.length - 1] + (x - xs[xs.length - 1]);
  let i = 0;
  while (xs[i + 1] < x) i++;
  return ys[i] + (ys[i + 1] - ys[i]) * (x - xs[i]) / (xs[i + 1] - xs[i]);
};
const tmap = opt.sync && JSON.parse(readFileSync(join(pdir, opt.sync))).map;
const songT = i => (tmap ? interp(i / track.fps, tmap.src, tmap.song) : layer.start + i / track.fps);
const frameAt = t => Math.round((tmap ? interp(t, tmap.song, tmap.src) : t - layer.start) * track.fps);

// --- motion model ---
const pos = [];
if (opt.mode === "amplify") {
  const mx = fx.reduce((a, b) => a + b) / n, my = fy.reduce((a, b) => a + b) / n;
  // tanh soft-clamp: linear for small motion, eases to the edge instead of hitting it
  const soft = (d, r) => r * Math.tanh(d / r);
  for (let i = 0; i < n; i++)
    pos.push([center[0] + soft(gain * (fx[i] - mx), reach[0]), center[1] + soft(gain * (fy[i] - my), reach[1])]);
} else if (opt.mode === "drift") {
  const damp = +(opt.damp ?? 0.94), spring = +(opt.spring ?? 0.0015), bounce = 0.85;
  let p = center.slice(), v = [0, 0];
  for (let i = 0; i < n; i++) {
    const dv = i ? [fx[i] - fx[i - 1], fy[i] - fy[i - 1]] : [0, 0];
    for (const k of [0, 1]) {
      v[k] = v[k] * damp + gain * dv[k] - spring * (p[k] - center[k]);
      p[k] += v[k];
      const lo = center[k] - reach[k], hi = center[k] + reach[k];
      if (p[k] < lo) { p[k] = 2 * lo - p[k]; v[k] = -v[k] * bounce; }
      if (p[k] > hi) { p[k] = 2 * hi - p[k]; v[k] = -v[k] * bounce; }
    }
    pos.push(p.slice());
  }
} else if (opt.mode === "hybrid") {
  // amplify as a base wiggle, plus "hops": on downbeats where his own head is moving hard,
  // he's launched the way he was moving, flies at constant speed into a picture edge that
  // he hits exactly on the next beat (or the one after), ricochets, and skids to rest by
  // the following beat. He supplies the impulse; the music supplies the timing.
  const beats = JSON.parse(readFileSync(join(pdir, "analysis/beats.json")));
  const bgain = +(opt.base ?? 2.5), every = +(opt.every ?? 2), pct = +(opt.pct ?? 60), hb = +(opt.hbias ?? 1.6);
  const tOf = songT, iOf = frameAt;
  const mx = fx.reduce((a, b) => a + b) / n, my = fy.reduce((a, b) => a + b) / n;
  const vel = i => { const a = Math.max(0, i - 3), b = Math.min(n - 1, i + 3); return [(fx[b] - fx[a]) / (b - a), (fy[b] - fy[a]) / (b - a)]; };
  const speeds = fx.map((_, i) => Math.hypot(...vel(i)));
  const thresh = [...speeds].sort((a, b) => a - b)[Math.floor(n * pct / 100)];
  const lim = [reach[0] * 0.85, reach[1] * 0.85];
  const bar = beats.downbeats[1] - beats.downbeats[0], beat = bar / 4;
  const end = tOf(n - 1);

  const hops = [];
  let home = [0, 0], lastBar = -Infinity;
  beats.downbeats.forEach((tb, bi) => {
    if (tb < tOf(0) + 0.5 || tb > end - 3 * beat || bi - lastBar < every) return;
    const v = vel(iOf(tb));
    if (Math.hypot(...v) < thresh) return;
    let d = [v[0] * hb, v[1]];
    d = [d[0] / Math.hypot(...d), d[1] / Math.hypot(...d)];
    // distance along d to the first wall of the home-offset box
    const s = Math.min(...[0, 1].map(k => d[k] > 1e-6 ? (lim[k] - home[k]) / d[k] : d[k] < -1e-6 ? (-lim[k] - home[k]) / d[k] : Infinity));
    const wallAxis = [0, 1].find(k => Math.abs(home[k] + d[k] * s) >= lim[k] - 1e-6);
    const nb = s < 250 ? 1 : 2;    // short flights land on the next beat, long ones on the one after
    const pW = [home[0] + d[0] * s, home[1] + d[1] * s];
    const r = d.slice(); r[wallAxis] = -r[wallAxis];
    const speed = s / (nb * beat);
    // skid out over one beat with ease-out from the same speed: distance = speed * beat / 2
    let pE = [pW[0] + r[0] * speed * beat / 2, pW[1] + r[1] * speed * beat / 2];
    pE = pE.map((x, k) => Math.max(-lim[k], Math.min(lim[k], x)));
    hops.push({ tA: tb, tW: tb + nb * beat, tE: tb + (nb + 1) * beat, pA: home, pW, pE });
    home = pE; lastBar = bi;
  });
  const homeAt = t => {
    let h = [0, 0];
    for (const o of hops) {
      if (t < o.tA) break;
      if (t < o.tW) { const u = (t - o.tA) / (o.tW - o.tA); return o.pA.map((x, k) => x + (o.pW[k] - x) * u); }
      if (t < o.tE) { const u = (t - o.tW) / (o.tE - o.tW), e = 1 - (1 - u) ** 2; return o.pW.map((x, k) => x + (o.pE[k] - x) * e); }
      h = o.pE;
    }
    return h;
  };
  // the wiggle fades out mid-flight so the wall contact lands clean
  const wiggleAt = t => { for (const o of hops) if (t > o.tA - beat / 2 && t < o.tE) return 0.25; return 1; };
  for (let i = 0; i < n; i++) {
    const t = tOf(i), h = homeAt(t), w = wiggleAt(t);
    pos.push([0, 1].map(k => {
      const p = center[k] + h[k] + w * bgain * ((k ? fy : fx)[i] - (k ? my : mx));
      return Math.max(center[k] - reach[k], Math.min(center[k] + reach[k], p));
    }));
  }
  opt.corners = hops.flatMap(o => [o.tA, o.tW]);
  console.error(`hybrid: ${hops.length} hops on downbeats ${hops.map(o => o.tA.toFixed(2)).join(" ")}; walls hit at ${hops.map(o => o.tW.toFixed(2)).join(" ")}`);
} else if (opt.mode === "gaze") {
  // He goes where he's looking. Head turn/tilt (plus a little of his eyes) away from his
  // resting "talking to camera" pose is a push in that direction; he gathers speed while he
  // keeps looking that way, coasts with drag, and bounces off the picture edges. Looking
  // straight at you he slows and grows; looking away, he shrinks back to normal size.
  const pose = JSON.parse(readFileSync(join(ROOT, "media/derived/face_pose.json")));
  const accel = +(opt.gain ?? 1400), drag = +(opt.drag ?? 1.6), dead = +(opt.dead ?? 0.25);
  const grow = +(opt.grow ?? 2.2), shrink = +(opt.shrink ?? 0.7), smax = +(opt.smax ?? 1.9), zone = +(opt.zone ?? 0.4);
  const dt = 1 / pose.fps;
  const P = pose.frames;
  const ch = k => {   // a pose channel with gaps filled and light smoothing
    const ok = [...P.keys()].filter(i => P[i]);
    const raw = P.map((f, i) => {
      if (f) return f[k];
      const a = ok.findLast(g => g < i), b = ok.find(g => g > i);
      return a === undefined ? P[b][k] : b === undefined ? P[a][k] : P[a][k] + (P[b][k] - P[a][k]) * (i - a) / (b - a);
    });
    return smooth(raw, 2);
  };
  const yaw = ch("yaw"), pitch = ch("pitch"), gh = ch("gaze_h");
  const y0 = median(yaw), p0 = median(pitch), g0 = median(gh);
  // normalize so ~1 = a clear look in that direction (+x screen-right, +y screen-down)
  const dirX = yaw.map((v, i) => (v - y0) / 15 + 0.5 * (gh[i] - g0) / 0.1);
  const dirY = pitch.map(v => (v - p0) / 9);

  let p = center.slice(), v = [0, 0], s = 1;
  const scale = [];
  for (let i = 0; i < n; i++) {
    const d = [dirX[i], dirY[i]], m = Math.hypot(...d);
    // past the dead zone, push along the look direction, harder the further he turns
    const push = m > dead ? (m - dead) / m : 0;
    const look = Math.exp(-((m / zone) ** 2));   // 1 = dead on at you
    for (const k of [0, 1]) {
      v[k] += (accel * d[k] * push - drag * v[k]) * dt;
      p[k] += v[k] * dt;
    }
    s += (look > 0.45 ? grow * look * (smax - s) : -shrink * (1 - look) * (s - 1)) * dt;
    for (const k of [0, 1]) {   // walls shrink as he grows, so the oval stays in the picture
      const r = reach[k] - (k ? FH : FW) * 0.3 * (s - 1);
      if (p[k] < center[k] - r) { p[k] = 2 * (center[k] - r) - p[k]; v[k] = -v[k] * 0.8; }
      if (p[k] > center[k] + r) { p[k] = 2 * (center[k] + r) - p[k]; v[k] = -v[k] * 0.8; }
    }
    pos.push(p.slice());
    scale.push(+s.toFixed(4));
  }
  // resample to a uniform grid in song time (a retime map makes clip frames uneven)
  const sdt = 0.04, t0 = songT(0), nS = Math.floor((songT(n - 1) - t0) / sdt) + 1;
  opt.scale = { t0, dt: sdt, values: Array.from({ length: nS }, (_, j) => {
    const f = Math.min(n - 1, Math.max(0, frameAt(t0 + j * sdt)));
    return scale[f];
  }) };
  const big = scale.filter(x => x > 1.3).length / n;
  console.error(`gaze: scale 1..${Math.max(...scale).toFixed(2)}, ${(big * 100).toFixed(0)}% of the time above 1.3x`);
} else throw new Error(`unknown --mode ${opt.mode}`);

const samples = pos.map((p, i) => ({ t: +songT(i).toFixed(4), p: [+p[0].toFixed(1), +p[1].toFixed(1)] }));
const anchors = fitSamples(samples, +opt.tol, opt.corners ?? []);
const out = opt.out ?? `paths/face_self_${opt.mode}.json`;
const params = { mode: opt.mode, gain, smooth: sw, tol: +opt.tol };
writeFileSync(join(pdir, out), JSON.stringify({
  anchors,
  ...(opt.scale && { scale: opt.scale }),
  takes: [{ t0: samples[0].t, t1: samples[samples.length - 1].t, source: "selfmotion", params, samples }],
}, null, 1) + "\n");
const xs = pos.map(p => p[0]), ys = pos.map(p => p[1]);
console.error(`${out}: ${anchors.length} anchors; x ${Math.min(...xs).toFixed(0)}..${Math.max(...xs).toFixed(0)}, y ${Math.min(...ys).toFixed(0)}..${Math.max(...ys).toFixed(0)}`);
