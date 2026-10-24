// Turn the preacher's own head motion (media/derived/face_track.json) into a layer path.
//
// usage: node tools/selfmotion.mjs [--project meine] [--mode amplify|drift] [--gain G]
//                                  [--smooth FRAMES] [--tol PX] [--out paths/NAME.json]
//
//   amplify  his offset from his average position, scaled by G, soft-clamped to the picture
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
} else throw new Error(`unknown --mode ${opt.mode}`);

const samples = pos.map((p, i) => ({ t: +(layer.start + i / track.fps).toFixed(4), p: [+p[0].toFixed(1), +p[1].toFixed(1)] }));
const anchors = fitSamples(samples, +opt.tol);
const out = opt.out ?? `paths/face_self_${opt.mode}.json`;
const params = { mode: opt.mode, gain, smooth: sw, tol: +opt.tol };
writeFileSync(join(pdir, out), JSON.stringify({
  anchors,
  takes: [{ t0: samples[0].t, t1: samples[samples.length - 1].t, source: "selfmotion", params, samples }],
}, null, 1) + "\n");
const xs = pos.map(p => p[0]), ys = pos.map(p => p[1]);
console.error(`${out}: ${anchors.length} anchors; x ${Math.min(...xs).toFixed(0)}..${Math.max(...xs).toFixed(0)}, y ${Math.min(...ys).toFixed(0)}..${Math.max(...ys).toFixed(0)}`);
