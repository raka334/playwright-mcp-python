"""Fixture-backed tool registry for Microsoft Playwright MCP compatibility."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any

from mcp import types


IMPLEMENTED_TOOLS = {
    "browser_click",
    "browser_close",
    "browser_console_messages",
    "browser_drag",
    "browser_drop",
    "browser_evaluate",
    "browser_file_upload",
    "browser_fill_form",
    "browser_generate_locator",
    "browser_handle_dialog",
    "browser_hover",
    "browser_mouse_click_xy",
    "browser_mouse_down",
    "browser_mouse_drag_xy",
    "browser_mouse_move_xy",
    "browser_mouse_up",
    "browser_mouse_wheel",
    "browser_navigate",
    "browser_navigate_back",
    "browser_network_request",
    "browser_network_requests",
    "browser_pdf_save",
    "browser_press_key",
    "browser_resize",
    "browser_run_code_unsafe",
    "browser_select_option",
    "browser_snapshot",
    "browser_tabs",
    "browser_take_screenshot",
    "browser_type",
    "browser_verify_element_visible",
    "browser_verify_list_visible",
    "browser_verify_text_visible",
    "browser_verify_value",
    "browser_wait_for",
}


@lru_cache(maxsize=1)
def schema_fixture() -> dict[str, Any]:
    path = files("playwright_mcp_python.schemas").joinpath("microsoft-tools-list.json")
    return json.loads(path.read_text())


def _tool_map(tools: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {tool["name"]: tool for tool in tools}


def raw_tools(caps: set[str] | None = None) -> list[dict[str, Any]]:
    fixture = schema_fixture()
    caps = caps or {"testing"}
    tools = _tool_map(fixture["tools"])

    capability_tools = fixture.get("capabilityTools", {})
    for cap in caps:
        for tool in capability_tools.get(cap, []):
            tools[tool["name"]] = tool

    return list(tools.values())


def tool_schemas(caps: set[str] | None = None) -> dict[str, dict]:
    return {tool["name"]: tool["inputSchema"] for tool in raw_tools(caps)}


def list_tools(caps: set[str] | None = None) -> list[types.Tool]:
    return [types.Tool.model_validate(tool) for tool in raw_tools(caps)]
