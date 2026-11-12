"""MCP tools for assessment reports.

These exist because the assessment skill used to write `reports/*.yaml` with a plain
file write, which walked straight past every check the service applies — most of all the
one that refuses a requirement naming a control the catalog does not have. A gate with an
open door beside it is not a gate.

There is no delete. An assessment is a record of work someone did on a date; an agent
removing one is not a capability worth having, and git is not a substitute for never
having offered it. There is no finalize either: signing a report off is the specialist's
judgment about their own work, made in the UI.
"""
from typing import Any

from keel.mcp.registry import register_tool
from keel.services import org_service, report_service

_RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}


@register_tool(annotations=_RO)
async def list_reports(system_id: str | None = None) -> dict:
    """Lists assessed systems, or one system's assessment dates.

    Without system_id: one entry per system (id, name, latest date, report count,
    status), and `org_facts`: what the organisation keeps between assessments, shared
    platforms and data policies, each with who confirmed it and when. With system_id:
    its dates, newest first.

    Call this first: an earlier report and a stored fact are questions not to ask
    again. Cite a fact by its `ref`."""
    if system_id:
        return {"series": report_service.get_report_series(system_id)}
    return {"reports": report_service.list_reports(), "org_facts": org_service.list_facts()}


@register_tool(annotations=_RO)
async def get_report(system_id: str, date: str) -> dict:
    """Gets one assessment in full: findings with their risk grades and reasoning, the
    controls asked for, what was ruled out and why, and `meta` — how the run went.

    Read the previous report before re-assessing a system: the delta is the point, and a
    finding whose grade has not changed should say so rather than be re-argued."""
    # Unwrapped on purpose: what comes back here is what save_report takes, so a read,
    # an edit and a write are one shape. The service call wraps it; a caller that passed
    # the wrapper straight back used to be refused for missing every top-level field.
    return report_service.get_report(system_id, date)["report"]


@register_tool(annotations=_WRITE)
async def create_report(
    system_id: str,
    system_name: str,
    system_description: str,
    assessor: str,
    date: str | None = None,
) -> dict:
    """Starts an empty draft assessment. Returns {success, system_id, date}.

    system_id is a slug (lowercase, digits, hyphens); date defaults to today. Refuses to
    land on an existing report — open that one with get_report and save into it instead.
    assessor is the person accountable for the judgments, not the agent: "Name <email>"
    from git config."""
    result = report_service.create_report(
        system_id=system_id, system_name=system_name,
        system_description=system_description, assessor=assessor, date=date,
    )
    if not result["success"]:
        return {"success": False, "error": result["error"],
                **({"errors": result["errors"]} if "errors" in result else {})}
    return {"success": True, "system_id": system_id, "date": result["report"]["date"]}


@register_tool(annotations=_WRITE)
async def save_report(system_id: str, date: str, report: dict[str, Any]) -> dict:
    """Writes an assessment. Returns {success, system_id, date, reverted_to_draft}.

    `report` is the whole document, not a patch — read it with get_report, change what
    you mean to change, and send it back. For a few items use update_report. system_id and date cannot be moved by a
    save, because the path is the report's identity.

    Editing is always allowed, including on a report already finalised; that one simply
    returns to draft, because a document that changed after sign-off is not signed off.
    Status is never set through this call.

    A requirement may ask for something the catalog does not have — that is how an
    assessment tells the library what it is missing. Record it with mitigation_id left
    empty and the ask written in description. Never invent a plausible-looking id: it
    reads as a cataloged control, resolves to nothing, and the save is refused.

    Every evidence, question and threat id the report names must be in it, and an
    evidence link must be https, on a host in evidence_hosts, pinned to its commit and
    anchored at the lines; otherwise the save is refused. Each surface ledger outcome
    must name a finding, discard or paused branch of the report, and one
    fingerprint (system, threat id, root cause) is one finding.

    `open` lists what the assessment has not established yet: unanswered questions,
    branches waiting on them, graded findings with no evidence, high findings nobody
    tried to refute, shipped asks with no catalog card and no invariant, enforce_at and
    done_check, and a missing or unwalked surface ledger. While it is non-empty the
    assessment is not done: get the answers (from whoever started you, if you run as a
    subagent) and continue; do not hand back a link as if it were finished."""
    return _saved(system_id, date, report_service.save_report(system_id, date, report))


@register_tool(annotations=_WRITE)
async def update_report(
    system_id: str, date: str, changes: dict[str, Any] | None = None,
    remove: dict[str, list[Any]] | None = None,
) -> dict:
    """Changes part of an assessment; returns what save_report returns, `open` included.
    Prefer it to save_report while writing: reprinting the whole report each pass is the
    costliest output of a run.

    `changes` holds only what you add or change. In findings, paused, discarded,
    surfaces, open_questions and evidence an item replaces the one with the same id or is
    appended; any other field is replaced whole. `remove` drops items by id:
    {"open_questions": ["Q3"]}. Same checks as save_report; a refused update changes
    nothing."""
    return _saved(system_id, date, report_service.update_report(system_id, date, changes, remove))


def _saved(system_id: str, date: str, result: dict[str, Any]) -> dict:
    if not result["success"]:
        return {"success": False, "error": result["error"],
                **({"errors": result["errors"]} if "errors" in result else {})}
    out = {"success": True, "system_id": system_id, "date": date,
           "reverted_to_draft": result["reverted_to_draft"]}
    if result["open"]:
        out["open"] = result["open"]
    # Advice, never a block: a missing prerequisite, a harm or source outside the threat.
    return {**out, "advice": result["advice"]} if result["advice"] else out
