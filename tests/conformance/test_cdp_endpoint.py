from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import quote

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp_test_client import MCPTestClient


CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


@pytest.mark.skipif(not CHROME.exists(), reason="Google Chrome is required for local CDP parity test")
@pytest.mark.asyncio
async def test_python_mcp_works_over_local_cdp_endpoint() -> None:
    user_data_dir = tempfile.mkdtemp(prefix="playwright-mcp-python-cdp-")
    proc = subprocess.Popen(
        [
            str(CHROME),
            "--remote-debugging-port=9333",
            "--no-first-run",
            "--no-default-browser-check",
            f"--user-data-dir={user_data_dir}",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    previous_pythonpath = os.environ.get("PYTHONPATH")
    os.environ["PYTHONPATH"] = "src" if not previous_pythonpath else f"src:{previous_pythonpath}"
    bridge = MCPTestClient(call_timeout=90)
    try:
        time.sleep(3)
        await bridge.start(
            "python",
            "-m",
            "playwright_mcp_python.cli",
            ["--cdp-endpoint", "http://localhost:9333", "--image-responses", "allow"],
        )
        tools = await bridge.list_tools()
        assert len(tools) == 28

        html = quote("<title>CDP</title><button onclick=\"document.body.dataset.clicked='yes'\">Submit</button>")
        nav = await bridge.call_tool("browser_navigate", {"url": f"data:text/html,{html}"})
        assert not nav.get("isError"), nav

        snapshot = await bridge.call_tool("browser_snapshot", {})
        assert not snapshot.get("isError"), snapshot
        snapshot_text = snapshot["content"][0]["text"]
        assert "Submit" in snapshot_text
        assert "ref=e2" in snapshot_text

        click = await bridge.call_tool("browser_click", {"element": "Submit button", "target": "e2"})
        assert not click.get("isError"), click

        value = await bridge.call_tool("browser_evaluate", {"function": "() => document.body.dataset.clicked"})
        assert not value.get("isError"), value
        assert "yes" in value["content"][0]["text"]

        screenshot = await bridge.call_tool("browser_take_screenshot", {"type": "png"})
        assert not screenshot.get("isError"), screenshot
        assert any(item.get("type") == "image" for item in screenshot["content"])
    finally:
        await bridge.close()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(user_data_dir, ignore_errors=True)
        if previous_pythonpath is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = previous_pythonpath
