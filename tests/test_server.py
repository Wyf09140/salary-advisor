import base64

import pytest

from src.app.server import BadRequest, dispatch, estimate, parse_resume


def test_dispatch_routes_and_errors():
    status, skills = dispatch("/api/skills")
    assert status == 200 and {"key", "label"} <= set(skills[0])
    assert dispatch("/api/estimate", {"title": "", "location": ""})[0] == 422
    assert dispatch("/api/estimate", "not a dict")[0] == 400
    assert dispatch("/api/nope", {})[0] == 404
    status, out = dispatch("/api/estimate", {"title": "SWE", "location": "Boston, MA"})
    assert status == 200 and "range" in out


def test_estimate_contract():
    out = estimate({"title": "Data Scientist", "location": "San Jose, CA", "skills": ["python", "nope"], "years": "2"})
    r = out["range"]
    assert r["p10"] <= r["p50"] <= r["p90"] and "bls_median" in r
    assert all({"skill", "label", "delta"} <= set(x) for x in out["recommendations"])
    assert "python" not in [x["skill"] for x in out["recommendations"]]


def test_estimate_requires_title_and_location():
    with pytest.raises(BadRequest) as e:
        estimate({"title": " ", "location": ""})
    assert e.value.status == 422 and set(e.value.payload["errors"]) == {"title", "location"}


def test_parse_resume_txt():
    data = base64.b64encode(b"2 years of experience with Python and SQL").decode()
    out = parse_resume({"name": "cv.txt", "data": data})
    assert {"python", "sql"} <= set(out["skills"]) and out["years"] == 2.0


def test_parse_resume_bad_base64():
    with pytest.raises(BadRequest):
        parse_resume({"name": "cv.txt", "data": "not base64!"})
