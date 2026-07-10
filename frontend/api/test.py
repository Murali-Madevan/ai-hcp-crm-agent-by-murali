import sys
import os
import json
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            from app.main import app
            from app.config import settings
            groq_key = os.environ.get("GROQ_API_KEY", "")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "type": type(app).__name__,
                "db_url": settings.DATABASE_URL,
                "frontend_origin": settings.FRONTEND_ORIGIN,
                "frontend_origin_alt": settings.FRONTEND_ORIGIN_ALT,
                "groq_key_set": bool(groq_key),
                "groq_key_prefix": groq_key[:8] + "..." if groq_key and len(groq_key) > 8 else "",
            }).encode())
        except Exception as e:
            import traceback
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc()
            }).encode())

    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len)
        try:
            import json as j
            data = j.loads(body)
            from app.routers.form_agent import chat
            from app.database import SessionLocal
            from fastapi import Depends
            db = SessionLocal()
            try:
                result = chat(data, db)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(j.dumps({"result": "ok"}).encode())
            finally:
                db.close()
        except Exception as e:
            import traceback
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc()
            }).encode())
