"""Where one assessed system stands against a framework, entry by entry.

Coverage says which library threats answer each entry of a tracked framework. A report
says, for each threat, whether it was found in the system and what is built against it.
Put together they give a standing per entry, and the reason for it is already written in
the report: the risk and its open fixes, or why the threat was ruled out. Nothing here
calls a model.

The frameworks tracked today are threat lists (OWASP, ATLAS, SAIF), not regulations. A
regulation becomes one more coverage file mapped to threats, and this needs no change.
"""
from __future__ import annotations

from typing import Any

from keel.schemas.report import Report
from keel.services import coverage_service, report_service

# Worst first: an entry takes the worst standing among the threats that answer it.
STANDINGS = ("not_met", "waiting", "not_assessed", "met", "does_not_apply")


def threat_standing(report: Report, threat_id: str) -> dict[str, Any]:
    """What the report says about one library threat, with the report's own reason."""
    for f in report.findings:
        if f.id != threat_id:
            continue
        open_fixes = [q for q in f.requirements if q.included and q.coverage_status != "already_covered"]
        if open_fixes:
            return {"threat": threat_id, "standing": "not_met", "severity": f.risk.severity,
                    "likelihood": f.risk.likelihood, "open_fixes": len(open_fixes),
                    "why": f.vulnerability}
        return {"threat": threat_id, "standing": "met", "severity": f.risk.severity,
                "likelihood": f.risk.likelihood, "open_fixes": 0,
                "why": "; ".join(q.coverage_note for q in f.requirements if q.coverage_note) or None}
    for d in report.discarded:
        if d.id == threat_id:
            return {"threat": threat_id, "standing": "does_not_apply", "why": d.reason}
    for p in report.paused:
        if p.id == threat_id:
            return {"threat": threat_id, "standing": "waiting", "why": p.note,
                    "waiting_on": list(p.waiting_on)}
    return {"threat": threat_id, "standing": "not_assessed", "why": None}


def standing(report: Report, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every entry of every framework, with its standing for this system.

    An entry the library leaves out of scope or has no card for keeps that state: the
    assessment could not have looked at it, and saying "not met" would blame the system
    for a gap in the library."""
    out = []
    for src in sources:
        counts = {k: 0 for k in (*STANDINGS, "out_of_scope", "library_gap")}
        entries = []
        for e in src["entries"]:
            if e["state"] == "out_of_scope":
                s, threats = "out_of_scope", []
            elif e["state"] == "gap":
                s, threats = "library_gap", []
            elif not e.get("threats"):
                # Answered by a control alone. An assessment walks threats, so it never
                # reached this entry: not assessed, rather than blamed on the library.
                s, threats = "not_assessed", []
            else:
                threats = [threat_standing(report, t) for t in e["threats"]]
                s = min((t["standing"] for t in threats), key=STANDINGS.index)
            counts[s] += 1
            entries.append({"ref": e["ref"], "title": e["title"], "group": e.get("group"),
                            "standing": s, "threats": threats, "note": e.get("note")})
        out.append({"source": src["source"], "counts": counts, "entries": entries})
    return out


def _sources() -> list[dict[str, Any]]:
    """The framework files as plain data. Not `coverage_service.matrix()`: that also runs
    the library's consistency checks, which costs seconds and adds nothing here."""
    return [{"source": doc.source.model_dump(mode="json"),
             "entries": [e.model_dump(mode="json") for e in doc.entries]}
            for doc in coverage_service.load_sources()]


def system_compliance(system_id: str) -> dict[str, Any]:
    """One system's latest report against every tracked framework."""
    report = next((r for r in report_service._latest_per_system() if r.system_id == system_id), None)
    if report is None:
        from keel.errors import NotFound
        raise NotFound(f"no report for system {system_id!r}")
    return {"system_id": report.system_id, "system_name": report.system_name,
            "date": report.date, "status": report.status,
            "frameworks": standing(report, _sources())}


def all_compliance() -> dict[str, Any]:
    """Every system's latest report, tallies only: the across-systems table."""
    sources = _sources()
    systems = []
    for r in report_service._latest_per_system():
        systems.append({"system_id": r.system_id, "system_name": r.system_name, "date": r.date,
                        "status": r.status,
                        "frameworks": [{"source_id": f["source"]["id"], "counts": f["counts"]}
                                       for f in standing(r, sources)]})
    return {"frameworks": [s["source"] for s in sources], "systems": systems}
