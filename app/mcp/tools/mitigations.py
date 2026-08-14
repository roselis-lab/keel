"""MCP tools for mitigation operations."""
from app.mcp.registry import register_tool
from app.services.mitigation_service import (
    list_mitigations as _list_mitigations,
    get_mitigation as _get_mitigation,
    create_mitigation as _create_mitigation,
    update_mitigation as _update_mitigation,
    delete_mitigation as _delete_mitigation,
)
from app.schemas.mitigation import MitigationCreate, MitigationUpdate, MitigationType, RequirementLevel

_RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_DESTRUCTIVE = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False}


@register_tool(annotations=_RO)
async def list_mitigations(session, brief: bool = True, include: list[str] | None = None) -> dict:
    """List mitigations. brief=True → [id, title, type] triples; else include any of:
    description, requirement_level, implementations."""
    return await _list_mitigations(session, brief=brief, include=include)


@register_tool(annotations=_RO)
async def get_mitigation(session, mitigation_id: str) -> dict:
    """Get a mitigation with all fields."""
    return await _get_mitigation(session, mitigation_id)


@register_tool(annotations=_WRITE, entity_type="mitigation")
async def create_mitigation(
    session,
    mitigation_id: str,
    title: str,
    type: MitigationType,
    description: str | None = None,
    requirement_level: RequirementLevel | None = None,
    implementations: list[dict] | None = None,
) -> dict:
    """Create a mitigation. type ∈ {PREVENTIVE_HARD, PREVENTIVE_SOFT, DETECTIVE, CORRECTIVE};
    requirement_level ∈ {MANDATORY, RECOMMENDED}."""
    return await _create_mitigation(session, MitigationCreate(
        id=mitigation_id, title=title, type=type, description=description,
        requirement_level=requirement_level, implementations=implementations,
    ))


@register_tool(annotations=_WRITE, entity_type="mitigation")
async def update_mitigation(
    session,
    mitigation_id: str,
    title: str | None = None,
    type: MitigationType | None = None,
    description: str | None = None,
    requirement_level: RequirementLevel | None = None,
    implementations: list[dict] | None = None,
) -> dict:
    """Update mitigation content. Only provided fields change."""
    return await _update_mitigation(session, mitigation_id, MitigationUpdate(
        title=title, type=type, description=description,
        requirement_level=requirement_level, implementations=implementations,
    ))


@register_tool(annotations=_DESTRUCTIVE)
async def delete_mitigation(session, mitigation_id: str, confirm: bool = False) -> dict:
    """Delete a mitigation and its threat links. Call with confirm=True to apply."""
    return await _delete_mitigation(session, mitigation_id, confirm=confirm)
