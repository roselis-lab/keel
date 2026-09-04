"""MCP tools package."""
from keel.mcp.registry import get_tool_list, dispatch_tool

# Import tool modules to register their tools.
from keel.mcp.tools import threats  # noqa: F401
from keel.mcp.tools import mitigations  # noqa: F401
from keel.mcp.tools import style_guide  # noqa: F401
from keel.mcp.tools import health  # noqa: F401
from keel.mcp.tools import coverage  # noqa: F401
from keel.mcp.tools import reports  # noqa: F401
from keel.mcp.tools import search  # noqa: F401
from keel.mcp.tools import model  # noqa: F401

__all__ = ["get_tool_list", "dispatch_tool"]
