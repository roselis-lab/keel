"""MCP tools for threat operations."""
from app.mcp.registry import register_tool
from app.services.threat_service import (
    list_threats as _list_threats,
    get_threat as _get_threat,
    create_threat as _create_threat,
    update_threat as _update_threat,
    delete_threat as _delete_threat,
    batch_update_threats as _batch_update_threats,
    add_mitigation as _add_mitigation,
    remove_mitigation as _remove_mitigation,
)
from app.schemas.threat import ThreatCreate, ThreatUpdate

_RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_DESTRUCTIVE = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False}


@register_tool(annotations=_RO)
async def list_threats(session, brief: bool = True, include: list[str] | None = None) -> dict:
    """List threats. brief=True → [id, title] pairs; else include any of:
    description, impact_class, vulnerability, reachability, tags, mitigations."""
    return await _list_threats(session, brief=brief, include=include)


@register_tool(annotations=_RO)
async def get_threat(session, threat_id: str) -> dict:
    """Get a threat with description, impact_class, vulnerability, reachability,
    tags and linked mitigations."""
    return await _get_threat(session, threat_id)


@register_tool(annotations=_WRITE, entity_type="threat")
async def create_threat(
    session,
    threat_id: str,
    title: str,
    description: str | None = None,
    impact_class: str | None = None,
    vulnerability: list[str] | None = None,
    reachability: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Create a threat. The catalog is impact-centric: `impact_class` is the
    asset/damage anchor (strict enum); `vulnerability` (prose list) is HOW the
    system is exploitable — each item one recognizable pattern (cause+where+weakness);
    `reachability` (prose) is the carve-outs when it is NOT a live path (reachability
    + asset materiality, un-mitigated). Follow the style guide before authoring."""
    return await _create_threat(session, ThreatCreate(
        id=threat_id, title=title, description=description,
        impact_class=impact_class, vulnerability=vulnerability,
        reachability=reachability, tags=tags,
    ))


@register_tool(annotations=_WRITE, entity_type="threat")
async def update_threat(
    session,
    threat_id: str,
    title: str | None = None,
    description: str | None = None,
    impact_class: str | None = None,
    vulnerability: list[str] | None = None,
    reachability: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Update threat content. Only provided fields change."""
    return await _update_threat(session, threat_id, ThreatUpdate(
        title=title, description=description, impact_class=impact_class,
        vulnerability=vulnerability, reachability=reachability, tags=tags,
    ))


@register_tool(annotations=_DESTRUCTIVE)
async def delete_threat(session, threat_id: str, confirm: bool = False) -> dict:
    """Delete a threat and its mitigation links. Call with confirm=True to apply."""
    return await _delete_threat(session, threat_id, confirm=confirm)


@register_tool(annotations=_WRITE, entity_type="threat")
async def batch_update_threats(session, updates: list[dict], confirm: bool = False) -> dict:
    """Batch update threats. Each item: {threat_id, ...fields}. confirm=True to apply."""
    return await _batch_update_threats(session, updates, confirm=confirm)


@register_tool(annotations=_WRITE, entity_type="threat_mitigation")
async def add_threat_mitigation(session, threat_id: str, mitigation_id: str, rationale: str) -> dict:
    """Link a mitigation to a threat with a rationale (UPSERT)."""
    return await _add_mitigation(session, threat_id, mitigation_id, rationale)


@register_tool(annotations=_WRITE)
async def remove_threat_mitigation(session, threat_id: str, mitigation_id: str) -> dict:
    """Unlink a mitigation from a threat."""
    return await _remove_mitigation(session, threat_id, mitigation_id)
