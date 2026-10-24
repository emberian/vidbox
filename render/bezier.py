"""Timed cubic Bezier path evaluation; mirrors evalPath in studio/bezier.js."""
import bisect


def _cubic(p0, p1, p2, p3, u):
    v = 1 - u
    b0, b1, b2, b3 = v * v * v, 3 * v * v * u, 3 * v * u * u, u * u * u
    return (
        b0 * p0[0] + b1 * p1[0] + b2 * p2[0] + b3 * p3[0],
        b0 * p0[1] + b1 * p1[1] + b2 * p2[1] + b3 * p3[1],
    )


class Path:
    def __init__(self, data):
        self.anchors = sorted(data.get("anchors", []), key=lambda a: a["t"])
        self.times = [a["t"] for a in self.anchors]
        self.scale_track = data.get("scale")

    def scale(self, t):
        S = self.scale_track
        if not S or not S["values"]:
            return 1.0
        v = S["values"]
        x = max(0.0, min((t - S["t0"]) / S["dt"], len(v) - 1))
        i = min(int(x), len(v) - 2)
        if i < 0:
            return v[0]
        return v[i] + (v[i + 1] - v[i]) * (x - i)

    def __call__(self, t):
        A = self.anchors
        if not A:
            return None
        if t <= A[0]["t"]:
            return tuple(A[0]["p"])
        if t >= A[-1]["t"]:
            return tuple(A[-1]["p"])
        i = bisect.bisect_right(self.times, t) - 1
        a, b = A[i], A[i + 1]
        p0, p3 = a["p"], b["p"]
        p1 = (p0[0] + a["hout"][0], p0[1] + a["hout"][1])
        p2 = (p3[0] + b["hin"][0], p3[1] + b["hin"][1])
        return _cubic(p0, p1, p2, p3, (t - a["t"]) / (b["t"] - a["t"]))
