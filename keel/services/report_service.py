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

from keel.errors import Conflict, Invalid, NotFound, invalid_from_pydantic
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
    has_delta, status, keywords}. A system with no parseable report file is omitted.

    `keywords` is what a rail filter searches beyond the name: the description, and the
    threat and control ids of the latest assessment. Filtering a handful of system names
    is not worth a search box — "which systems still owe me CTRL-HACT-CRITICAL" is.
    """
    root = _reports_dir()
    if not root.is_dir():
        return []

    out: list[dict[str, Any]] = []
    for system_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        reports = _load_system_reports(system_dir)
        if not reports:
            continue
        latest = reports[0]
        ids = {f.id for f in latest.findings}
        ids |= {r.mitigation_id for f in latest.findings for r in f.requirements if r.mitigation_id}
        ids |= {d.id for d in latest.discarded}
        out.append({
            "system_id": system_dir.name,
            "system_name": latest.system_name,
            "latest_date": latest.date,
            "status": latest.status,
            "report_count": len(reports),
            "has_delta": any(r.delta_summary for r in reports),
            "keywords": " ".join([latest.system_description, *sorted(ids)]).lower(),
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
    """The file for one report, or None when either part would escape the archive.

    Two checks, and only the second is load-bearing. The patterns give a readable refusal
    and keep ids to a shape; the resolve-and-compare is what actually holds, because a
    pattern is one edit away from being wrong and does not survive a symlink, a
    normalisation quirk, or a platform that rewrites the name on the way to disk. This
    was pattern-only, which made it the last place in the codebase where a regex was the
    whole boundary.
    """
    if not SYSTEM_ID_RE.match(system_id) or not DATE_RE.match(date):
        return None

    root = _reports_dir().resolve()
    system_dir = (root / system_id).resolve()
    path = (system_dir / f"{date}.yaml").resolve()
    if system_dir.parent != root or path.parent != system_dir:
        return None
    return path


def _require_path(system_id: str, date: str):
    """The file, or a NotFound that says what dates do exist for this system."""
    path = _report_path(system_id, date)
    if path is None:
        raise Invalid(
            f"{system_id!r} / {date!r} is not a valid system id and date",
            hint="system_id is lowercase letters, digits and hyphens; date is YYYY-MM-DD",
        )
    if not path.is_file():
        dates = [r["date"] for r in get_report_series(system_id)]
        raise NotFound(
            f"no assessment of {system_id!r} on {date}",
            entity_type="report", entity_id=system_id,
            hint=f"it has {', '.join(dates)}" if dates
                 else "call list_reports to see the assessed systems",
        )
    return path


def get_report(system_id: str, date: str) -> dict[str, Any]:
    """`{"success": True, "report": {...}}`. Raises NotFound or Invalid."""
    path = _require_path(system_id, date)
    report = _load_report_file(path)
    if report is None:
        raise Invalid(
            f"the report on disk for {system_id} / {date} does not parse",
            hint="open it with the repair editor, or fix the YAML by hand",
        )
    return {"success": True, "report": report.model_dump()}


def _write(path: Path, report: Report) -> None:
    """Field order comes from the schema's own declaration order, so a file the UI saves
    and a file the skill writes are byte-comparable and diff cleanly."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_yaml(report.model_dump()), encoding="utf-8")


def catalog_reference_errors(report: Report) -> list[str]:
    """Every id in a report that does not resolve to a catalog entry.

    A requirement for something the catalog does not have is a normal, wanted outcome —
    it is how an assessment tells the library what it is missing, and `insights()` reads
    it as the library's own to-do list. The way to record one is `mitigation_id: null`
    plus a `description` saying what is needed. Inventing a plausible-looking id instead
    is a different thing wearing the same clothes: it reads as a cataloged control, it
    resolves to nothing, and nothing downstream can tell the two apart.

    So a non-null id has to be real. Checked on save, against the catalog as it stands —
    reports already on disk are never re-checked, because a control renamed years later
    must not make an archived assessment unreadable.
    """
    from keel.store import get_store

    store = get_store()
    errors: list[str] = []

    def check_mitigation(mid: str | None, where: str) -> None:
        if mid and mid not in store.mitigations:
            errors.append(
                f"{where}: no mitigation {mid!r} in the catalog. If the control is not in "
                f"the library, leave mitigation_id empty and describe the ask instead — "
                f"that is what tells the library what it is missing."
            )

    for i, f in enumerate(report.findings):
        if f.from_catalog and f.id not in store.threats:
            errors.append(
                f"findings[{i}]: marked from_catalog but no threat {f.id!r} is in the "
                f"catalog. Set from_catalog to false if this threat is specific to this system."
            )
        for k, r in enumerate(f.requirements):
            check_mitigation(r.mitigation_id, f"findings[{i}].requirements[{k}]")
        for k, ig in enumerate(f.ignored_mitigations):
            check_mitigation(ig.mitigation_id, f"findings[{i}].ignored_mitigations[{k}]")

    for i, d in enumerate(report.discarded):
        if d.id not in store.threats:
            errors.append(f"discarded[{i}]: no threat {d.id!r} in the catalog")

    return errors


def missing_prerequisites(report: Report) -> list[str]:
    """Advice, not an error: a requirement whose prerequisite the report does not ask for.

    A control that presupposes another one is not verifiable on its own, so shipping the
    ask without its prerequisite hands the product team something they cannot sign off.
    This never blocks a save - the assessor may have good reason, and a half-written
    draft trips it constantly."""
    from keel.store import get_store

    store = get_store()
    asked = {
        r.mitigation_id
        for f in report.findings for r in f.requirements
        if r.mitigation_id and r.included is not False
    }
    out: list[str] = []
    for mid in sorted(asked):
        for prereq in (store.mitigations.get(mid) or {}).get("requires") or []:
            if prereq not in asked:
                out.append(
                    f"{mid} presupposes {prereq}, which this assessment does not ask for - "
                    f"its acceptance criteria cannot be checked without it"
                )
    return out


def save_report(system_id: str, date: str, data: dict[str, Any]) -> dict[str, Any]:
    """Write a report. Editing is always allowed; a final report goes back to draft.

    There used to be three verbs here — save, correct, reopen — and between them they
    asked the reader to classify their own edit before making it. Nobody wants to answer
    "is this a correction or a re-assessment?" before fixing a typo. So: edit whenever
    you like, and touching a final report drops it back to draft, because a document
    that changed after being signed off is not signed off any more. Finalising again is
    the whole ceremony.
    """
    path = _require_path(system_id, date)
    existing = _load_report_file(path)
    if existing is None:
        raise Invalid(
            f"the report on disk for {system_id} / {date} does not parse",
            hint="open it with the repair editor, or fix the YAML by hand",
        )

    try:
        report = Report(**data)
    except ValidationError as exc:
        raise invalid_from_pydantic(
            exc,
            hint="pass the report document itself - system_id, system_name, date, "
                 "assessor, findings. The MCP get_report hands you exactly that; the "
                 "service function wraps it in {success, report}, so unwrap first",
        ) from exc
    # The path IS the identity. Accepting a body that disagrees with it would let a save
    # of one report silently land on another.
    if report.system_id != system_id or report.date != date:
        raise Invalid(
            "system_id and date cannot be changed by a save",
            hint="create_report starts a new one; this call only rewrites this document",
        )

    ref_errors = catalog_reference_errors(report)
    if ref_errors:
        raise Invalid(
            "the assessment names catalog entries that do not exist",
            details=[{"field": None, "message": m} for m in ref_errors],
            hint="for a control the library does not have, leave mitigation_id empty and "
                 "write the ask in description",
        )

    # Status is not the caller's to set here: it is a consequence of editing, and
    # finalising is a separate, deliberate act.
    was_final = existing.status == "final"
    report.status = "draft"
    _write(path, report)
    return {
        "success": True,
        "report": report.model_dump(),
        "reverted_to_draft": was_final,
        "advice": missing_prerequisites(report),
    }


def finalize_report(system_id: str, date: str) -> dict[str, Any]:
    """Freeze a draft. Already-final is not an error — the caller got what it wanted."""
    path = _require_path(system_id, date)
    report = _load_report_file(path)
    if report is None:
        raise Invalid(f"the report on disk for {system_id} / {date} does not parse")
    if report.status != "final":
        report.status = "final"
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
        # Name the half that is actually wrong: the UI highlights by `field`, and a
        # caller sent to fix the id when the date was malformed fixes nothing.
        bad_id = not SYSTEM_ID_RE.match(system_id)
        raise Invalid(
            f"{system_id!r} is not a usable system id" if bad_id
            else f"{date!r} is not a usable date",
            field="system_id" if bad_id else "date",
            hint="lowercase letters, digits and hyphens - 'checkout-agent', not "
                 "'Checkout Agent'" if bad_id else "YYYY-MM-DD",
        )
    if path.exists():
        raise Conflict(
            f"{system_id} already has an assessment dated {date}",
            entity_type="report", entity_id=system_id,
            hint="open it with get_report and save into it, or use another date",
        )
    try:
        report = Report(
            system_id=system_id, system_name=system_name,
            system_description=system_description, date=date, assessor=assessor,
        )
    except ValidationError as exc:
        raise invalid_from_pydantic(exc) from exc
    _write(path, report)
    return {"success": True, "report": report.model_dump()}
