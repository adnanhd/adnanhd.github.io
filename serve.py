#!/usr/bin/env python3
"""Serve the site locally for testing.

`file://` is not enough any more: the blog search loads pagefind as a
module and fetches its index in byte ranges, and neither works off the
filesystem. Python's own http.server ignores Range requests, which makes
pagefind hang, so this adds them.

    python3 serve.py            # http://localhost:8000
"""

import http.server
import os
import re
import socketserver
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".pagefind": "application/wasm",
    }

    def send_head(self):
        rng = self.headers.get("Range")
        if not rng:
            return super().send_head()
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            return super().send_head()
        m = re.match(r"bytes=(\d+)-(\d*)", rng)
        if not m:
            return super().send_head()
        size = os.path.getsize(path)
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else size - 1
        end = min(end, size - 1)
        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        return f

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()


with socketserver.ThreadingTCPServer(("", PORT), Handler) as httpd:
    print(f"http://localhost:{PORT}/index.html?tab=blogs")
    httpd.serve_forever()
