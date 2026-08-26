"""Read-only access to `reports/` — an archive of assessment runs, one YAML file per
assessment, grouped into a folder per assessed system.

Unlike `keel/store.py`'s `Store`, nothing here is cached in memory: reports are read
fresh off disk on every call, because they are an immutable archive rather than hot
editable catalog data. Reports are written by the `assess-genai-with-library` skill
straight to disk; this module never writes.

Defensive by design: the archive holds many independent files, so one malformed or
schema-violating report is skipped in list views rather than failing the whole
request, and `get_report` reports the problem instead of raising.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from keel.schemas.report import Report

DEFAULT_REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"


def _reports_dir() -> Path:
    """Honors `settings.reports_dir` (env `REPORTS_DIR`); empty falls back to `reports/`."""
    from keel.config import settings

    return Path(settings.reports_dir) if settings.reports_dir else DEFAULT_REPORTS_DIR


def _load_report_file(path: Path) -> Report | None:
    """Parse one report file. None on any failure (unreadable, bad YAML, wrong shape)."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(data, dict):
        return None
    try:
        return Report(**data)
    except ValidationError:
        return None


def _load_system_reports(system_dir: Path) -> list[Report]:
    """Every parseable report in one system folder, newest first."""
    reports = [r for r in (_load_report_file(p) for p in sorted(system_dir.glob("*.yaml"))) if r]
    reports.sort(key=lambda r: r.date, reverse=True)
    return reports


def list_reports() -> list[dict[str, Any]]:
    """One entry per system folder: {system_id, system_name, latest_date, report_count,
    has_delta}. A system with no parseable report file is omitted entirely."""
    root = _reports_dir()
    if not root.is_dir():
        return []

    out: list[dict[str, Any]] = []
    for system_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        reports = _load_system_reports(system_dir)
        if not reports:
            continue
        out.append({
            "system_id": system_dir.name,
            "system_name": reports[0].system_name,
            "latest_date": reports[0].date,
            "report_count": len(reports),
            "has_delta": any(r.delta_summary for r in reports),
        })
    return out


def get_report_series(system_id: str) -> list[dict[str, Any]]:
    """`[{date, system_name}, ...]` for one system, newest first. Empty when the system
    folder is missing or holds nothing parseable — a system with no reports yet is not
    an error."""
    system_dir = _reports_dir() / system_id
    if not system_dir.is_dir():
        return []
    return [{"date": r.date, "system_name": r.system_name} for r in _load_system_reports(system_dir)]


def get_report(system_id: str, date: str) -> dict[str, Any]:
    """`{"success": True, "report": {...}}`, or `{"success": False, "error": "..."}`."""
    path = _reports_dir() / system_id / f"{date}.yaml"
    if not path.is_file():
        return {"success": False, "error": f"No report for {system_id!r} on {date!r}"}
    report = _load_report_file(path)
    if report is None:
        return {"success": False, "error": f"Report {system_id}/{date}.yaml could not be parsed"}
    return {"success": True, "report": report.model_dump()}
