"""Style guide tool-name -> entity-type registry and pointer builder.

Style methodology is intentionally NOT inlined into tool descriptions — that
bloats tools/list and dilutes in long contexts. Instead, write-tools get a short
pointer telling the model to fetch fresh methodology via the `get_style_guide`
MCP tool right before writing.
"""
from __future__ import annotations


# Tool name -> entity type; populated by the registry decorator.
TOOL_ENTITY_TYPES: dict[str, str] = {}


def register_tool_entity(tool_name: str, entity_type: str) -> None:
    TOOL_ENTITY_TYPES[tool_name] = entity_type


def get_tool_style_pointer(tool_name: str) -> str:
    """Return a short reminder for the LLM to fetch methodology before writing.

    Synchronous — no DB call. Actual content is served by `get_style_guide`
    when the model decides to fetch it.
    """
    entity_type = TOOL_ENTITY_TYPES.get(tool_name)
    if not entity_type:
        return ""
    return (
        f"\n\nStyle guide is mandatory for this tool. Do not author or edit a "
        f"{entity_type} without first calling "
        f"`get_style_guide(entity_type=\"{entity_type}\")` and following it — it defines "
        f"required field formats, content rules, avoid-lists, and examples. If you have "
        f"not read it this turn, read it before writing. Per field: "
        f"`get_style_guide(entity_type=\"{entity_type}\", field_name=\"<name>\")`."
    )
