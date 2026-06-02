from __future__ import annotations

import json
from importlib.resources import files

from playwright_mcp_python.registry import IMPLEMENTED_TOOLS, list_tools


def tool_names(caps: set[str] | None = None) -> set[str]:
    return {tool.name for tool in list_tools(caps)}


def test_snapshot_tool_list() -> None:
    fixture_path = files("playwright_mcp_python.schemas").joinpath("microsoft-tools-list.json")
    fixture = json.loads(fixture_path.read_text())
    assert tool_names({"testing"}) == set(fixture["defaultTools"])


def test_registry_matches_schema_fixture_tool_names() -> None:
    fixture_path = files("playwright_mcp_python.schemas").joinpath("microsoft-tools-list.json")
    fixture = json.loads(fixture_path.read_text())
    assert tool_names({"testing"}) == set(fixture["defaultTools"])
    assert "browser_pdf_save" in fixture["pdfTools"]
    assert "browser_mouse_move_xy" in fixture["visionTools"]


def test_registry_matches_schema_fixture_input_schemas() -> None:
    fixture_path = files("playwright_mcp_python.schemas").joinpath("microsoft-tools-list.json")
    fixture = json.loads(fixture_path.read_text())
    expected = {tool["name"]: tool["inputSchema"] for tool in fixture["tools"]}
    actual = {tool.name: tool.inputSchema for tool in list_tools({"testing"})}
    assert actual == expected


def test_capabilities_pdf() -> None:
    assert "browser_pdf_save" in tool_names({"pdf"})


def test_capabilities_vision() -> None:
    names = tool_names({"vision"})
    assert "browser_mouse_move_xy" in names
    assert "browser_mouse_click_xy" in names
    assert "browser_mouse_drag_xy" in names


def test_all_exposed_tools_have_implementation_path() -> None:
    names = tool_names({"testing", "pdf", "vision"})
    assert names <= IMPLEMENTED_TOOLS
