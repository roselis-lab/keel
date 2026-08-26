"""Read-only access to reports/.

Unlike the catalog, reports are NOT loaded into the in-memory Store — they're an
archive, read fresh off disk per call. So these tests point `settings.reports_dir` at
a temp directory (the same seam `test_catalog_dir_override.py` uses for the catalog)
rather than installing a store.
"""
import yaml

import keel.config
from keel.services import report_service

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


def _write_report(reports_dir, system_id, date, extra=None):
    d = reports_dir / system_id
    d.mkdir(parents=True, exist_ok=True)
    payload = dict(VALID_REPORT, system_id=system_id, date=date)
    if extra:
        payload.update(extra)
    (d / f"{date}.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")


def _write_broken(reports_dir, system_id, date):
    d = reports_dir / system_id
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{date}.yaml").write_text("not: [valid, yaml, :::", encoding="utf-8")


def test_reports_dir_honors_override(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    assert report_service._reports_dir() == tmp_path


def test_list_reports_missing_dir_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path / "nope"))
    assert report_service.list_reports() == []


def test_list_reports_empty_dir_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    assert report_service.list_reports() == []


def test_list_reports_groups_by_system_with_latest_date(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-05-10")
    _write_report(tmp_path, "checkout-agent", "2026-08-26", {"delta_summary": "added a new tool"})
    _write_report(tmp_path, "support-bot", "2026-07-01")

    by_id = {i["system_id"]: i for i in report_service.list_reports()}
    assert set(by_id) == {"checkout-agent", "support-bot"}
    assert by_id["checkout-agent"]["latest_date"] == "2026-08-26"
    assert by_id["checkout-agent"]["report_count"] == 2
    assert by_id["checkout-agent"]["has_delta"] is True
    assert by_id["support-bot"]["report_count"] == 1
    assert by_id["support-bot"]["has_delta"] is False


def test_list_reports_skips_a_malformed_file(tmp_path, monkeypatch):
    """One bad file must not take down the whole listing — this is an archive of many
    independent files, not a single validated catalog."""
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    _write_broken(tmp_path, "broken-system", "2026-08-01")

    assert [i["system_id"] for i in report_service.list_reports()] == ["checkout-agent"]


def test_list_reports_skips_a_schema_violating_file(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    d = tmp_path / "wrong-shape"
    d.mkdir()
    (d / "2026-08-01.yaml").write_text(yaml.safe_dump({"system_id": "x"}), encoding="utf-8")

    assert [i["system_id"] for i in report_service.list_reports()] == ["checkout-agent"]


def test_get_report_series_sorted_newest_first(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-05-10")
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    assert [r["date"] for r in report_service.get_report_series("checkout-agent")] == [
        "2026-08-26", "2026-05-10",
    ]


def test_get_report_series_unknown_system_is_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    assert report_service.get_report_series("no-such-system") == []


def test_get_report_returns_parsed_report(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    result = report_service.get_report("checkout-agent", "2026-08-26")
    assert result["success"] is True
    assert result["report"]["system_name"] == "Checkout Agent"


def test_get_report_missing_file_returns_error_not_exception(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    result = report_service.get_report("no-such-system", "2026-08-26")
    assert result["success"] is False
    assert "error" in result


def test_get_report_malformed_file_returns_error_not_exception(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_broken(tmp_path, "broken-system", "2026-08-01")
    result = report_service.get_report("broken-system", "2026-08-01")
    assert result["success"] is False
    assert "error" in result
