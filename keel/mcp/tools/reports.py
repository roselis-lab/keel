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
from keel.services import report_service

_RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}


@register_tool(annotations=_RO)
async def list_reports(system_id: str | None = None) -> dict:
    """Lists assessed systems, or one system's assessment dates.

    Without system_id: one entry per system — id, name, latest date, how many reports,
    current status. With system_id: that system's dates, newest first.

    Call this at the start of an assessment. A system that has been assessed before has
    a previous report to work from, and re-deriving findings that were already settled
    wastes the specialist's time and loses the reasoning behind the old grades."""
    if system_id:
        return {"series": report_service.get_report_series(system_id)}
    return {"reports": report_service.list_reports()}


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
    you mean to change, and send it back. system_id and date cannot be moved by a save,
    because the path is the report's identity.

    Editing is always allowed, including on a report already finalised; that one simply
    returns to draft, because a document that changed after sign-off is not signed off.
    Status is never set through this call.

    A requirement may ask for something the catalog does not have — that is how an
    assessment tells the library what it is missing. Record it with mitigation_id left
    empty and the ask written in description. Never invent a plausible-looking id: it
    reads as a cataloged control, resolves to nothing, and the save is refused."""
    result = report_service.save_report(system_id, date, report)
    if not result["success"]:
        return {"success": False, "error": result["error"],
                **({"errors": result["errors"]} if "errors" in result else {})}
    out = {"success": True, "system_id": system_id, "date": date,
           "reverted_to_draft": result["reverted_to_draft"]}
    # Advice, never a block: a requirement whose prerequisite is not also being asked for.
    return {**out, "advice": result["advice"]} if result["advice"] else out
