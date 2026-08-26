"""MCP tools for mitigation operations."""
from keel.mcp.registry import register_tool
from keel.schemas.mitigation import (
    MitigationClass,
    MitigationCreate,
    MitigationStatus,
    MitigationUpdate,
)
from keel.services.mitigation_service import (
    list_mitigations as _list_mitigations,
    get_mitigation as _get_mitigation,
    create_mitigation as _create_mitigation,
    update_mitigation as _update_mitigation,
    delete_mitigation as _delete_mitigation,
)

_RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_DESTRUCTIVE = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False}


@register_tool(annotations=_RO)
async def list_mitigations(brief: bool = True, include: list[str] | None = None) -> dict:
    """List mitigations. brief=True → [id, name, mitigation_class] triples; else include any of:
    status, purpose, scope, control_mechanism, failure_behavior, telemetry, anti_patterns,
    validation, faq, review, maintainer, locus, formal_implementation_risk."""
    return await _list_mitigations(brief=brief, include=include)


@register_tool(annotations=_RO)
async def get_mitigation(mitigation_id: str) -> dict:
    """Get a mitigation card with all fields."""
    return await _get_mitigation(mitigation_id)


@register_tool(annotations=_WRITE, entity_type="mitigation")
async def create_mitigation(
    mitigation_id: str,
    name: str,
    mitigation_class: MitigationClass,
    status: MitigationStatus | None = None,
    purpose: str | None = None,
    scope: str | None = None,
    control_mechanism: str | None = None,
    failure_behavior: str | None = None,
) -> dict:
    """Create a mitigation card. mitigation_class ∈ {gating_control, detector, process,
    evidential_mitigation, corrective} — it is a switch that sets how control_mechanism and
    failure_behavior are read. Rich fields (telemetry, anti_patterns, validation, faq, review,
    locus, ...) are authored via the catalog YAML."""
    return await _create_mitigation(MitigationCreate(
        id=mitigation_id, name=name, mitigation_class=mitigation_class, status=status,
        purpose=purpose, scope=scope, control_mechanism=control_mechanism,
        failure_behavior=failure_behavior,
    ))


@register_tool(annotations=_WRITE, entity_type="mitigation")
async def update_mitigation(
    mitigation_id: str,
    name: str | None = None,
    mitigation_class: MitigationClass | None = None,
    status: MitigationStatus | None = None,
    purpose: str | None = None,
    scope: str | None = None,
    control_mechanism: str | None = None,
    failure_behavior: str | None = None,
) -> dict:
    """Update mitigation card content. Only provided fields change."""
    return await _update_mitigation(mitigation_id, MitigationUpdate(
        name=name, mitigation_class=mitigation_class, status=status, purpose=purpose,
        scope=scope, control_mechanism=control_mechanism, failure_behavior=failure_behavior,
    ))


@register_tool(annotations=_DESTRUCTIVE)
async def delete_mitigation(mitigation_id: str, confirm: bool = False) -> dict:
    """Delete a mitigation and its threat links. Call with confirm=True to apply."""
    return await _delete_mitigation(mitigation_id, confirm=confirm)
