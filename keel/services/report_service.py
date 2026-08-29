"""Access to `reports/` — an archive of assessment runs, one YAML file per assessment,
grouped into a folder per assessed system.

Unlike `keel/store.py`'s `Store`, nothing here is cached in memory: reports are read
fresh off disk on every call. The skill writes the first pass straight to disk; the
specialist then corrects it through `save_report` until `finalize_report` freezes it.

Two different things can happen to a finished report, and they are separate calls
because they mean separate things:

* `correct_report` — the assessment was right, the record was wrong. A typo, a
  mis-stated owner, a grade that came out of the conversation differently from how it
  was written down. It unlocks the SAME dated report for editing. The date does not
  move, because nothing was re-assessed.
* `reopen_report` — the system changed. New tools, new surface, new answers. This is a
  new assessment, so it gets a new date, carrying the previous findings forward as a
  starting point rather than making anyone retype them.

`save_report` still refuses a final report outright: unlocking is a deliberate act, not
something a stray keystroke does. Git is the audit trail — every one of these files is
versioned — so `status` records the state of the WORK, not a lock on the file.

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


def _latest_per_system() -> list[Report]:
    """Each system's most recent report. Cross-system figures are taken from these and
    not from the whole archive: an older assessment's findings may already be closed,
    and counting them would keep reporting work that is done."""
    root = _reports_dir()
    if not root.is_dir():
        return []
    out = []
    for system_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        reports = _load_system_reports(system_dir)
        if reports:
            out.append(reports[0])
    return out


def _all_reports() -> list[Report]:
    root = _reports_dir()
    if not root.is_dir():
        return []
    out: list[Report] = []
    for system_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        out.extend(_load_system_reports(system_dir))
    return out


def insights() -> dict[str, Any]:
    """What the archive says read ACROSS systems rather than one at a time.

    Reports are the only evidence Keel has about whether its model matches reality, so
    every figure here points back at something to do:

    * `most_requested` — one control asked for by several systems, implemented by none,
      is a thing to build once centrally instead of N times.
    * `off_catalog` — a finding with no catalog threat, or an ask with no catalog card,
      is the library's own to-do list, written by real assessments.
    * `threat_activity` — a card ruled out more often than it is confirmed describes
      something that keeps turning out not to apply, and is a candidate for rewording.
    * `drafts` — an assessment nobody finalized is unfinished work.
    """
    from keel.store import get_store

    store = get_store()
    latest, every = _latest_per_system(), _all_reports()

    requested: dict[str, list[str]] = {}
    off_catalog: list[dict[str, Any]] = []
    confirmed: dict[str, set[str]] = {}
    ruled_out: dict[str, set[str]] = {}
    severity_mix = {"high": 0, "medium": 0, "low": 0}
    per_system: list[dict[str, Any]] = []

    for rep in latest:
        open_asks = 0
        own_mix = {"high": 0, "medium": 0, "low": 0}
        for f in rep.findings:
            severity_mix[f.risk.severity] += 1
            own_mix[f.risk.severity] += 1
            open_asks += sum(
                1 for r in f.requirements
                if r.included and r.coverage_status != "already_covered"
            )
            confirmed.setdefault(f.id, set()).add(rep.system_id)
            if not f.from_catalog:
                off_catalog.append({
                    "kind": "threat", "label": f.id, "detail": f.scenario,
                    "system_id": rep.system_id, "date": rep.date,
                })
            for r in f.requirements:
                if not r.included or r.coverage_status == "already_covered":
                    continue
                if r.mitigation_id:
                    requested.setdefault(r.mitigation_id, []).append(rep.system_id)
                else:
                    off_catalog.append({
                        "kind": "control", "label": r.description or "", "detail": f.id,
                        "system_id": rep.system_id, "date": rep.date,
                    })
        for d in rep.discarded:
            ruled_out.setdefault(d.id, set()).add(rep.system_id)
        per_system.append({
            "system_id": rep.system_id,
            "system_name": rep.system_name,
            "date": rep.date,
            "status": rep.status,
            "findings": len(rep.findings),
            "open_requirements": open_asks,
            "severity": own_mix,
        })
    # Worst first: most high findings, then most findings. A dashboard chart is read
    # top-down, so the row that needs attention has to be the one the eye lands on.
    per_system.sort(key=lambda s: (-s["severity"]["high"], -s["findings"], s["system_id"]))

    most_requested = [
        {
            "mitigation_id": mid,
            "name": (store.mitigations.get(mid) or {}).get("name") or mid,
            "in_catalog": mid in store.mitigations,
            # An empty `implementations` list means the control is a recommendation, not
            # something present anywhere — see the assessment skill's reading of it.
            "implemented": bool((store.mitigations.get(mid) or {}).get("implementations")),
            "systems": sorted(set(systems)),
        }
        for mid, systems in requested.items()
    ]
    most_requested.sort(key=lambda x: (-len(x["systems"]), x["mitigation_id"]))

    activity = [
        {
            "id": tid,
            "title": (store.threats.get(tid) or {}).get("title") or tid,
            "in_catalog": tid in store.threats,
            "confirmed": sorted(confirmed.get(tid, set())),
            "ruled_out": sorted(ruled_out.get(tid, set())),
        }
        for tid in sorted(set(confirmed) | set(ruled_out))
    ]

    return {
        "systems": len(latest),
        "assessments": len(every),
        "latest_date": max((r.date for r in every), default=None),
        "drafts": [
            {"system_id": r.system_id, "date": r.date} for r in every if r.status == "draft"
        ],
        "severity_mix": severity_mix,
        "per_system": per_system,
        "most_requested": most_requested,
        "off_catalog": off_catalog,
        "threat_activity": activity,
        "never_assessed": sorted(set(store.threats) - set(confirmed) - set(ruled_out)),
    }


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


def correct_report(system_id: str, date: str) -> dict[str, Any]:
    """Unlock a final report for correction, keeping its date.

    Fixing a mistake in the record is not a re-assessment: nothing about the system was
    looked at again, so moving the date would be a lie about when the work was done.
    Already-draft is not an error — the caller wanted it editable and it is.
    """
    path = _report_path(system_id, date)
    if path is None or not path.is_file():
        return {"success": False, "error": f"No report for {system_id!r} on {date!r}"}
    report = _load_report_file(path)
    if report is None:
        return {"success": False, "error": "the report on disk could not be parsed"}
    if report.status != "draft":
        report.status = "draft"
        _write(path, report)
    return {"success": True, "report": report.model_dump()}


def create_report(
    system_id: str, system_name: str, system_description: str, assessor: str,
    date: str | None = None,
) -> dict[str, Any]:
    """An empty draft for a system that has never been assessed, or a fresh start.

    Refuses to land on an existing file: creating is never a way to lose a report.
    """
    date = date or datetime.date.today().isoformat()
    path = _report_path(system_id, date)
    if path is None:
        return {"success": False, "error": "system id must be lowercase letters, digits and hyphens"}
    if path.exists():
        return {"success": False, "error": f"{system_id} already has a report for {date}"}
    try:
        report = Report(
            system_id=system_id, system_name=system_name,
            system_description=system_description, date=date, assessor=assessor,
        )
    except ValidationError as exc:
        return {"success": False, "error": "invalid report", "errors": exc.errors()}
    _write(path, report)
    return {"success": True, "report": report.model_dump()}


def reopen_report(system_id: str, date: str, today: str | None = None) -> dict[str, Any]:
    """Copy a report into a new draft dated today, leaving the original untouched.

    This is a NEW assessment of a changed system, not a correction — see
    `correct_report` for that. Refuses to overwrite an existing file, so starting one
    twice in a day cannot discard the draft already in progress.
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
