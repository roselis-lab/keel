"""One search across the whole library."""
from keel.mcp.registry import register_tool
from keel.services import search_service

_RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}


@register_tool(annotations=_RO)
async def search(q: str, kind: str | None = None, limit: int = 20) -> dict:
    """Searches everything at once: threats, mitigation cards, coverage rows and past
    assessments. Start here — listing a whole entity type to look for one thing is the
    expensive way to ask this.

    Case-insensitive substring over ids, titles and prose (a threat's weaknesses and
    reachability, a card's purpose and scope, a coverage entry's note). Returns
    {hits, count, truncated}; each hit is kind, id, title, which field matched and the
    text around the match — enough to decide what to fetch, not the fetch itself. Follow
    a hit with get_threat, get_mitigation, get_coverage or get_report.

    Searching all four kinds is the point: someone asking whether Keel covers tool
    misuse does not yet know whether the answer is a threat, a control, a row of the
    matrix or a system that already hit it. Narrow with kind (threat, mitigation,
    coverage, report) only once you do know.

    A coverage hit carries its state, so "we have a row for it, still a gap" and "we
    have a threat for it" come back distinguishable in one call."""
    return search_service.search(q, kind=kind, limit=limit)
