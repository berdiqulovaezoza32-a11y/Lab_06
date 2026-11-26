"""Minimal threaded HTTP worker for teaching Docker networks and scaling."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import datetime
import html
import json
import os
import socket
import time

INSTANCE = socket.gethostname()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.respond(200, "text/plain; charset=utf-8", b"OK")
            return

        ms = parse_qs(parsed.query).get("ms", ["0"])[0]
        try:
            delay = min(max(int(ms), 0), 2000) / 1000
        except ValueError:
            delay = 0
        time.sleep(delay)
        payload = {
            "instance": INSTANCE,
            "time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "delay_ms": round(delay * 1000),
            "message": "Docker virtual tarmoq laboratoriyasi",
        }

        if parsed.path == "/api":
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.respond(200, "application/json; charset=utf-8", data)
            return
        if parsed.path == "/":
            name = html.escape(INSTANCE)
            page = f"""<!doctype html><html lang='uz'><head><meta charset='utf-8'>
            <meta name='viewport' content='width=device-width, initial-scale=1'>
            <title>Cloud Network Lab</title>
            <style>body{{font-family:system-ui,sans-serif;max-width:720px;margin:5rem auto;padding:1rem;background:#f5f7fb;color:#183153}}.panel{{background:white;border-radius:16px;padding:28px;box-shadow:0 8px 24px #1232}}code{{background:#e6effb;padding:5px;border-radius:5px}}</style></head>
            <body><div class='panel'><h1>Bulut tarmoqlari laboratoriyasi</h1>
            <p>So‘rovga javob bergan konteyner: <code>{name}</code></p>
            <p>Har safar sahifani yangilang. Bir nechta nusxa bo‘lsa, nom o‘zgarishi mumkin.</p>
            <p><a href='/api'>JSON API javobi</a> | <a href='/api?ms=150'>150 ms ish simulyatsiyasi</a></p>
            </div></body></html>"""
            self.respond(200, "text/html; charset=utf-8", page.encode("utf-8"))
            return
        self.respond(404, "text/plain; charset=utf-8", b"Not found")

    def respond(self, code, content_type, payload):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        pass  # NGINX access log serves as the single autoscaling metric source.


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
