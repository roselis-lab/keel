"""Keel MCP server (mcp SDK 2.x).

Two transports via one code path:
  - stdio (default, no args) — for local Claude Code subprocess use
  - Streamable HTTP (--http) — for Docker / any remote MCP client
"""
import asyncio
import json
import sys
from pathlib import Path
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import Server

from keel.config import settings
from keel.lib.style_guide import SERVER_INSTRUCTIONS
from keel.mcp.registry import get_tool_list
from keel.mcp.tools import dispatch_tool


@asynccontextmanager
async def server_lifespan(server: Server) -> AsyncIterator[dict[str, Any]]:
    """Load the catalog from `catalog/*.yaml` into memory on startup — no setup step."""
    print("Keel MCP server starting...", file=sys.stderr)
    from keel.store import get_store
    get_store()
    try:
        yield {}
    finally:
        print("Keel MCP server shutting down...", file=sys.stderr)


async def handle_list_tools(ctx, params) -> types.ListToolsResult:
    """List available MCP tools (style guide pointers appended to write tools)."""
    tools = [types.Tool.model_validate(t) for t in get_tool_list()]
    return types.ListToolsResult(tools=tools)


async def handle_call_tool(ctx, params) -> types.CallToolResult:
    """Dispatch a tool call, serializing the result as JSON text."""
    try:
        result = await dispatch_tool(params.name, params.arguments or {})
        text = json.dumps(result, indent=2, default=str)
        return types.CallToolResult(content=[types.TextContent(type="text", text=text)])
    except Exception as e:
        text = json.dumps({"error": str(e), "success": False}, indent=2)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=text)],
            is_error=True,
        )


server = Server(
    settings.mcp_server_name,
    version=settings.mcp_server_version,
    # Said once here rather than repeated on every write tool, where five copies of the
    # same paragraph were 11% of the tool list and were paid for in every conversation.
    instructions=SERVER_INSTRUCTIONS,
    lifespan=server_lifespan,
    on_list_tools=handle_list_tools,
    on_call_tool=handle_call_tool,
)


async def run_stdio() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def run_http() -> None:
    """Run Streamable HTTP transport on settings.mcp_http_port (stateless)."""
    import uvicorn
    from contextlib import asynccontextmanager as _asynccontextmanager
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.applications import Starlette
    from starlette.routing import Mount

    session_manager = StreamableHTTPSessionManager(app=server, stateless=True)

    async def handle_streamable_http(scope, receive, send):
        await session_manager.handle_request(scope, receive, send)

    @_asynccontextmanager
    async def app_lifespan(_app):
        async with session_manager.run():
            print(
                f"Keel MCP HTTP listening on "
                f"http://{settings.mcp_http_host}:{settings.mcp_http_port}/mcp",
                file=sys.stderr,
            )
            yield

    app = Starlette(
        routes=[Mount("/mcp", app=handle_streamable_http)],
        lifespan=app_lifespan,
    )
    uvicorn.run(app, host=settings.mcp_http_host, port=settings.mcp_http_port, log_level="info")


def main():
    """Entry point. `validate` checks the catalog YAML, `schema` regenerates the JSON
    Schema files, `style-guide export|import` moves the whole guide in bulk, `--http`
    selects Streamable HTTP, and no args runs the stdio MCP server."""
    args = sys.argv[1:]
    if args and args[0] == "schema":
        from keel.schema_export import DEFAULT_SCHEMA_DIR, schemas_are_fresh, write_schemas

        if "--check" in args:
            if schemas_are_fresh():
                print("Schema files are fresh.", file=sys.stderr)
            else:
                print("Schema files are stale — run `keel schema`.", file=sys.stderr)
                raise SystemExit(1)
        else:
            write_schemas()
            print(f"Wrote JSON Schema to {DEFAULT_SCHEMA_DIR}", file=sys.stderr)
        return
    if args and args[0] == "style-guide":
        # Bulk YAML in and out is a migration, not authoring, and it used to be two MCP
        # tools. A model authoring a card never needs to move the whole guide at once,
        # and `import --replace` clears every entity it touches — not something to leave
        # sitting in a tool list where a host may auto-approve it.
        import asyncio as _asyncio

        from keel.services import style_guide_service as sg

        sub = args[1] if len(args) > 1 else ""
        if sub == "export":
            print(_asyncio.run(sg.export_yaml()))
            return
        if sub == "import":
            path = args[2] if len(args) > 2 else ""
            if not path:
                print("usage: keel style-guide import <file.yaml> [--replace]", file=sys.stderr)
                raise SystemExit(2)
            mode = "replace" if "--replace" in args else "merge"
            text = Path(path).read_text(encoding="utf-8")
            result = _asyncio.run(sg.import_yaml(text, mode=mode, updated_by="cli:import"))
            print(f"Imported ({mode}): {result}", file=sys.stderr)
            return
        print("usage: keel style-guide export | import <file.yaml> [--replace]", file=sys.stderr)
        raise SystemExit(2)

    if args and args[0] == "validate":
        from keel.catalog import catalog_warnings, validate_catalog

        strict = "--strict" in args
        errs = validate_catalog()
        warns = catalog_warnings()

        # Advisory tier: printed to stderr, but never fails CI on its own (only --strict does).
        if warns:
            print(f"Warnings ({len(warns)}):", file=sys.stderr)
            for w in warns:
                print(f"  ! {w}", file=sys.stderr)

        if errs:
            print(f"Catalog invalid ({len(errs)} problem(s)):", file=sys.stderr)
            for e in errs:
                print(f"  - {e}", file=sys.stderr)
            raise SystemExit(1)

        if warns and strict:
            print(f"--strict: {len(warns)} warning(s) treated as errors.", file=sys.stderr)
            raise SystemExit(1)

        print("Catalog is valid.", file=sys.stderr)
    elif "--http" in args:
        run_http()
    else:
        asyncio.run(run_stdio())


if __name__ == "__main__":
    main()
