"""MCP tool for library health."""
from keel.mcp.registry import register_tool
from keel.services.health_service import check_library_health as _check_library_health

_RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}


@register_tool(annotations=_RO)
async def check_library_health() -> dict:
    """How the library is doing, in three separate tiers.

    `errors`: a record failed its schema at load and is not being served — each carries
    file, entity_id, field, message, dropped. `warnings`: advisory (over-graded link
    strength, missing references, unused vocabulary); a half-authored draft may
    legitimately trip them. `issues`: content gaps in records that loaded fine —
    threats_missing_weaknesses, threats_missing_harm, threats_without_mitigation.

    Also returns `stats`, `style_guide_coverage` and `implementation_coverage_counts`."""
    return await _check_library_health()


@register_tool(annotations=_RO)
async def get_vocabulary() -> dict:
    """The four frozen vocabularies, with what each value means.

    `harm`, `surface`, `source` and `components` are enforced as enums everywhere, so a
    tool schema shows you the allowed tokens but not what they stand for. This returns
    `{harm: {value: {name, desc}}, ...}` — read it once before classifying a threat
    rather than guessing which component a weakness sits on."""
    from keel.store import get_store

    return get_store().vocabulary
