"""Read-only report endpoints. No write path exists — reports are written to disk by
the assessment skill, not through the API."""
import yaml
from fastapi.testclient import TestClient

import keel.config
from keel.main import app

VALID_REPORT = {
    "system_id": "checkout-agent",
    "system_name": "Checkout Agent",
    "system_description": "Handles checkout for the storefront.",
    "date": "2026-08-26",
    "assessor": "Jane Doe <jane@example.com>",
    "findings": [],
    "discarded": [],
    "dialogue": [],
}


def _write_report(reports_dir, system_id, date):
    d = reports_dir / system_id
    d.mkdir(parents=True, exist_ok=True)
    payload = dict(VALID_REPORT, system_id=system_id, date=date)
    (d / f"{date}.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")


def test_route_list_reports(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    r = TestClient(app).get("/reports")
    assert r.status_code == 200
    assert r.json()["reports"][0]["system_id"] == "checkout-agent"


def test_route_list_reports_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    r = TestClient(app).get("/reports")
    assert r.status_code == 200
    assert r.json()["reports"] == []


def test_route_report_series(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-05-10")
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    r = TestClient(app).get("/reports/checkout-agent")
    assert r.status_code == 200
    assert [x["date"] for x in r.json()["series"]] == ["2026-08-26", "2026-05-10"]


def test_route_report_series_unknown_system_returns_empty_not_404(tmp_path, monkeypatch):
    """A system with no reports yet is not an error."""
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    r = TestClient(app).get("/reports/no-such-system")
    assert r.status_code == 200
    assert r.json()["series"] == []


def test_route_get_report_ok(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    r = TestClient(app).get("/reports/checkout-agent/2026-08-26")
    assert r.status_code == 200
    assert r.json()["system_name"] == "Checkout Agent"


def test_route_get_report_missing_is_404(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    r = TestClient(app).get("/reports/no-such-system/2026-08-26")
    assert r.status_code == 404


def test_route_get_report_malformed_is_404_not_500(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    d = tmp_path / "broken-system"
    d.mkdir()
    (d / "2026-08-01.yaml").write_text("not: [valid, yaml, :::", encoding="utf-8")
    r = TestClient(app).get("/reports/broken-system/2026-08-01")
    assert r.status_code == 404
