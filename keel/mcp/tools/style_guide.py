"""MCP tools for the authoring style guide (methodology)."""
from typing import Any

from keel.mcp.registry import register_tool
from keel.services import style_guide_service as svc

_RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}


@register_tool(annotations=_RO)
async def get_style_guide(
    entity_type: str | None = None,
    field_name: str | None = None,
) -> dict[str, Any]:
    """Return authoring methodology for an entity / field.

    Granularity:
      - no args                    → full guide (all entities, all fields)
      - entity_type only           → all fields of that entity
      - entity_type + field_name   → just that field
      - field_name without entity  → error (field names are not unique)

    Call this BEFORE writing/updating an entity to follow current methodology.
    """
    if field_name and not entity_type:
        return {
            "error": "field_name requires entity_type (field names are not unique across entities)",
            "success": False,
        }
    if entity_type and field_name:
        try:
            return (await svc.get_field(entity_type, field_name)).model_dump()
        except KeyError as e:
            return {"error": str(e), "success": False}
    if entity_type:
        return (await svc.get_entity(entity_type)).model_dump()
    return (await svc.get_full_guide()).model_dump()


@register_tool(annotations=_WRITE)
async def update_style_guide_field(
    entity_type: str,
    field_name: str,
    purpose: str | None = None,
    content_requirements: list[str] | None = None,
    instructions: list[str] | None = None,
    avoid: list[str] | None = None,
    examples: list[str] | None = None,
    subfields: dict[str, Any] | None = None,
    allowed_values: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Partial update of a style guide field. Only provided slots are written."""
    patch = {k: v for k, v in {
        "purpose": purpose,
        "content_requirements": content_requirements,
        "instructions": instructions,
        "avoid": avoid,
        "examples": examples,
        "subfields": subfields,
        "allowed_values": allowed_values,
    }.items() if v is not None}
    try:
        return (await svc.update_field(
            entity_type, field_name, patch, updated_by="mcp",
        )).model_dump()
    except KeyError as e:
        return {"error": str(e), "success": False}


@register_tool(annotations=_RO)
async def list_incomplete_style_fields() -> dict[str, Any]:
    """List fields whose methodology is empty. Returns {items, count}."""
    items = await svc.list_incomplete()
    return {"items": items, "count": len(items)}


@register_tool(annotations=_WRITE)
async def import_style_guide_yaml(yaml_text: str, mode: str = "merge") -> dict[str, Any]:
    """Import style guide from YAML. mode='merge' (UPSERT) or 'replace' (destructive)."""
    return await svc.import_yaml(yaml_text, mode=mode, updated_by="mcp:import")


@register_tool(annotations=_RO)
async def export_style_guide_yaml() -> dict[str, str]:
    """Export the full style guide as YAML text. Returns {yaml: <text>}."""
    return {"yaml": await svc.export_yaml()}
