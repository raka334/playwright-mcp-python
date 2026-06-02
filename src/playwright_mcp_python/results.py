"""Helpers for MCP tool result envelopes."""

from __future__ import annotations

from mcp import types


def text_result(text: str) -> types.CallToolResult:
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=text)],
        isError=False,
    )


def image_result(data: str, mime_type: str = "image/png", text: str | None = None) -> types.CallToolResult:
    content = []
    if text:
        content.append(types.TextContent(type="text", text=text))
    content.append(types.ImageContent(type="image", data=data, mimeType=mime_type))
    return types.CallToolResult(content=content, isError=False)


def tool_error(message: str) -> types.CallToolResult:
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=message)],
        isError=True,
    )
