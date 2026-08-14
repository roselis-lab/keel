"""MCP tools package."""
from app.mcp.registry import get_tool_list, dispatch_tool

# Import tool modules to register their tools.
from app.mcp.tools import threats  # noqa: F401
from app.mcp.tools import mitigations  # noqa: F401
from app.mcp.tools import style_guide  # noqa: F401
from app.mcp.tools import health  # noqa: F401

__all__ = ["get_tool_list", "dispatch_tool"]
