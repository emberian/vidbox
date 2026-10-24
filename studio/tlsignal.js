// Scalar signal evaluation for the timeline viewer (TIMELINE.md "Signals"). The viewer uses it to
// draw a layer's opacity envelope; it returns null for forms it can't evaluate as a number
// (vectors, Bezier paths), and the caller treats those as "unknown".

const ub = (a, x) => { let lo = 0, hi = a.length; while (lo < hi) { const m = (lo + hi) >> 1; if (a[m] <= x) lo = m + 1; else hi = m; } return lo; };

// music: {beats, downbeats, onsets: [[t, s]], intensity: {dt, values}}
export function makeEval(music) {
  const B = music.beats, D = music.downbeats;
  const onT = music.onsets.map(o => o[0]), onS = music.onsets.map(o => o[1]);
  const I = music.intensity;
  // beat index of the first downbeat, so that beat-signal phase 0 lands on downbeats
  const d0 = D.length ? Math.max(0, ub(B, D[0] + 0.03) - 1) : 0;
  const meanBeat = B.length > 1 ? (B[B.length - 1] - B[0]) / (B.length - 1) : 0.5;

  const fracBeat = t => {  // continuous beat position, extrapolated past the ends
    if (!B.length) return t / meanBeat;
    const i = ub(B, t) - 1;
    if (i < 0) return (t - B[0]) / meanBeat;
    if (i >= B.length - 1) return B.length - 1 + (t - B[B.length - 1]) / meanBeat;
    return i + (t - B[i]) / (B[i + 1] - B[i]);
  };
  const intensity = t => {
    const x = t / I.dt, i = Math.floor(x), v = I.values;
    if (i < 0) return v[0];
    if (i >= v.length - 1) return v[v.length - 1];
    return v[i] + (v[i + 1] - v[i]) * (x - i);
  };
  const shape = (p, s, beatLen) => {
    const sh = s.shape || "decay";
    if (sh === "decay") return Math.exp(-(p * beatLen * (s.div ?? 1)) / (s.tau ?? 0.12));
    if (sh === "pulse") return p < (s.width ?? 0.25) ? 1 : 0;
    if (sh === "saw") return p;
    if (sh === "ramp") return 1 - p;
    if (sh === "sine") return 0.5 - 0.5 * Math.cos(2 * Math.PI * p);
    if (sh === "tri") return 1 - Math.abs(2 * p - 1);
    return null;
  };
  const ease = (e, u) => (e === "hold" ? 0 : e === "smooth" ? u * u * (3 - 2 * u) : u);

  function ev(s, t) {
    if (typeof s === "number") return s;
    if (s == null || typeof s !== "object" || Array.isArray(s)) return null;
    if (s.k) {
      const k = s.k;
      if (!k.length || typeof k[0][1] !== "number") return null;
      if (t <= k[0][0]) return k[0][1];
      if (t >= k[k.length - 1][0]) return k[k.length - 1][1];
      let i = 0; while (k[i + 1][0] < t) i++;
      const u = (t - k[i][0]) / (k[i + 1][0] - k[i][0] || 1);
      return k[i][1] + (k[i + 1][1] - k[i][1]) * ease(s.ease, u);
    }
    if (s.dense) {
      const { t0, dt, v } = s.dense;
      if (!v.length || typeof v[0] !== "number") return null;
      const x = (t - t0) / dt, i = Math.floor(x);
      if (i < 0) return v[0];
      if (i >= v.length - 1) return v[v.length - 1];
      return v[i] + (v[i + 1] - v[i]) * (x - i);
    }
    if (s.beat) {
      const b = s.beat, div = b.div ?? 1;
      const fb = fracBeat(t) - d0 - (b.offset ?? 0);
      const p = ((fb / div) % 1 + 1) % 1;
      return shape(p, b, meanBeat);
    }
    if (s.intensity) return intensity(t);
    if (s.onset) {
      const tau = s.onset.tau ?? 0.15, min = s.onset.min ?? 0;
      let i = ub(onT, t) - 1, best = 0;
      for (; i >= 0 && t - onT[i] < 6 * tau; i--) if (onS[i] >= min) best = Math.max(best, onS[i] * Math.exp(-(t - onT[i]) / tau));
      return best;
    }
    if (s.range) { const v = ev(s.of, t); return v == null ? null : s.range[0] + (s.range[1] - s.range[0]) * v; }
    if (s.clamp) { const v = ev(s.of, t); return v == null ? null : Math.min(s.clamp[1], Math.max(s.clamp[0], v)); }
    if (s.add) { let a = 0; for (const x of s.add) { const v = ev(x, t); if (v == null) return null; a += v; } return a; }
    if (s.mul) { let a = 1; for (const x of s.mul) { const v = ev(x, t); if (v == null) return null; a *= v; } return a; }
    return null;
  }
  return ev;
}

// a short human description of a signal, for tooltips
export function describe(s) {
  if (s == null) return "—";
  if (typeof s === "number") return String(+s.toFixed(3));
  if (Array.isArray(s)) return `[${s.map(describe).join(", ")}]`;
  const k = Object.keys(s)[0];
  if (k === "k") return `keys×${s.k.length}${s.ease ? " " + s.ease : ""}`;
  if (k === "beat") return `beat/${s.beat.div ?? 1} ${s.beat.shape || "decay"}`;
  if (k === "range") return `${s.range[0]}..${s.range[1]} of ${describe(s.of)}`;
  if (k === "path" || k === "pathscale") return `${k} ${s[k]}`;
  return k;
}
