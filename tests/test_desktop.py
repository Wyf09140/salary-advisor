"""Desktop app checks that run without opening a window."""
import pytest

pytest.importorskip("webview")  # desktop extras are optional (requirements-desktop.txt)

from src.desktop import app


def test_page_html_turns_on_desktop_mode(monkeypatch):
    monkeypatch.delenv("SA_DESKTOP_OPEN", raising=False)
    assert '<html lang="en" class="desktop">' in app.page_html()
    monkeypatch.setenv("SA_DESKTOP_OPEN", "1")
    assert 'class="desktop start-open"' in app.page_html()


def test_bridge_call_matches_web_api():
    out = app.Api().call("/api/estimate", {"title": "Data Analyst", "location": "Boston, MA"})
    assert out["status"] == 200 and {"p10", "p50", "p90", "bls_median"} <= set(out["data"]["range"])
    assert app.Api().call("/api/estimate", {"title": "", "location": ""})["status"] == 422
