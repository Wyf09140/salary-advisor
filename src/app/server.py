"""JSON API and static host for the dedicated web frontend in web/. Owner: Sophak.

Run:  python -m src.app.server        then open http://localhost:8600
Stdlib only (no new dependencies). Wraps the same predict()/recommend() and resume parser as the
Streamlit app, so both front ends always show the same numbers.

Endpoints
  GET  /api/skills          -> [{"key", "label"}]
  POST /api/parse-resume    {"name", "data": base64}                      -> {"skills", "years"}
  POST /api/estimate        {"title", "location", "salary", "skills", "years"}
                            -> {"range": {"p10","p50","p90","bls_median"}, "recommendations": [{"skill","label","delta"}]}
                            -> 422 {"errors": {field: message}} when title/location are missing
"""
import base64
import binascii
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.config import ROOT, SKILLS
from src.models.predict import predict, recommend
from src.app.resume_parser import extract_text, extract_skills, extract_years
from src.app.components import skill_label

WEB = ROOT / "web"
MAX_BODY = 15 * 1024 * 1024  # base64 of a ~10 MB resume


class BadRequest(Exception):
    def __init__(self, status: int, payload: dict):
        self.status, self.payload = status, payload


def _number(value, field: str) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        raise BadRequest(422, {"errors": {field: "Enter a number"}})


def estimate(body: dict) -> dict:
    title = str(body.get("title", "")).strip()
    location = str(body.get("location", "")).strip()
    errors = {}
    if not title:
        errors["title"] = "Enter a job title"
    if not location:
        errors["location"] = "Enter a city and state"
    if errors:
        raise BadRequest(422, {"errors": errors})
    skills = [s for s in body.get("skills") or [] if s in SKILLS]
    years = _number(body.get("years"), "years")
    r = predict(title, location, skills, years)
    recs = recommend({"title": title, "location": location, "skills": skills, "years_exp": years})
    return {
        "range": {k: float(r[k]) for k in ("p10", "p50", "p90", "bls_median")},
        "recommendations": [{"skill": s, "label": skill_label(s), "delta": float(d)} for s, d in recs],
    }


def parse_resume(body: dict) -> dict:
    name = str(body.get("name", ""))
    try:
        data = base64.b64decode(body.get("data", ""), validate=True)
    except (binascii.Error, ValueError):
        raise BadRequest(400, {"error": "File data is not valid base64"})
    try:
        text = extract_text(data, name)
    except Exception:
        raise BadRequest(422, {"error": "We couldn't read this file"})
    return {"skills": extract_skills(text), "years": extract_years(text)}


ROUTES = {"/api/estimate": estimate, "/api/parse-resume": parse_resume}


def skills() -> list[dict]:
    return [{"key": s, "label": skill_label(s)} for s in SKILLS]


def dispatch(path: str, body: dict | None = None) -> tuple[int, object]:
    """One entry point for every API call -> (status, payload). Used by the HTTP server below and by
    the desktop app's JS bridge (src/desktop/app.py), so both front ends get identical answers."""
    if path == "/api/skills":
        return 200, skills()
    route = ROUTES.get(path)
    if route is None:
        return 404, {"error": "Not found"}
    if not isinstance(body, dict):
        return 400, {"error": "Expected a JSON object"}
    try:
        return 200, route(body)
    except BadRequest as e:
        return e.status, e.payload
    except Exception as e:  # model or parser failure: keep running, tell the UI
        print(f"[salary-advisor] {path} failed: {e!r}", file=sys.stderr)
        return 500, {"error": "We couldn't estimate this role"}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def _send_json(self, status: int, payload) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/skills":
            return self._send_json(*dispatch(self.path))
        return super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            return self._send_json(413, {"error": "File is too large (max 10 MB)"})
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send_json(400, {"error": "Invalid JSON"})
        self._send_json(*dispatch(self.path, body))

    def log_message(self, fmt, *args):  # quieter console: only errors
        if args and str(args[1] if len(args) > 1 else "").startswith(("4", "5")):
            super().log_message(fmt, *args)


def main() -> None:
    port = int(os.environ.get("PORT", 8600))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Salary Advisor web app: http://localhost:{port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
