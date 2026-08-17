"""MCP tools for threat operations."""
from typing import Any

from keel.mcp.registry import register_tool
from keel.schemas.threat import Harm, Source, Strength, Surface, ThreatCreate, ThreatUpdate
from keel.services.threat_service import (
    list_threats as _list_threats,
    get_threat as _get_threat,
    create_threat as _create_threat,
    update_threat as _update_threat,
    delete_threat as _delete_threat,
    batch_update_threats as _batch_update_threats,
    add_mitigation as _add_mitigation,
    remove_mitigation as _remove_mitigation,
)

_RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_DESTRUCTIVE = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False}


@register_tool(annotations=_RO)
async def list_threats(brief: bool = True, include: list[str] | None = None) -> dict:
    """List threats. brief=True → [id, title] pairs; else include any of:
    harm, surface, source, weaknesses, reachability, mitigations, references, tags."""
    return await _list_threats(brief=brief, include=include)


@register_tool(annotations=_RO)
async def get_threat(threat_id: str) -> dict:
    """Get a threat with weaknesses, harm, surface, source, reachability, and mitigations."""
    return await _get_threat(threat_id)


@register_tool(annotations=_WRITE, entity_type="threat")
async def create_threat(
    threat_id: str,
    title: str,
    harm: Harm,
    weaknesses: list[dict[str, Any]],
    reachability: str,
    surface: list[Surface] | None = None,
    source: list[Source] | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Create a threat. `weaknesses` is a list of {component, text, nature?}; each weakness is an
    architectural condition (cause+where+defect), NOT a technique or a consequence. `harm` is the
    consequence class; `reachability` is the rule-out gate ('NOT applicable if…'). Follow the style
    guide before authoring. Link mitigations via add_threat_mitigation; add references via update."""
    return await _create_threat(ThreatCreate(
        id=threat_id, title=title, harm=harm, weaknesses=weaknesses, reachability=reachability,
        surface=surface or [], source=source or [], tags=tags or [],
    ))


@register_tool(annotations=_WRITE, entity_type="threat")
async def update_threat(
    threat_id: str,
    title: str | None = None,
    harm: Harm | None = None,
    weaknesses: list[dict[str, Any]] | None = None,
    reachability: str | None = None,
    surface: list[Surface] | None = None,
    source: list[Source] | None = None,
    references: list[dict[str, Any]] | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Update threat content. Only provided fields change."""
    return await _update_threat(threat_id, ThreatUpdate(
        title=title, harm=harm, weaknesses=weaknesses, reachability=reachability,
        surface=surface, source=source, references=references, tags=tags,
    ))


@register_tool(annotations=_DESTRUCTIVE)
async def delete_threat(threat_id: str, confirm: bool = False) -> dict:
    """Delete a threat and its mitigation links. Call with confirm=True to apply."""
    return await _delete_threat(threat_id, confirm=confirm)


@register_tool(annotations=_WRITE, entity_type="threat")
async def batch_update_threats(updates: list[dict], confirm: bool = False) -> dict:
    """Batch update threats. Each item: {threat_id, ...fields}. confirm=True to apply."""
    return await _batch_update_threats(updates, confirm=confirm)


@register_tool(annotations=_WRITE)
async def add_threat_mitigation(
    threat_id: str, mitigation_id: str, strength: Strength, rationale: str,
) -> dict:
    """Link a mitigation to a threat. strength ∈ {gating (blocks), soft (only lowers likelihood)};
    a soft control does not close the threat."""
    return await _add_mitigation(threat_id, mitigation_id, strength, rationale)


@register_tool(annotations=_WRITE)
async def remove_threat_mitigation(threat_id: str, mitigation_id: str) -> dict:
    """Unlink a mitigation from a threat."""
    return await _remove_mitigation(threat_id, mitigation_id)
