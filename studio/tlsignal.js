// Scalar signal evaluation for the timeline viewer (TIMELINE.md "Signals"). The viewer uses it to
// draw a layer's opacity envelope; it returns null for forms it can't evaluate as a number
// (vectors, Bezier paths), and the caller treats those as "unknown".
// Mirrors render/signals.py (Music + compile_signal) for the scalar forms; keep them in step.

const ub = (a, x) => { let lo = 0, hi = a.length; while (lo < hi) { const m = (lo + hi) >> 1; if (a[m] <= x) lo = m + 1; else hi = m; } return lo; };
const median = a => {
  const s = [...a].sort((x, y) => x - y), n = s.length;
  return n % 2 ? s[n >> 1] : (s[n / 2 - 1] + s[n / 2]) / 2;
};

// music: {beats, downbeats, onsets: [[t, s]], intensity: {dt, values}}
export function makeEval(music) {
  const B = music.beats, D = music.downbeats;
  const onT = music.onsets.map(o => o[0]), onS = music.onsets.map(o => o[1]);
  const I = music.intensity;
  // signals.py Music: period = median beat interval; db0 = the beat nearest the first downbeat
  // (phase origin, so beat-signal phase 0 lands on downbeats)
  const period = B.length > 1 ? median(B.slice(1).map((b, i) => b - B[i])) : 0.5;
  let db0 = 0;
  if (D.length) for (let i = 1; i < B.length; i++) if (Math.abs(B[i] - D[0]) < Math.abs(B[db0] - D[0])) db0 = i;

  const beatPos = t => {  // continuous beat count, extrapolated at the median period off the ends
    if (!B.length) return t / period;
    if (t < B[0]) return (t - B[0]) / period;
    if (t >= B[B.length - 1]) return B.length - 1 + (t - B[B.length - 1]) / period;
    const i = ub(B, t) - 1;
    return i + (t - B[i]) / (B[i + 1] - B[i]);
  };
  const smoothed = new Map();   // smooth seconds -> moving-average copy of the intensity values
  const intensity = (t, smooth = 0) => {
    let v = I.values;
    if (smooth > 0) {
      const key = Math.round(smooth * 1000);
      if (!smoothed.has(key)) {
        const k = Math.max(1, Math.floor(smooth / I.dt)), n = v.length, out = new Array(n);
        for (let i = 0; i < n; i++) {
          let s = 0;
          for (let j = i - k; j <= i + k; j++) s += v[Math.min(n - 1, Math.max(0, j))];
          out[i] = s / (2 * k + 1);
        }
        smoothed.set(key, out);
      }
      v = smoothed.get(key);
    }
    const x = Math.min(Math.max(t / I.dt, 0), v.length - 1), i = Math.min(Math.floor(x), v.length - 2);
    if (i < 0) return v[0];
    return v[i] + (v[i + 1] - v[i]) * (x - i);
  };
  const shape = (ph, s, len) => {   // len: the period in seconds (div beats)
    const sh = s.shape || "decay";
    if (sh === "decay") return Math.exp(-ph * len / (s.tau ?? 0.12));
    if (sh === "pulse") return ph < (s.width ?? 0.25) ? 1 : 0;
    if (sh === "saw") return ph;
    if (sh === "ramp") return 1 - ph;
    if (sh === "sine") return 0.5 - 0.5 * Math.cos(2 * Math.PI * ph);
    if (sh === "tri") return 1 - Math.abs(2 * ph - 1);
    return null;
  };
  const ease = (e, u) => (e === "hold" ? 0 : e === "smooth" ? u * u * (3 - 2 * u) : u);
  const sortedKeys = new WeakMap();   // signals.py sorts keyframes by time once, at compile

  function ev(s, t) {
    if (typeof s === "number") return s;
    if (s == null || typeof s !== "object" || Array.isArray(s)) return null;
    if (s.k) {
      if (!s.k.length || typeof s.k[0][1] !== "number") return null;
      let k = sortedKeys.get(s);
      if (!k) { k = [...s.k].sort((a, b) => a[0] - b[0]); sortedKeys.set(s, k); }
      if (t <= k[0][0]) return k[0][1];
      if (t >= k[k.length - 1][0]) return k[k.length - 1][1];
      let lo = 0, hi = k.length;   // last key with time <= t (bisect_right - 1)
      while (lo < hi) { const m = (lo + hi) >> 1; if (k[m][0] <= t) lo = m + 1; else hi = m; }
      const i = lo - 1, u = (t - k[i][0]) / (k[i + 1][0] - k[i][0]);
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
      const c = (beatPos(t) - db0) / div - (b.offset ?? 0);   // offset is in periods, as in signals.py
      return shape(c - Math.floor(c), b, div * period);
    }
    if (s.intensity) return intensity(t, s.intensity.smooth ?? 0);
    if (s.onset) {
      const tau = s.onset.tau ?? 0.15, min = s.onset.min ?? 0.3;
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
