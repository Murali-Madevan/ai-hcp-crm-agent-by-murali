import sys
import os
import json
from http.server import BaseHTTPRequestHandler

CWD = os.getcwd()
FILE_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.join(FILE_DIR, '..', '..', 'backend')
BACKEND_ABS = os.path.abspath(BACKEND_DIR)

sys.path.insert(0, BACKEND_ABS)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            listing = os.listdir(BACKEND_ABS) if os.path.isdir(BACKEND_ABS) else "NOT_A_DIR"
            app_listing = os.listdir(os.path.join(BACKEND_ABS, 'app')) if os.path.isdir(os.path.join(BACKEND_ABS, 'app')) else "NOT_A_DIR"
            cwd_listing = os.listdir(CWD) if os.path.isdir(CWD) else "NOT_A_DIR"
            task_listing = os.listdir('/var/task') if os.path.isdir('/var/task') else "NOT_A_DIR"
            from app.main import app
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "cwd": CWD,
                "file_dir": FILE_DIR,
                "backend_abs": BACKEND_ABS,
                "backend_exists": os.path.isdir(BACKEND_ABS),
                "backend_listing": listing,
                "app_listing": app_listing,
                "task_listing": task_listing,
                "cwd_listing": cwd_listing,
                "pythonpath": sys.path[:5],
            }).encode())
        except Exception as e:
            import traceback
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            err = {
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc(),
                "cwd": CWD,
                "file_dir": FILE_DIR,
                "backend_abs": BACKEND_ABS,
                "backend_exists": os.path.isdir(BACKEND_ABS),
            }
            try:
                err["task_listing"] = os.listdir('/var/task') if os.path.isdir('/var/task') else "N/A"
            except:
                err["task_listing"] = "ERROR"
            self.wfile.write(json.dumps(err).encode())
