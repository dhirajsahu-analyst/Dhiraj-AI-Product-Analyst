#!/usr/bin/env python3
"""
🌐 Local server for the Ask Alteryx dashboard.

Serves ask_alteryx_dashboard.html and exposes GET /api/refresh, which re-queries
Snowflake and returns the fresh data blob as JSON. The dashboard's "Refresh data"
button calls this endpoint and re-renders in place — same design, new numbers.

Run:
  python3 serve_dashboard.py            # http://localhost:8000
  python3 serve_dashboard.py --port 9000

Note: with browser-SSO auth, each live refresh opens an SSO popup. For popup-free
refresh, configure key-pair auth (see SCHEDULER_SETUP.md).
"""

import os
import sys
import json
import http.server
import socketserver

import refresh_dashboard as rd

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8000
if "--port" in sys.argv:
    PORT = int(sys.argv[sys.argv.index("--port") + 1])


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=HERE, **k)

    def do_GET(self):
        if self.path.split("?")[0] in ("/api/refresh", "/api/refresh/"):
            return self.handle_refresh()
        if self.path in ("/", ""):
            self.path = "/ask_alteryx_dashboard.html"
        return super().do_GET()

    def handle_refresh(self):
        print("↻ /api/refresh — querying Snowflake …")
        try:
            data = rd.build_data()          # live pull + assemble
            rd.render(data)                  # also refresh the on-disk HTML
            body = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            print("✅ refreshed")
        except Exception as e:
            msg = json.dumps({"error": str(e)}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
            print(f"❌ refresh failed: {e}")

    def log_message(self, *a):
        pass  # quiet default logging


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"\n🚀 Ask Alteryx dashboard → http://localhost:{PORT}")
        print("   Click “Refresh data” to pull live numbers · Ctrl+C to stop.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 stopped")
