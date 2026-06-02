"""Low-level MCP server wiring."""

from __future__ import annotations

from mcp.server import Server
from mcp.server.stdio import stdio_server

from playwright_mcp_python.config import LaunchConfig
from playwright_mcp_python.registry import list_tools
from playwright_mcp_python.session import BrowserSession
from playwright_mcp_python.tools import dispatch_tool


def create_server(config: LaunchConfig) -> Server:
    server = Server("playwright-mcp-python", version="0.1.0")
    session = BrowserSession(config)

    @server.list_tools()
    async def handle_list_tools():
        return list_tools(config.caps)

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict):
        return await dispatch_tool(name, arguments, session, config)

    server.browser_session = session  # type: ignore[attr-defined]
    return server


async def run_stdio(config: LaunchConfig) -> None:
    server = create_server(config)
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    finally:
        await server.browser_session.shutdown()  # type: ignore[attr-defined]
