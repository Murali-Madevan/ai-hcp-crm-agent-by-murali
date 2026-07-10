import sys
import os
import json
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            from app.main import app
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "import_ok", "type": type(app).__name__}).encode())
        except Exception as e:
            import traceback
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            err = {"error": str(e), "type": type(e).__name__, "traceback": traceback.format_exc()}
            self.wfile.write(json.dumps(err).encode())
