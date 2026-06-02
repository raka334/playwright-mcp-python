from __future__ import annotations

import pytest
from urllib.parse import quote

from playwright_mcp_python.config import LaunchConfig
from playwright_mcp_python.session import BrowserSession
from playwright_mcp_python.tools import dispatch_tool


def text_content(result) -> str:
    content = result.content[0]
    assert content.type == "text"
    return content.text


@pytest.mark.asyncio
async def test_browser_navigate() -> None:
    config = LaunchConfig(browser="chrome", headless=True)
    session = BrowserSession(config)
    try:
        result = await dispatch_tool(
            "browser_navigate",
            {"url": "data:text/html,<title>Hello</title><h1>Hello, world!</h1>"},
            session,
            config,
        )
        assert result.isError is False
        assert "await page.goto" in text_content(result)
        assert "### Snapshot" in text_content(result)
    finally:
        await session.shutdown()


@pytest.mark.asyncio
async def test_browser_evaluate_after_navigate() -> None:
    config = LaunchConfig(browser="chrome", headless=True)
    session = BrowserSession(config)
    try:
        await dispatch_tool(
            "browser_navigate",
            {"url": "data:text/html,<title>Hello</title><h1>Hello, world!</h1>"},
            session,
            config,
        )
        result = await dispatch_tool(
            "browser_evaluate",
            {"function": "() => document.title"},
            session,
            config,
        )
        assert result.isError is False
        assert '"Hello"' in text_content(result)
    finally:
        await session.shutdown()


@pytest.mark.asyncio
async def test_snapshot_refs_click_type_wait_console_network() -> None:
    html = quote(
        """
        <title>Title</title>
        <button>Submit</button>
        <input aria-label="Name" />
        <div id="status">Ready</div>
        <script>
          console.log('hello-console');
          fetch('data:text/plain,ok');
          const button = document.querySelector('button');
          button.addEventListener('click', () => {
            button.focus();
            document.querySelector('#status').textContent = 'Clicked';
          });
        </script>
        """
    )
    config = LaunchConfig(browser="chrome", headless=True)
    session = BrowserSession(config)
    try:
        await dispatch_tool("browser_navigate", {"url": f"data:text/html,{html}"}, session, config)

        snapshot = await dispatch_tool("browser_snapshot", {}, session, config)
        assert snapshot.isError is False
        snapshot_text = text_content(snapshot)
        assert 'button "Submit"' in snapshot_text
        assert "[ref=e" in snapshot_text

        button_ref = next(ref for ref, selector in session.refs.items() if selector == "body > button")
        input_ref = next(ref for ref, selector in session.refs.items() if selector == "body > input")

        clicked = await dispatch_tool("browser_click", {"element": "Submit button", "target": button_ref}, session, config)
        assert clicked.isError is False
        assert "Clicked" in text_content(clicked)

        typed = await dispatch_tool("browser_type", {"element": "Name", "target": input_ref, "text": "Alice"}, session, config)
        assert typed.isError is False
        assert "Alice" in text_content(typed)

        waited = await dispatch_tool("browser_wait_for", {"text": "Clicked"}, session, config)
        assert waited.isError is False

        console = await dispatch_tool("browser_console_messages", {"level": "info"}, session, config)
        assert console.isError is False
        assert "hello-console" in text_content(console)

        network = await dispatch_tool("browser_network_requests", {"static": False}, session, config)
        assert network.isError is False
        assert "data:text/html" in text_content(network)
    finally:
        await session.shutdown()


@pytest.mark.asyncio
async def test_remaining_action_tools() -> None:
    html = quote(
        """
        <title>Tools</title>
        <button onclick="window.clicked = true">Button</button>
        <select aria-label="Choice"><option>One</option><option>Two</option></select>
        <input aria-label="Check" type="checkbox" />
        <input aria-label="Upload" type="file" />
        <ul id="list"><li>Alpha</li><li>Beta</li></ul>
        <div id="drop" ondrop="window.dropped = true">Drop</div>
        <div id="drag">Drag</div>
        <script>window.clicked = false; window.dropped = false;</script>
        """
    )
    config = LaunchConfig(browser="chrome", headless=True)
    session = BrowserSession(config)
    try:
        await dispatch_tool("browser_navigate", {"url": f"data:text/html,{html}"}, session, config)

        hover = await dispatch_tool("browser_hover", {"target": "button"}, session, config)
        assert hover.isError is False

        key = await dispatch_tool("browser_press_key", {"key": "Tab"}, session, config)
        assert key.isError is False

        select = await dispatch_tool("browser_select_option", {"target": "select", "values": ["Two"]}, session, config)
        assert select.isError is False

        fill = await dispatch_tool(
            "browser_fill_form",
            {"fields": [{"target": "input[type=checkbox]", "name": "Check", "type": "checkbox", "value": "true"}]},
            session,
            config,
        )
        assert fill.isError is False

        verify_element = await dispatch_tool("browser_verify_element_visible", {"role": "button", "accessibleName": "Button"}, session, config)
        assert verify_element.isError is False

        verify_text = await dispatch_tool("browser_verify_text_visible", {"text": "Alpha"}, session, config)
        assert verify_text.isError is False

        verify_list = await dispatch_tool("browser_verify_list_visible", {"element": "items", "target": "#list", "items": ["Alpha", "Beta"]}, session, config)
        assert verify_list.isError is False

        verify_value = await dispatch_tool("browser_verify_value", {"type": "checkbox", "element": "Check", "target": "input[type=checkbox]", "value": "true"}, session, config)
        assert verify_value.isError is False

        locator = await dispatch_tool("browser_generate_locator", {"target": "button"}, session, config)
        assert locator.isError is False
        assert "page.locator" in text_content(locator)

        resize = await dispatch_tool("browser_resize", {"width": 800, "height": 600}, session, config)
        assert resize.isError is False

        back = await dispatch_tool("browser_navigate_back", {}, session, config)
        assert back.isError in {False, True}
    finally:
        await session.shutdown()


@pytest.mark.asyncio
async def test_drag_drop_dialog_upload_run_code_pdf_and_mouse_tools(tmp_path) -> None:
    html = quote(
        """
        <title>More Tools</title>
        <style>#drag,#drop{width:80px;height:40px;margin:8px;border:1px solid black}</style>
        <div id="drag" draggable="true">Drag</div>
        <div id="drop">Drop</div>
        <input id="file" type="file" />
        <script>
          drop.addEventListener('dragover', event => event.preventDefault());
          drop.addEventListener('drop', event => { event.preventDefault(); window.dropped = true; });
          window.dropped = false;
        </script>
        """
    )
    config = LaunchConfig(browser="chrome", headless=True, caps={"testing", "pdf", "vision"})
    session = BrowserSession(config)
    try:
        await dispatch_tool("browser_navigate", {"url": f"data:text/html,{html}"}, session, config)

        drag = await dispatch_tool("browser_drag", {"startTarget": "#drag", "endTarget": "#drop"}, session, config)
        assert drag.isError is False

        drop = await dispatch_tool("browser_drop", {"target": "#drop", "data": {"text/plain": "hello"}}, session, config)
        assert drop.isError is False

        page = await session.page()
        async with page.expect_file_chooser():
            await page.locator("#file").click()
        upload_file = tmp_path / "upload.txt"
        upload_file.write_text("hello")
        upload = await dispatch_tool("browser_file_upload", {"paths": [str(upload_file)]}, session, config)
        assert upload.isError is False

        await page.evaluate("setTimeout(() => alert('hello'), 0)")
        await page.wait_for_event("dialog")
        dialog = await dispatch_tool("browser_handle_dialog", {"accept": True}, session, config)
        assert dialog.isError is False

        unsafe = await dispatch_tool("browser_run_code_unsafe", {"code": "() => document.title"}, session, config)
        assert unsafe.isError is False
        assert "More Tools" in text_content(unsafe)

        pdf_path = tmp_path / "page.pdf"
        pdf = await dispatch_tool("browser_pdf_save", {"filename": str(pdf_path)}, session, config)
        assert pdf.isError is False
        assert pdf_path.exists()

        for name, args in [
            ("browser_mouse_move_xy", {"x": 10, "y": 10}),
            ("browser_mouse_click_xy", {"x": 10, "y": 10}),
            ("browser_mouse_drag_xy", {"startX": 10, "startY": 10, "endX": 20, "endY": 20}),
            ("browser_mouse_down", {}),
            ("browser_mouse_up", {}),
            ("browser_mouse_wheel", {"deltaX": 0, "deltaY": 10}),
        ]:
            result = await dispatch_tool(name, args, session, config)
            assert result.isError is False, text_content(result)
    finally:
        await session.shutdown()
