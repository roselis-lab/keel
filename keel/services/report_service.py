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

from urllib.parse import urlsplit

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


def _evidence_url_error(url: str, commit: str | None) -> str | None:
    """Why this permalink is refused, or None. Structure only: scheme, host, pin, anchor."""
    from keel.config import settings

    parts = urlsplit(url)
    if parts.scheme != "https":
        return "is not https"
    host = (parts.hostname or "").lower()
    allowed = {h.lower() for h in settings.evidence_hosts}
    if host not in allowed:
        return (f"points to {host or 'no host'}, which is not in evidence_hosts "
                f"({', '.join(sorted(allowed)) or 'empty'})")
    if parts.username or parts.password:
        return "carries credentials"
    if parts.query:
        return "carries a query string; a permalink to lines needs none"
    if not commit or commit not in parts.path.split("/"):
        return "is not pinned to the entry's commit: a link to a branch moves"
    if not parts.fragment:
        return "has no line anchor: it should open at the lines, not at the file"
    return None


def structure_errors(report: Report) -> list[str]:
    """Links inside a report that do not hold together. Refused on save.

    Evidence ids, question ids and threat ids are how the parts of a report point at
    each other; a pointer to nothing reads as support that is not there. A branch
    waiting on a question that already has its answer is refused too: the answer is
    in, so the branch is graded or discarded now, not left waiting.
    """
    errors: list[str] = []
    ev_ids = [e.id for e in report.evidence]
    for dup in sorted({i for i in ev_ids if ev_ids.count(i) > 1}):
        errors.append(f"evidence: id {dup} is used more than once")
    known_ev = set(ev_ids)
    q_by_id = {q.id: q for q in report.open_questions}
    if len(q_by_id) != len(report.open_questions):
        errors.append("open_questions: a question id is used more than once")

    for i, e in enumerate(report.evidence):
        if e.url:
            why = _evidence_url_error(e.url, e.commit)
            if why:
                errors.append(f"evidence[{i}] (id {e.id}): the link {why}")

    def check_refs(refs: list[int], where: str) -> None:
        for ref in refs:
            if ref not in known_ev:
                errors.append(f"{where}: evidence {ref} is not in the evidence list")

    for i, f in enumerate(report.findings):
        check_refs(f.evidence, f"findings[{i}]")
        if f.risk_today is not None and f.deployment in (None, "live"):
            errors.append(
                f"findings[{i}] ({f.id}): risk_today is for a feature that is not live yet; "
                "a live one has a single grade"
            )
    for i, d in enumerate(report.discarded):
        check_refs(d.evidence, f"discarded[{i}]")

    # One fingerprint, one finding: two cards for the same defect of the same threat in
    # one report are a duplicate, whatever their wording.
    prints = [fingerprint(report.system_id, f.id, f.root_cause) for f in report.findings]
    for dup in sorted({p for p in prints if p and prints.count(p) > 1}):
        errors.append(f"findings: {dup} appears more than once; one defect is one finding")

    finding_ids = {f.id for f in report.findings}
    for i, d in enumerate(report.discarded):
        if d.by == "review" and d.id in finding_ids and fingerprint(report.system_id, d.id, d.root_cause) in prints:
            errors.append(f"discarded[{i}]: {d.id} was refuted in review and is also graded; it is one of the two")

    s_ids = [s.id for s in report.surfaces]
    for dup in sorted({i for i in s_ids if s_ids.count(i) > 1}):
        errors.append(f"surfaces: id {dup} is used more than once")
    branch_ids = finding_ids | {d.id for d in report.discarded} | {p.id for p in report.paused}
    for i, s in enumerate(report.surfaces):
        check_refs(s.evidence, f"surfaces[{i}]")
        for oid in s.outcome:
            if oid not in branch_ids:
                errors.append(
                    f"surfaces[{i}] ({s.id}): outcome {oid} is not a finding, discard "
                    "or paused branch of this report"
                )

    decided = {f.id for f in report.findings} | {d.id for d in report.discarded}
    for i, p in enumerate(report.paused):
        if p.id in decided:
            errors.append(f"paused[{i}]: {p.id} is also graded or discarded; it is one of the three")
        for qid in p.waiting_on:
            q = q_by_id.get(qid)
            if q is None:
                errors.append(f"paused[{i}]: waits on {qid}, which is not in open_questions")
            elif (q.answer or "").strip():
                errors.append(
                    f"paused[{i}]: {qid} has its answer, so {p.id} no longer waits - "
                    "grade it as a finding or discard it by its reachability condition"
                )
    return errors


def open_items(report: Report) -> list[str]:
    """What still stands between this report and being finished. Blocks finalizing.

    A question without an answer, a branch waiting on one, and a graded finding with no
    evidence behind it are all the same thing: an assessment that went past something it
    had not established.
    """
    out: list[str] = []
    for q in report.open_questions:
        if not (q.answer or "").strip():
            out.append(f"{q.id} is not answered: {q.question}")
    for p in report.paused:
        out.append(f"{p.id} waits on {', '.join(p.waiting_on)}")
    for i, f in enumerate(report.findings):
        if not f.evidence:
            out.append(f"findings[{i}] ({f.id}) is graded with no evidence entry behind it")
        if f.risk.severity == "high" and f.review is None:
            out.append(
                f"findings[{i}] ({f.id}) is graded high and nobody who did not raise it has "
                "tried to refute it"
            )
        for ri, r in enumerate(f.requirements):
            # A catalog card carries purpose, locus and validation; an ask with no card
            # has only what is written here.
            if not r.included or r.coverage_status == "already_covered" or r.mitigation_id:
                continue
            missing = [k for k in ("invariant", "enforce_at", "done_check") if not (getattr(r, k) or "").strip()]
            if missing:
                out.append(
                    f"findings[{i}] ({f.id}) requirement {ri + 1} ships without "
                    f"{', '.join(missing)}: nobody can build or accept it as written"
                )
    if not report.surfaces:
        out.append("no surface ledger: list every entry point, tool and data path the system has")
    for s in report.surfaces:
        if not s.outcome and not (s.note or "").strip():
            out.append(f"surface {s.id} ({s.name}) was listed but not walked: no outcome and no note")
    return out


def ruled_out_before(report: Report) -> list[str]:
    """Advice: a finding that an earlier assessment of this system ruled out, raised again.

    Allowed, because the system or a fact can change, but the change has to be named.
    Without this, a discard quietly expires the next time someone runs the assessment,
    and the reasoning that ruled it out is re-derived or lost. A discard with a root cause
    matches on the fingerprint; one without matches on the threat id.
    """
    earlier = [
        r for r in _load_system_reports(_reports_dir() / report.system_id)
        if r.date < report.date
    ]
    seen: dict[str, tuple[str, str, str]] = {}
    for r in sorted(earlier, key=lambda r: r.date):
        for d in r.discarded:
            key = fingerprint(r.system_id, d.id, d.root_cause) or d.id
            seen[key] = (r.date, d.by, d.reason)
    out: list[str] = []
    for i, f in enumerate(report.findings):
        hit = seen.get(fingerprint(report.system_id, f.id, f.root_cause) or "") or seen.get(f.id)
        if hit:
            how = "refuted in review" if hit[1] == "review" else "ruled out by reachability"
            out.append(
                f"findings[{i}] ({f.id}) was {how} on {hit[0]}: {hit[2]} Say in delta "
                "which new fact brings it back"
            )
    return out


def cards_without_checks(report: Report) -> list[str]:
    """Advice: a shipped catalog requirement whose card says nothing about how to accept it.

    The card is where purpose, locus and validation live, so filling it serves every
    system that ships the control. Until then the assessment can say it for this system
    in `done_check`.
    """
    from keel.store import get_store

    store = get_store()
    out: list[str] = []
    for i, f in enumerate(report.findings):
        for r in f.requirements:
            if not r.mitigation_id or not r.included or r.coverage_status == "already_covered":
                continue
            card = store.mitigations.get(r.mitigation_id) or {}
            if not card.get("validation") and not (r.done_check or "").strip():
                out.append(
                    f"findings[{i}] ({f.id}): {r.mitigation_id} has no validation on its card; "
                    "write done_check for this system, and the card is worth filling"
                )
    return out


def catalog_mismatches(report: Report) -> list[str]:
    """Advice: a finding whose harm or source is outside its catalog threat's values.

    Sometimes right (the catalog can be wrong, and that is how the library learns it is),
    so it never blocks. But it is said out loud, because a different harm usually means a
    different threat, and an override nobody noticed is how a misfiled finding gets in.
    """
    from keel.store import get_store

    store = get_store()
    out: list[str] = []
    for i, f in enumerate(report.findings):
        t = store.threats.get(f.id) if f.from_catalog else None
        if not t:
            continue
        if t.get("harm") and f.harm != t["harm"]:
            out.append(
                f"findings[{i}] ({f.id}): harm {f.harm!r}, the catalog threat says "
                f"{t['harm']!r}. If the harm really differs, it may be a different threat"
            )
        sources = t.get("source") or []
        if sources and f.source.who not in sources:
            out.append(
                f"findings[{i}] ({f.id}): source {f.source.who!r} is not among the catalog "
                f"threat's sources ({', '.join(sources)})"
            )
    return out


def fingerprint(system_id: str, finding_id: str, root_cause: str | None) -> str | None:
    """The finding's identity across re-assessments and across systems that share it."""
    return f"{system_id}/{finding_id}/{root_cause}" if root_cause else None


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


def check_report(system_id: str, date: str, data: dict[str, Any]) -> dict[str, Any]:
    """What save_report would refuse for this body, without writing anything, so the
    editor can say it as you type. `errors` with a field are the schema's; the ones
    without are about the report as a whole. `advice` never blocks a save."""
    try:
        report = Report(**data)
    except ValidationError as exc:
        errors = [
            {"field": ".".join(str(x) for x in e["loc"]), "msg": e["msg"]}
            for e in exc.errors()
        ]
        return {"ok": False, "errors": errors, "advice": []}
    whole = catalog_reference_errors(report) + structure_errors(report)
    if report.system_id != system_id or report.date != date:
        whole.insert(0, "system_id and date cannot be changed by a save")
    advice = (missing_prerequisites(report) + catalog_mismatches(report)
              + ruled_out_before(report) + cards_without_checks(report))
    return {
        "ok": not whole,
        "errors": [{"field": "", "msg": m} for m in whole],
        "advice": [{"field": "", "msg": m} for m in advice],
    }


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
    struct_errors = structure_errors(report)
    if struct_errors:
        raise Invalid(
            "parts of the assessment point at things that are not there",
            details=[{"field": None, "message": m} for m in struct_errors],
            hint="every evidence, question and threat id a report names must be in it; an "
                 "evidence link must be https, on a host in evidence_hosts, pinned to the "
                 "entry's commit and anchored at the lines",
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
        # Not done while this is non-empty: the assessor does not leave these for later.
        "open": open_items(report),
        "advice": missing_prerequisites(report) + catalog_mismatches(report)
        + ruled_out_before(report) + cards_without_checks(report),
    }


# The report's lists whose items carry an `id`. A change to one of them merges by id; any
# other top-level field is replaced as a whole.
LIST_SECTIONS = ("findings", "paused", "discarded", "surfaces", "open_questions", "evidence")


def update_report(system_id: str, date: str, changes: dict[str, Any] | None = None,
                  remove: dict[str, list[Any]] | None = None) -> dict[str, Any]:
    """Change part of a report and save it through the same checks as save_report.

    An assessment is written in passes: a finding, then its evidence, then an answer. Sending
    the whole document back each time made the agent reprint everything it had already
    written, and output is the most expensive token there is. Here an item in a list section
    replaces the item with the same id or is appended; `remove` drops items by id.
    """
    data = get_report(system_id, date)["report"]
    for key, value in (changes or {}).items():
        if key not in LIST_SECTIONS:
            data[key] = value
            continue
        if not isinstance(value, list) or not all(isinstance(i, dict) and "id" in i for i in value):
            raise Invalid(
                f"{key} must be a list of items that each carry an id",
                hint=f"send only the {key} items you add or change, each with its id",
            )
        items = {item["id"]: item for item in data.get(key) or []}
        for item in value:
            items[item["id"]] = item
        data[key] = list(items.values())
    for key, gone in (remove or {}).items():
        if key not in LIST_SECTIONS:
            raise Invalid(f"remove works on {', '.join(LIST_SECTIONS)}, not {key!r}",
                          hint="to clear any other field, set it in changes")
        have = {item["id"] for item in data.get(key) or []}
        missing = [i for i in gone if i not in have]
        if missing:
            raise Invalid(f"{key} has no item with id {', '.join(map(str, missing))}",
                          hint="get_report shows the ids that are there")
        data[key] = [item for item in data[key] if item["id"] not in set(gone)]
    return save_report(system_id, date, data)


def finalize_report(system_id: str, date: str) -> dict[str, Any]:
    """Freeze a draft. Already-final is not an error — the caller got what it wanted."""
    path = _require_path(system_id, date)
    report = _load_report_file(path)
    if report is None:
        raise Invalid(f"the report on disk for {system_id} / {date} does not parse")
    blockers = open_items(report)
    if report.status != "final" and blockers:
        raise Invalid(
            "the assessment still goes past things it has not established",
            details=[{"field": None, "message": m} for m in blockers],
            hint="answer the open questions, finish the paused branches, and back every "
                 "graded finding with evidence, then finalize",
        )
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
