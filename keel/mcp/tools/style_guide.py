"""MCP tools for the authoring style guide — the bar every catalog field has to meet.

The style guide has no create or delete: its fields are not content, they are the schema's
own fields, so the set is fixed by `keel/schemas/` and only the guidance about them is
written here.
"""
from typing import Any

from keel.mcp.registry import register_tool
from keel.services import style_guide_service as svc

_RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}

SLOTS = "purpose, content_requirements, instructions, avoid, examples, subfields, allowed_values"
ENTITY_SLOTS = "purpose, instructions, avoid"


@register_tool(annotations=_RO)
async def get_style_guide(
    entity_type: str | None = None,
    field_name: str | None = None,
    incomplete_only: bool = False,
) -> dict[str, Any]:
    """Gets the authoring bar: purpose, what a value must contain, what to avoid,
    examples. Read it BEFORE writing anything it covers.

    Scope it — the whole guide is thousands of tokens. entity_type + field_name is one
    field's bar. entity_type alone adds the `entity` block: the bar for the RECORD —
    whether this is one record or part of one, and what to settle before any field. Read
    that before creating anything; a field-scoped call does not return it. Neither
    argument gives everything, rarely right. incomplete_only=True lists unwritten bars.

    entity_type: threat, mitigation, weakness, mitigation_link, implementation.
    field_name without entity_type is an error; names repeat across entities."""
    if incomplete_only:
        items = await svc.list_incomplete()
        if entity_type:
            items = [i for i in items if i["entity_type"] == entity_type]
        return {"items": items, "count": len(items)}
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
async def update_style_guide(
    entity_type: str, patch: dict[str, Any], field_name: str | None = None
) -> dict[str, Any]:
    """Updates the authoring bar. Only the slots in `patch` change; list slots are
    REPLACED, not appended to. `field_name` scopes it as on get_style_guide.

    With one: that field's bar. Slots: purpose, content_requirements, instructions,
    avoid (named failure modes, not vague warnings), examples, subfields, allowed_values.

    Without one: the bar for the RECORD, the part no field can carry. Slots: purpose
    (what one record of this entity is), instructions (what to settle before any field,
    above all whether this is one record or part of one), avoid.

    This edits the rules, not the catalog. Check a requirement is not already another
    field's job, nor a record-level rule pushed into a field: two places asking the same
    thing is how one goes stale."""
    try:
        if field_name is None:
            row = await svc.update_entity(entity_type, patch, updated_by="mcp")
            return {"success": True, "entity_type": entity_type, "scope": "record",
                    "changed": sorted(patch),
                    "entity": row.model_dump() if row else None}
        field = await svc.update_field(entity_type, field_name, patch, updated_by="mcp")
    except KeyError as e:
        return {"success": False, "error": str(e), "allowed_slots": SLOTS,
                "allowed_entities": ", ".join(svc.ENTITY_ORDER)}
    except Exception as e:  # a slot that does not exist, or a bad shape
        return {"success": False, "error": str(e),
                "allowed_slots": SLOTS if field_name else ENTITY_SLOTS}
    return {"success": True, "entity_type": entity_type, "field_name": field.field_name,
            "scope": "field", "changed": sorted(patch)}
