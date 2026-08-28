"""Access to `reports/` — an archive of assessment runs, one YAML file per assessment,
grouped into a folder per assessed system.

Unlike `keel/store.py`'s `Store`, nothing here is cached in memory: reports are read
fresh off disk on every call. The skill writes the first pass straight to disk; the
specialist then corrects it through `save_report` until `finalize_report` freezes it.

**A final report is never overwritten.** `save_report` refuses one, and `reopen_report`
is the way forward: it copies a final report into a new draft under today's date, so a
correction lands beside the record it revises instead of erasing it.

Defensive by design: the archive holds many independent files, so one malformed or
schema-violating report is skipped in list views rather than failing the whole
request, and `get_report` reports the problem instead of raising.
"""
from __future__ import annotations

import datetime
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from keel.schemas.report import Report
from keel.store import dump_yaml

# A system id is a folder name and a date is a file name, both taken from the URL.
# Anything outside these shapes could escape the archive directory.
SYSTEM_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

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
    """`[{date, system_name, status}, ...]` for one system, newest first. Empty when the
    system folder is missing or holds nothing parseable — a system with no reports yet
    is not an error."""
    if not SYSTEM_ID_RE.match(system_id):
        return []
    system_dir = _reports_dir() / system_id
    if not system_dir.is_dir():
        return []
    return [
        {"date": r.date, "system_name": r.system_name, "status": r.status}
        for r in _load_system_reports(system_dir)
    ]


def _report_path(system_id: str, date: str) -> Path | None:
    """The file for one report, or None when either id would escape the archive."""
    if not SYSTEM_ID_RE.match(system_id) or not DATE_RE.match(date):
        return None
    return _reports_dir() / system_id / f"{date}.yaml"


def get_report(system_id: str, date: str) -> dict[str, Any]:
    """`{"success": True, "report": {...}}`, or `{"success": False, "error": "..."}`."""
    path = _report_path(system_id, date)
    if path is None or not path.is_file():
        return {"success": False, "error": f"No report for {system_id!r} on {date!r}"}
    report = _load_report_file(path)
    if report is None:
        return {"success": False, "error": f"Report {system_id}/{date}.yaml could not be parsed"}
    return {"success": True, "report": report.model_dump()}


def _write(path: Path, report: Report) -> None:
    """Field order comes from the schema's own declaration order, so a file the UI saves
    and a file the skill writes are byte-comparable and diff cleanly."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_yaml(report.model_dump()), encoding="utf-8")


def save_report(system_id: str, date: str, data: dict[str, Any]) -> dict[str, Any]:
    """Replace one report with a corrected version. Refuses to touch a final report."""
    path = _report_path(system_id, date)
    if path is None:
        return {"success": False, "error": "invalid system id or date"}
    if not path.is_file():
        return {"success": False, "error": f"No report for {system_id!r} on {date!r}"}

    existing = _load_report_file(path)
    if existing is None:
        return {"success": False, "error": "the report on disk could not be parsed"}
    if existing.status == "final":
        return {
            "success": False,
            "error": "this report is final — open it as a new draft to revise it",
        }

    try:
        report = Report(**data)
    except ValidationError as exc:
        return {"success": False, "error": "invalid report", "errors": exc.errors()}
    # The path IS the identity. Accepting a body that disagrees with it would let a save
    # of one report silently land on another.
    if report.system_id != system_id or report.date != date:
        return {"success": False, "error": "system_id and date cannot be changed by a save"}
    if report.status != "draft":
        return {"success": False, "error": "use finalize to move a report out of draft"}

    _write(path, report)
    return {"success": True, "report": report.model_dump()}


def finalize_report(system_id: str, date: str) -> dict[str, Any]:
    """Freeze a draft. Already-final is not an error — the caller got what it wanted."""
    path = _report_path(system_id, date)
    if path is None or not path.is_file():
        return {"success": False, "error": f"No report for {system_id!r} on {date!r}"}
    report = _load_report_file(path)
    if report is None:
        return {"success": False, "error": "the report on disk could not be parsed"}
    if report.status != "final":
        report.status = "final"
        _write(path, report)
    return {"success": True, "report": report.model_dump()}


def reopen_report(system_id: str, date: str, today: str | None = None) -> dict[str, Any]:
    """Copy a report into a new draft dated today, leaving the original untouched.

    This is how a final report gets corrected. Refuses to overwrite an existing file, so
    reopening twice in one day cannot discard the draft already in progress.
    """
    source_path = _report_path(system_id, date)
    if source_path is None or not source_path.is_file():
        return {"success": False, "error": f"No report for {system_id!r} on {date!r}"}
    report = _load_report_file(source_path)
    if report is None:
        return {"success": False, "error": "the report on disk could not be parsed"}

    new_date = today or datetime.date.today().isoformat()
    target_path = _report_path(system_id, new_date)
    if target_path is None:
        return {"success": False, "error": "invalid date"}
    if target_path.exists():
        return {
            "success": False,
            "error": f"a report for {new_date} already exists — open that one instead",
        }

    report.date = new_date
    report.status = "draft"
    _write(target_path, report)
    return {"success": True, "report": report.model_dump()}
