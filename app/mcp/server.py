"""Keel MCP server (mcp SDK 2.x).

Two transports via one code path:
  - stdio (default, no args) — for local Claude Code subprocess use
  - Streamable HTTP (--http) — for Docker / any remote MCP client
"""
import asyncio
import json
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import Server
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.mcp.registry import get_tool_list
from app.mcp.tools import dispatch_tool


@asynccontextmanager
async def server_lifespan(server: Server) -> AsyncIterator[dict[str, Any]]:
    """Manage server lifespan with a database connection."""
    print("Keel MCP server starting...", file=sys.stderr)

    engine = create_async_engine(settings.database_url, echo=settings.debug)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Keep style guide skeletons in sync with the current model fields.
    async with async_session_maker() as session:
        from app.services.style_guide_service import sync_skeletons
        await sync_skeletons(session)

    try:
        yield {"engine": engine, "session_maker": async_session_maker}
    finally:
        print("Keel MCP server shutting down...", file=sys.stderr)
        await engine.dispose()


async def handle_list_tools(ctx, params) -> types.ListToolsResult:
    """List available MCP tools (style guide pointers appended to write tools)."""
    tools = [types.Tool.model_validate(t) for t in get_tool_list()]
    return types.ListToolsResult(tools=tools)


async def handle_call_tool(ctx, params) -> types.CallToolResult:
    """Dispatch a tool call, serializing the result as JSON text."""
    session_maker = ctx.lifespan_context["session_maker"]
    async with session_maker() as session:
        try:
            result = await dispatch_tool(params.name, params.arguments or {}, session)
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


async def _run_catalog(action: str) -> None:
    """One-shot catalog commands (`seed` / `export`) against the configured DB."""
    from app.catalog import export_catalog, load_catalog

    engine = create_async_engine(settings.database_url, echo=settings.debug)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with maker() as session:
            if action == "seed":
                result = await load_catalog(session)
                print(f"Seeded catalog into the database: {result}", file=sys.stderr)
            else:
                result = await export_catalog(session)
                print(f"Exported database to catalog/: {result}", file=sys.stderr)
    finally:
        await engine.dispose()


def main():
    """Entry point. `seed` / `export` run catalog commands; `--http` selects
    Streamable HTTP; no args runs the stdio MCP server."""
    args = sys.argv[1:]
    if args and args[0] in ("seed", "export"):
        asyncio.run(_run_catalog(args[0]))
    elif "--http" in args:
        run_http()
    else:
        asyncio.run(run_stdio())


if __name__ == "__main__":
    main()
