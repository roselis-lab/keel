"""Extensions: packages that add to Keel without Keel knowing them.

An extension is a Python package that declares an entry point in the group
`keel.extensions`. The entry point names an object or a module with a `name` and any of
these, each optional:

- `check(report, section) -> list[str]`: what is wrong with its own section of a report.
  The errors are refused on save like Keel's own, each starting `extensions.<name>: `.
- `draw_diagram(report, section, threats, shape) -> (html, note) | None`: the diagram on
  the report page. The first extension that returns something draws it; when none does,
  Keel draws its own. It may raise `keel.diagram.Unavailable` to say why it cannot.
- `routers`: FastAPI routers, mounted on the app before the page catch-all.
- `register_mcp(mcp)`: adds MCP tools after Keel's own. `mcp` is `keel.mcp.registry`, so
  a tool is added with `mcp.register_tool(...)` the same way Keel adds its own.
- `commands`: `{name: run(args) -> exit code}`, run as `keel <name> ...`. A name Keel
  already uses stays Keel's.

A report keeps an extension's data in `extensions[<name>]`. Keel stores that section and
never reads it, so a report written with an extension opens, checks and saves on a Keel
without it.

An extension that fails to load, or whose hook raises, is logged and left out: Keel keeps
working without it.
"""
from __future__ import annotations

import logging
from functools import cache
from importlib.metadata import entry_points
from typing import Any, Callable

logger = logging.getLogger("keel.extensions")

GROUP = "keel.extensions"

# Keel's own subcommands (keel/mcp/server.py:main). An extension cannot take one of them.
KEEL_COMMANDS = frozenset({
    "up", "down", "site", "recheck", "export", "publish", "schema", "style-guide",
    "validate", "reports",
})


@cache
def installed() -> tuple[Any, ...]:
    """Every extension that loads, in entry point order. Read once per process, so a
    broken one is logged once."""
    out = []
    for ep in entry_points(group=GROUP):
        try:
            ext = ep.load()
        except Exception:
            logger.exception("extension %r did not load; Keel runs without it", ep.name)
            continue
        name = getattr(ext, "name", None)
        if not isinstance(name, str) or not name:
            logger.warning("extension %r has no name; Keel runs without it", ep.name)
            continue
        out.append(ext)
    return tuple(out)


def _section(report: Any, name: str) -> dict[str, Any]:
    return (getattr(report, "extensions", None) or {}).get(name) or {}


def check_errors(report: Any) -> list[str]:
    """Each installed extension's errors for its own section. A report with no section
    for an extension is not checked by it, and a section whose extension is not installed
    is not checked at all."""
    errors: list[str] = []
    present = getattr(report, "extensions", None) or {}
    for ext in installed():
        check = getattr(ext, "check", None)
        if check is None or ext.name not in present:
            continue
        try:
            found = check(report, present[ext.name] or {})
        except Exception:
            logger.exception("extension %r: check failed; its section was not checked", ext.name)
            continue
        errors.extend(f"extensions.{ext.name}: {e}" for e in found or [])
    return errors


def draw_diagram(report: Any, threats: dict[str, Any], shape: str) -> tuple[str, str | None] | None:
    """The first extension's diagram, or None when no extension draws one.

    `keel.diagram.Unavailable` passes through to the caller, which says it to the reader.
    Any other failure is logged and the next extension, or Keel's own diagram, is used."""
    from keel.diagram import Unavailable

    for ext in installed():
        draw = getattr(ext, "draw_diagram", None)
        if draw is None:
            continue
        try:
            drawn = draw(report, _section(report, ext.name), threats, shape)
        except Unavailable:
            raise
        except Exception:
            logger.exception("extension %r: draw_diagram failed; skipped", ext.name)
            continue
        if drawn is not None:
            html, note = drawn
            return html, note
    return None


def include_routers(app: Any) -> None:
    """Mount every extension's routers on the app. Called before the page catch-all,
    which would otherwise answer their paths with the app's HTML."""
    for ext in installed():
        for router in getattr(ext, "routers", None) or []:
            app.include_router(router)


def register_mcp(mcp: Any) -> None:
    """Let every extension add its MCP tools, after Keel's own are registered."""
    for ext in installed():
        register = getattr(ext, "register_mcp", None)
        if register is None:
            continue
        try:
            register(mcp)
        except Exception:
            logger.exception("extension %r: register_mcp failed; its tools are not added", ext.name)


def commands() -> dict[str, Callable[[list[str]], int]]:
    """`keel <name>` for every extension command. A name Keel uses, or one an earlier
    extension took, is refused with a warning."""
    out: dict[str, Callable[[list[str]], int]] = {}
    for ext in installed():
        for name, run in (getattr(ext, "commands", None) or {}).items():
            if name in KEEL_COMMANDS or name.startswith("-"):
                logger.warning("extension %r: `keel %s` is Keel's own; refused", ext.name, name)
            elif name in out:
                logger.warning("extension %r: `keel %s` is taken by another extension; refused",
                               ext.name, name)
            else:
                out[name] = run
    return out
