from __future__ import annotations

import os
import re
import shutil
import sys
from urllib.parse import quote

import pytest

sys.path.insert(0, "src")
sys.path.insert(0, os.path.dirname(__file__))

from mcp_test_client import MCPTestClient


pytestmark = pytest.mark.upstream_live


def _has_npx() -> bool:
    return shutil.which("npx") is not None or shutil.which("npx.cmd") is not None


async def _start(command: str, *args):
    bridge = MCPTestClient(call_timeout=90)
    await bridge.start(command, *args)
    return bridge


def _text(result: dict) -> str:
    return result["content"][0]["text"]


def _semantic_tokens(text: str) -> set[str]:
    tokens = set()
    for token in ["button", "textbox", "list", "listitem", "Submit", "Name", "Alpha", "Beta", "ref=e1", "ref=e2", "ref=e3"]:
        if token in text:
            tokens.add(token)
    return tokens


@pytest.mark.skipif(not _has_npx(), reason="npx required for upstream comparison")
@pytest.mark.asyncio
async def test_live_tools_list_matches_upstream() -> None:
    upstream = await _start("npx", "@playwright/mcp@0.0.75", ["--caps", "testing"])
    previous_pythonpath = os.environ.get("PYTHONPATH")
    os.environ["PYTHONPATH"] = "src" if not previous_pythonpath else f"src:{previous_pythonpath}"
    python = await _start("python", "-m", "playwright_mcp_python.cli", ["--browser", "chrome"])
    try:
        upstream_tools = await upstream.list_tools()
        python_tools = await python.list_tools()
        assert [tool["name"] for tool in python_tools] == [tool["name"] for tool in upstream_tools]
        assert [tool["inputSchema"] for tool in python_tools] == [tool["inputSchema"] for tool in upstream_tools]
    finally:
        await upstream.close()
        await python.close()
        if previous_pythonpath is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = previous_pythonpath


@pytest.mark.skipif(not _has_npx(), reason="npx required for upstream comparison")
@pytest.mark.asyncio
async def test_live_navigate_outputs_are_tool_successes() -> None:
    html = quote("<title>Live</title><button>Submit</button>")
    url = f"data:text/html,{html}"
    upstream = await _start("npx", "@playwright/mcp@0.0.75", ["--browser", "chrome"])
    previous_pythonpath = os.environ.get("PYTHONPATH")
    os.environ["PYTHONPATH"] = "src" if not previous_pythonpath else f"src:{previous_pythonpath}"
    python = await _start("python", "-m", "playwright_mcp_python.cli", ["--browser", "chrome"])
    try:
        upstream_result = await upstream.call_tool("browser_navigate", {"url": url})
        python_result = await python.call_tool("browser_navigate", {"url": url})
        assert not upstream_result.get("isError")
        assert not python_result.get("isError")
        upstream_text = upstream_result["content"][0]["text"]
        python_text = python_result["content"][0]["text"]
        assert "### Ran Playwright code" in upstream_text
        assert "### Ran Playwright code" in python_text
        assert "page.goto" in upstream_text
        assert "page.goto" in python_text
        assert "Snapshot" in upstream_text
        assert "Snapshot" in python_text
    finally:
        await upstream.close()
        await python.close()
        if previous_pythonpath is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = previous_pythonpath


@pytest.mark.skipif(not _has_npx(), reason="npx required for upstream comparison")
@pytest.mark.asyncio
async def test_live_core_behavior_matches_upstream_semantics() -> None:
    html = quote(
        '<title>Parity</title><button>Submit</button><input aria-label="Name">'
        '<ul><li>Alpha</li><li>Beta</li></ul>'
        '<script>document.querySelector("button").onclick=()=>document.body.dataset.clicked="yes"</script>'
    )
    url = f"data:text/html,{html}"
    upstream = await _start("npx", "@playwright/mcp@0.0.75", ["--browser", "chrome"])
    previous_pythonpath = os.environ.get("PYTHONPATH")
    os.environ["PYTHONPATH"] = "src" if not previous_pythonpath else f"src:{previous_pythonpath}"
    python = await _start("python", "-m", "playwright_mcp_python.cli", ["--browser", "chrome"])
    try:
        for bridge in [upstream, python]:
            result = await bridge.call_tool("browser_navigate", {"url": url})
            assert not result.get("isError")

        upstream_snapshot = await upstream.call_tool("browser_snapshot", {})
        python_snapshot = await python.call_tool("browser_snapshot", {})
        assert not upstream_snapshot.get("isError")
        assert not python_snapshot.get("isError")

        upstream_tokens = _semantic_tokens(_text(upstream_snapshot))
        python_tokens = _semantic_tokens(_text(python_snapshot))
        assert {"button", "textbox", "Submit", "Name", "Alpha", "Beta", "ref=e1", "ref=e2", "ref=e3"} <= upstream_tokens
        assert {"button", "textbox", "Submit", "Name", "Alpha", "Beta", "ref=e1", "ref=e2", "ref=e3"} <= python_tokens

        for tool_name, args in [
            ("browser_click", {"element": "Submit button", "target": "e2"}),
            ("browser_type", {"element": "Name input", "target": "e3", "text": "Alice"}),
            ("browser_wait_for", {"text": "Alpha"}),
        ]:
            upstream_result = await upstream.call_tool(tool_name, args)
            python_result = await python.call_tool(tool_name, args)
            assert not upstream_result.get("isError"), _text(upstream_result)
            assert not python_result.get("isError"), _text(python_result)
            upstream_text = _text(upstream_result)
            python_text = _text(python_result)
            assert "### Ran Playwright code" in upstream_text
            assert "### Ran Playwright code" in python_text
            assert "page." in upstream_text
            assert "page." in python_text
    finally:
        await upstream.close()
        await python.close()
        if previous_pythonpath is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = previous_pythonpath
