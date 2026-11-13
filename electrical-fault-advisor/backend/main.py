"""
Electrical Fault First-Response Advisor - REST API
FastAPI backend with dual-mode standard library fallback.
"""

import sys
import os
import json
from typing import Dict, Any, List

# Ensure current dir is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fault_advisor import (
    RULES,
    BASELINE,
    EVENTS,
    VALID_ATTRIBUTES,
    advise,
)

PORT = 8000
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

# Try importing FastAPI
try:
    from fastapi import FastAPI, HTTPException, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel, field_validator
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


def validate_facts_dict(data: Dict[str, Any]) -> List[str]:
    """Validates input payload against allowed domain values."""
    errors = []
    required_keys = ["feeder", "alarm", "load", "weather", "backup"]
    for k in required_keys:
        if k not in data:
            errors.append(f"Missing required field '{k}'")
        else:
            val = str(data[k]).strip().lower()
            if val not in VALID_ATTRIBUTES[k]:
                allowed = ", ".join(sorted(VALID_ATTRIBUTES[k]))
                errors.append(f"Invalid value '{val}' for field '{k}'. Allowed values: [{allowed}]")
    return errors


def compute_evaluation() -> Dict[str, Any]:
    """Evaluates the 17 benchmark events for Advisor vs Baseline."""
    results = []
    advisor_correct = 0
    baseline_correct = 0
    n = len(EVENTS)

    for ev in EVENTS:
        ev_id = ev["id"]
        facts = ev["facts"]
        expected = ev["expected"]

        adv_res = advise(facts)
        adv_act = adv_res["action"]
        rule_id = adv_res["chosen_rule"]["id"] if adv_res["chosen_rule"] else None
        adv_ok = adv_act == expected
        if adv_ok:
            advisor_correct += 1

        alarm = facts["alarm"]
        base_act = BASELINE.get(alarm, "monitor")
        base_ok = base_act == expected
        if base_ok:
            baseline_correct += 1

        results.append({
            "id": ev_id,
            "facts": facts,
            "description": ev.get("description", ""),
            "advisor_action": adv_act,
            "rule_id": rule_id,
            "expected": expected,
            "correct": adv_ok,
            "baseline_action": base_act,
            "baseline_correct": base_ok,
        })

    advisor_pct = round((advisor_correct / n) * 100, 1)
    baseline_pct = round((baseline_correct / n) * 100, 1)

    return {
        "events": results,
        "totals": {
            "advisor_correct": advisor_correct,
            "baseline_correct": baseline_correct,
            "n": n,
            "advisor_pct": advisor_pct,
            "baseline_pct": baseline_pct,
        },
    }


# =========================================================================
# FastAPI Application Definition (if available)
# =========================================================================
if HAS_FASTAPI:
    app = FastAPI(
        title="Electrical Fault First-Response Advisor",
        description="Rule-based decision support system for campus electrical substation",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request as StarletteRequest

    class NoCacheMiddleware(BaseHTTPMiddleware):
        """Prevent browsers caching static assets during development."""
        async def dispatch(self, request: StarletteRequest, call_next):
            response = await call_next(request)
            # Only set no-cache on static assets (not API JSON responses)
            if not request.url.path.startswith("/api/"):
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
                response.headers["Pragma"] = "no-cache"
            return response

    app.add_middleware(NoCacheMiddleware)

    class AdviseRequest(BaseModel):
        feeder: str
        alarm: str
        load: str
        weather: str
        backup: str

        @field_validator("feeder", "alarm", "load", "weather", "backup")
        @classmethod
        def validate_attribute(cls, v: str, info) -> str:
            field = info.field_name
            cleaned = v.strip().lower()
            if cleaned not in VALID_ATTRIBUTES.get(field, set()):
                allowed = ", ".join(sorted(VALID_ATTRIBUTES[field]))
                raise ValueError(f"Invalid value '{v}' for '{field}'. Allowed: [{allowed}]")
            return cleaned

    @app.get("/api/rules")
    def get_rules():
        return list(RULES.values())

    @app.get("/api/events")
    def get_events():
        return EVENTS

    @app.post("/api/advise")
    def post_advise(req: AdviseRequest):
        facts = {
            "feeder": req.feeder,
            "alarm": req.alarm,
            "load": req.load,
            "weather": req.weather,
            "backup": req.backup,
        }
        return advise(facts)

    @app.get("/api/evaluate")
    def get_evaluate():
        return compute_evaluation()

    if os.path.exists(FRONTEND_DIR):
        app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


# =========================================================================
# Built-in Fallback HTTP Server (Standard Library)
# =========================================================================
def run_standalone_server(port: int = PORT):
    import http.server
    import socketserver
    import urllib.parse
    import mimetypes

    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("text/css", ".css")

    class AdvisorHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

        def guess_type(self, path):
            if str(path).endswith(".js"):
                return "application/javascript"
            if str(path).endswith(".css"):
                return "text/css"
            return super().guess_type(path)

        def send_response(self, code, message=None):
            super().send_response(code, message)
            # Prevent browser caching of static assets so updates appear immediately
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")

        def _send_cors_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

        def do_OPTIONS(self):
            self.send_response(204)
            self._send_cors_headers()
            self.end_headers()

        def _send_json(self, data: Any, status_code: int = 200):
            body = json.dumps(data, indent=2).encode("utf-8")
            self.send_response(status_code)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path.rstrip("/")

            if path == "/api/rules":
                self._send_json(list(RULES.values()))
            elif path == "/api/events":
                self._send_json(EVENTS)
            elif path == "/api/evaluate":
                self._send_json(compute_evaluation())
            else:
                # Serve frontend static files (no-cache to prevent stale assets)
                super().do_GET()
                # Note: headers already sent by parent; we patch via send_header override instead

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path.rstrip("/")

            if path == "/api/advise":
                try:
                    content_length = int(self.headers.get("Content-Length", 0))
                    raw_body = self.rfile.read(content_length).decode("utf-8")
                    data = json.loads(raw_body)
                except Exception as e:
                    self._send_json({"detail": f"Malformed JSON: {str(e)}"}, status_code=422)
                    return

                errors = validate_facts_dict(data)
                if errors:
                    self._send_json({"detail": "; ".join(errors)}, status_code=422)
                    return

                facts = {
                    "feeder": str(data["feeder"]).strip().lower(),
                    "alarm": str(data["alarm"]).strip().lower(),
                    "load": str(data["load"]).strip().lower(),
                    "weather": str(data["weather"]).strip().lower(),
                    "backup": str(data["backup"]).strip().lower(),
                }
                res = advise(facts)
                self._send_json(res)
            else:
                self._send_json({"detail": "Not Found"}, status_code=404)

    # Find free port starting at port
    curr_port = port
    while curr_port < port + 20:
        try:
            with socketserver.TCPServer(("", curr_port), AdvisorHTTPRequestHandler) as httpd:
                print("=" * 65)
                print(f" Electrical Fault First-Response Advisor API Server running!")
                print(f" URL: http://localhost:{curr_port}")
                print(f" API Endpoints: /api/rules, /api/events, /api/advise, /api/evaluate")
                print("=" * 65)
                print("Press Ctrl+C to stop.")
                httpd.serve_forever()
        except OSError:
            curr_port += 1
            continue


if __name__ == "__main__":
    if HAS_FASTAPI:
        try:
            import uvicorn
            uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
        except ImportError:
            run_standalone_server(PORT)
    else:
        run_standalone_server(PORT)

