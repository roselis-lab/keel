"""MCP tool registry — decorator-based registration with auto-generated inputSchema.

Style guide pointers are appended to write-tool descriptions at `tools/list`
time; decorators only record the entity_type.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, get_type_hints

from pydantic import Field, create_model

from keel.errors import KeelError

from keel.lib.style_guide import register_tool_entity, get_tool_style_pointer


@dataclass
class ToolDefinition:
    handler: Callable
    input_schema: dict[str, Any]
    description: str
    entity_type: str | None = None
    annotations: dict[str, bool] = field(default_factory=dict)
    output_schema: dict[str, Any] | None = None


TOOL_REGISTRY: dict[str, ToolDefinition] = {}


def register_tool(
    fn: Callable | None = None,
    *,
    annotations: dict[str, bool] | None = None,
    output_schema: dict[str, Any] | None = None,
    param_descriptions: dict[str, str] | None = None,
    entity_type: str | None = None,
) -> Callable:
    """Register an async function as an MCP tool.

    Usable as @register_tool or @register_tool(annotations=..., entity_type="threat").
    """
    def decorator(func: Callable) -> Callable:
        schema = build_input_schema(func, param_descriptions or {})
        doc = (func.__doc__ or "").strip()

        if entity_type:
            register_tool_entity(func.__name__, entity_type)

        TOOL_REGISTRY[func.__name__] = ToolDefinition(
            handler=func,
            input_schema=schema,
            description=doc,
            entity_type=entity_type,
            annotations=annotations or {},
            output_schema=output_schema,
        )
        return func

    if fn is not None:
        return decorator(fn)
    return decorator


def build_input_schema(
    fn: Callable,
    param_descriptions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build an MCP-compatible inputSchema from a function signature."""
    sig = inspect.signature(fn)
    hints = get_type_hints(fn, include_extras=True)
    descriptions = param_descriptions or {}

    field_definitions: dict[str, Any] = {}
    for name, param in sig.parameters.items():
        if name == "session":
            continue

        type_hint = hints.get(name, str)
        desc = descriptions.get(name, "")

        if param.default is inspect.Parameter.empty:
            field_definitions[name] = (
                type_hint,
                Field(..., description=desc) if desc else ...,
            )
        else:
            field_definitions[name] = (
                type_hint,
                Field(default=param.default, description=desc) if desc else param.default,
            )

    model = create_model(f"{fn.__name__}Input", **field_definitions)
    return model.model_json_schema()


def get_tool_list() -> list[dict[str, Any]]:
    """Return the MCP tool list with the style guide pointer appended to write tools."""
    result = []
    for name, defn in TOOL_REGISTRY.items():
        desc = defn.description
        pointer = get_tool_style_pointer(name)
        if pointer:
            desc = desc + pointer
        entry: dict[str, Any] = {
            "name": name,
            "description": desc,
            "inputSchema": defn.input_schema,
        }
        if defn.output_schema:
            entry["outputSchema"] = defn.output_schema
        if defn.annotations:
            entry["annotations"] = defn.annotations
        result.append(entry)
    return result


async def dispatch_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a tool call by name using the registry.

    Service failures arrive here as typed exceptions and leave as a payload carrying the
    kind, the field, and a hint about what would have been right. Tools therefore contain
    no error branches: they describe the happy path and let this translate the rest."""
    defn = TOOL_REGISTRY.get(name)
    if defn is None:
        return {
            "success": False, "code": "not_found",
            "error": f"unknown tool {name!r}",
            "hint": f"available: {', '.join(sorted(TOOL_REGISTRY))}",
        }

    kwargs = {k: v for k, v in arguments.items() if k != "session"}
    try:
        return await defn.handler(**kwargs)
    except KeelError as exc:
        return exc.as_dict()
    except TypeError as exc:
        # A missing or misspelled argument. The schema says what is allowed, but the
        # caller has evidently not used it, so repeat it here rather than echo Python.
        params = list(defn.input_schema.get("properties", {}))
        required = defn.input_schema.get("required", [])
        return {
            "success": False, "code": "invalid", "error": str(exc),
            "hint": f"{name} takes {', '.join(params) or 'no arguments'}"
                    + (f"; required: {', '.join(required)}" if required else ""),
        }
