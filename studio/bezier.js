// Timed cubic Bezier paths.
//
// path = { anchors: [{ t, p: [x, y], hin: [dx, dy], hout: [dx, dy] }], takes: [...],
//          scale?: { t0, dt, values: [...] } }   (optional size multiplier, linear between samples)
// Anchors are sorted by t. Between anchors a and b the Bezier parameter is linear in time,
// u = (t - a.t) / (b.t - a.t), over control points a.p, a.p + a.hout, b.p + b.hin, b.p.
// render/bezier.py mirrors evalPath exactly; keep them in step.

const add = (a, b) => [a[0] + b[0], a[1] + b[1]];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1]];
const mul = (a, s) => [a[0] * s, a[1] * s];
const lerp = (a, b, u) => [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u];

function cubic(p0, p1, p2, p3, u) {
  const v = 1 - u;
  const b0 = v * v * v, b1 = 3 * v * v * u, b2 = 3 * v * u * u, b3 = u * u * u;
  return [
    b0 * p0[0] + b1 * p1[0] + b2 * p2[0] + b3 * p3[0],
    b0 * p0[1] + b1 * p1[1] + b2 * p2[1] + b3 * p3[1],
  ];
}

// Index of the anchor starting the segment containing t (assumes A[0].t <= t < A[last].t).
function segmentAt(A, t) {
  let lo = 0, hi = A.length - 1;
  while (hi - lo > 1) {
    const m = (lo + hi) >> 1;
    if (A[m].t <= t) lo = m; else hi = m;
  }
  return lo;
}

export function evalPath(path, t) {
  const A = path.anchors;
  if (!A.length) return null;
  if (t <= A[0].t) return A[0].p.slice();
  if (t >= A[A.length - 1].t) return A[A.length - 1].p.slice();
  const i = segmentAt(A, t), a = A[i], b = A[i + 1];
  return cubic(a.p, add(a.p, a.hout), add(b.p, b.hin), b.p, (t - a.t) / (b.t - a.t));
}

export function evalScale(path, t) {
  const S = path.scale;
  if (!S || !S.values.length) return 1;
  const x = Math.max(0, Math.min((t - S.t0) / S.dt, S.values.length - 1));
  const i = Math.min(Math.floor(x), S.values.length - 2);
  if (i < 0) return S.values[0];
  return S.values[i] + (S.values[i + 1] - S.values[i]) * (x - i);
}

// Least-squares cubic through samples[i0..i1] with endpoints pinned and the parameter
// fixed by time. Returns [p1, p2] (absolute inner control points).
function fitSegment(S, i0, i1) {
  const P0 = S[i0].p, P3 = S[i1].p, t0 = S[i0].t, dt = S[i1].t - t0;
  let c11 = 0, c12 = 0, c22 = 0, x1 = [0, 0], x2 = [0, 0];
  for (let i = i0; i <= i1; i++) {
    const u = (S[i].t - t0) / dt, v = 1 - u;
    const b0 = v * v * v, b1 = 3 * v * v * u, b2 = 3 * v * u * u, b3 = u * u * u;
    const r = sub(S[i].p, add(mul(P0, b0), mul(P3, b3)));
    c11 += b1 * b1; c12 += b1 * b2; c22 += b2 * b2;
    x1 = add(x1, mul(r, b1)); x2 = add(x2, mul(r, b2));
  }
  const det = c11 * c22 - c12 * c12;
  if (Math.abs(det) < 1e-9) return [lerp(P0, P3, 1 / 3), lerp(P0, P3, 2 / 3)];
  return [
    mul(sub(mul(x1, c22), mul(x2, c12)), 1 / det),
    mul(sub(mul(x2, c11), mul(x1, c12)), 1 / det),
  ];
}

// Fit samples [{t, p}] (sorted by t) with as few segments as keep max error <= tol px.
// `corners` are times that must become anchors left as sharp cusps (e.g. a bounce).
export function fitSamples(S, tol = 6, corners = []) {
  if (S.length < 2) return S.map(s => ({ t: s.t, p: s.p.slice(), hin: [0, 0], hout: [0, 0] }));
  const knots = [];  // [i0, i1, p1, p2]
  const rec = (i0, i1) => {
    const [p1, p2] = fitSegment(S, i0, i1);
    let worst = -1, err = 0;
    const t0 = S[i0].t, dt = S[i1].t - t0;
    for (let i = i0 + 1; i < i1; i++) {
      const q = cubic(S[i0].p, p1, p2, S[i1].p, (S[i].t - t0) / dt);
      const e = Math.hypot(q[0] - S[i].p[0], q[1] - S[i].p[1]);
      if (e > err) { err = e; worst = i; }
    }
    if (err > tol && i1 - i0 > 3) {
      // keep splits away from the very ends so both halves have something to fit
      const mid = Math.min(Math.max(worst, i0 + 2), i1 - 2);
      rec(i0, mid); rec(mid, i1);
    } else knots.push([i0, i1, p1, p2]);
  };
  const cut = [...new Set(corners.map(t => {
    let best = 0;
    for (let i = 1; i < S.length; i++) if (Math.abs(S[i].t - t) < Math.abs(S[best].t - t)) best = i;
    return best;
  }))].filter(i => i > 0 && i < S.length - 1).sort((a, b) => a - b);
  [0, ...cut, S.length - 1].reduce((i0, i1) => { if (i1 > i0) rec(i0, i1); return i1; });
  const cusp = new Set(cut.map(i => S[i].t));
  const A = [{ t: S[0].t, p: S[0].p.slice(), hin: [0, 0], hout: [0, 0] }];
  const reach = [];  // drawn stroke length of each segment
  for (const [i0, i1, p1, p2] of knots) {
    const prev = A[A.length - 1];
    prev.hout = sub(p1, prev.p);
    A.push({ t: S[i1].t, p: S[i1].p.slice(), hin: sub(p2, S[i1].p), hout: [0, 0] });
    let len = 0;
    for (let i = i0; i < i1; i++) len += Math.hypot(S[i + 1].p[0] - S[i].p[0], S[i + 1].p[1] - S[i].p[1]);
    reach.push(len);
  }
  for (let i = 1; i < A.length - 1; i++) if (!cusp.has(A[i].t)) smoothAnchor(A, i);
  // A handle longer than the stroke it shapes is a fitting artifact, not a gesture.
  A.forEach((a, i) => {
    if (i > 0) a.hin = clampLen(a.hin, reach[i - 1]);
    if (i < A.length - 1) a.hout = clampLen(a.hout, reach[i]);
  });
  return A;
}

function clampLen(h, max) {
  const l = Math.hypot(h[0], h[1]);
  return l > max ? mul(h, max / l) : h;
}

// Make velocity continuous through anchor i (C1 in time): hout/dt_out == -hin/dt_in.
export function smoothAnchor(A, i, keep = null) {
  if (i <= 0 || i >= A.length - 1) return;
  const a = A[i], dtIn = a.t - A[i - 1].t, dtOut = A[i + 1].t - a.t;
  let vel;
  if (keep === "in") vel = mul(a.hin, -1 / dtIn);
  else if (keep === "out") vel = mul(a.hout, 1 / dtOut);
  else vel = mul(sub(mul(a.hout, 1 / dtOut), mul(a.hin, 1 / dtIn)), 0.5);
  a.hout = mul(vel, dtOut);
  a.hin = mul(vel, -dtIn);
}

// Insert an anchor at time t without changing the curve's shape (de Casteljau split).
export function splitAt(path, t) {
  const A = path.anchors;
  if (A.length < 2 || t <= A[0].t || t >= A[A.length - 1].t) return -1;
  const i = segmentAt(A, t), a = A[i], b = A[i + 1];
  if (t - a.t < 1e-3 || b.t - t < 1e-3) return -1;
  const u = (t - a.t) / (b.t - a.t);
  const p0 = a.p, p1 = add(a.p, a.hout), p2 = add(b.p, b.hin), p3 = b.p;
  const q0 = lerp(p0, p1, u), q1 = lerp(p1, p2, u), q2 = lerp(p2, p3, u);
  const r0 = lerp(q0, q1, u), r1 = lerp(q1, q2, u), s = lerp(r0, r1, u);
  a.hout = sub(q0, p0);
  b.hin = sub(q2, p3);
  A.splice(i + 1, 0, { t, p: s, hin: sub(r0, s), hout: sub(r1, s) });
  return i + 1;
}

// Replace everything in [anchors[0].t, anchors[last].t] with the given anchors.
export function splice(path, anchors) {
  if (!anchors.length) return;
  const t0 = anchors[0].t, t1 = anchors[anchors.length - 1].t, eps = 1e-4;
  path.anchors = path.anchors
    .filter(a => a.t < t0 - eps || a.t > t1 + eps)
    .concat(anchors)
    .sort((a, b) => a.t - b.t);
}
