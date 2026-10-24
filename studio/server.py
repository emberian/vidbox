"""Studio server: static files from the repo root (with HTTP Range, which <video> seeking
needs) plus POST /api/save?path=projects/... to write JSON back to disk.

usage: uv run python studio/server.py [port]
"""
import json
import os
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "projects"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(302)
            self.send_header("Location", "/studio/index.html")
            self.end_headers()
            return
        url = urlparse(self.path)
        if url.path == "/api/ls":
            d = (ROOT / parse_qs(url.query).get("dir", [""])[0]).resolve()
            if d != PROJECTS and PROJECTS not in d.parents:
                return self.send_error(403)
            names = sorted(p.name for p in d.glob("*.json")) if d.is_dir() else []
            body = json.dumps(names).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        rng = self.headers.get("Range")
        m = rng and re.fullmatch(r"bytes=(\d*)-(\d*)", rng.strip())
        if not m:
            return super().do_GET()
        fpath = Path(self.translate_path(self.path))
        if not fpath.is_file():
            return self.send_error(404)
        size = fpath.stat().st_size
        if m[1]:
            start = int(m[1])
            end = min(int(m[2]), size - 1) if m[2] else size - 1
        else:  # suffix range: last N bytes
            start, end = max(0, size - int(m[2])), size - 1
        if start > end:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            return self.end_headers()
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(str(fpath)))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        with open(fpath, "rb") as f:
            f.seek(start)
            left = end - start + 1
            try:
                while left:
                    chunk = f.read(min(1 << 20, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass  # browsers abort range reads constantly while scrubbing

    def do_POST(self):
        url = urlparse(self.path)
        if url.path != "/api/save":
            return self.send_error(404)
        rel = parse_qs(url.query).get("path", [""])[0]
        dest = (ROOT / rel).resolve()
        if PROJECTS not in dest.parents or dest.suffix != ".json":
            return self.send_error(403, "can only save .json under projects/")
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        data = json.loads(body)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=1) + "\n")
        os.replace(tmp, dest)
        self.send_response(204)
        self.end_headers()

    def log_message(self, fmt, *args):
        if self.command == "POST" or (args and str(args[1])[0] in "45"):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"studio: http://127.0.0.1:{port}/studio/index.html?project=meine")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
