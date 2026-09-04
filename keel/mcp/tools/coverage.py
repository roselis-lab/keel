"""MCP tools for the coverage matrix — Keel's claim about the sources it tracks."""
from keel.mcp.registry import register_tool
from keel.services import coverage_service

_RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}


@register_tool(annotations=_RO)
async def get_coverage(source_id: str | None = None, state: str | None = None) -> dict:
    """Answers "does Keel cover X?" against the tracked sources, each pinned to a
    release. Every entry of that release carries one state:

      covered      — with the Keel ids answering it, sometimes in a shape of its own that
                     the note explains (prompt injection is a mechanism across many
                     threats, not one entry)
      out_of_scope — with reasoning. Keel's boundary, not a disagreement with the source
      gap          — nothing answers it yet

    Read this before saying Keel is missing something: the first two look like omissions
    if you only search the catalog.

    Called with no arguments this returns counts per source and no rows, because the
    full matrix is 130+ entries and the count usually answers the question. Ask for rows
    with source_id (owasp-llm, owasp-agentic, mitre-atlas, google-saif) or state;
    state="gap" is the authoring queue."""
    data = coverage_service.matrix()
    # Rows only when asked for. The whole matrix is 130+ entries and the counts answer
    # most questions on their own, so handing it over by default spends the caller's
    # context on rows it did not ask about.
    want_rows = bool(source_id or state)
    out = []
    for s in data["sources"]:
        if source_id and s["source"]["id"] != source_id:
            continue
        row = {
            "id": s["source"]["id"],
            "title": s["source"]["title"],
            "version": s["source"]["version"],
            "url": s["source"]["url"],
            "counts": s["counts"],
            "imported": s["imported"],
            "entry_count": s["source"]["entry_count"],
        }
        if want_rows:
            entries = s["entries"]
            if state:
                entries = [e for e in entries if e["state"] == state]
            row["entries"] = entries
        out.append(row)
    if source_id and not out:
        known = [s["source"]["id"] for s in data["sources"]]
        return {"success": False,
                "error": f"no tracked source {source_id!r}. Known: {', '.join(known)}"}
    result = {"sources": out, "warnings": data["warnings"]}
    if not want_rows:
        result["entries_omitted"] = (
            "counts only — pass source_id or state to get the rows themselves"
        )
    return result


@register_tool(annotations=_WRITE)
async def set_coverage_entry(
    source_id: str,
    ref: str,
    state: str,
    threats: list[str] | None = None,
    mitigations: list[str] | None = None,
    note: str | None = None,
) -> dict:
    """Moves one row of the matrix — the write that follows every authored threat. See
    get_coverage for what the three states mean.

    Enforced: covered needs at least one id, out_of_scope needs a note and no ids, gap
    takes no ids, and every id must exist in the catalog — a coverage claim is a public
    statement. Entries, source pins and list sizes are not editable here; they are claims
    about the outside world that a person checks against the source.

    Changing state without passing `note` drops the old one, since reasoning written
    about a different answer is usually wrong for the new one."""
    return coverage_service.set_entry(
        source_id, ref, state, threats=threats, mitigations=mitigations, note=note
    )
