"""MCP tools for library health and stats."""
from keel.mcp.registry import register_tool
from keel.services.health_service import check_library_health as _check_library_health, get_stats as _get_stats

_RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}


@register_tool(annotations=_RO)
async def check_library_health(session) -> dict:
    """Surface content and integrity gaps: threats missing vulnerability/impact_class, threats
    without mitigations, dangling links, plus style guide coverage."""
    return await _check_library_health(session)


@register_tool(annotations=_RO)
async def get_stats(session) -> dict:
    """Return counts across the library (threats, mitigations, links)."""
    return await _get_stats(session)
