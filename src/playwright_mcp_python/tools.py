"""Core Playwright MCP tool implementations."""

from __future__ import annotations

import asyncio
import base64
import json
import re
import time
from pathlib import Path
from typing import Any

from mcp import types

from playwright_mcp_python.config import LaunchConfig
from playwright_mcp_python.registry import IMPLEMENTED_TOOLS
from playwright_mcp_python.results import image_result, text_result, tool_error
from playwright_mcp_python.session import BrowserSession


SNAPSHOT_SCRIPT = r"""
() => {
  const selectorFor = (el) => {
    if (el.id)
      return '#' + CSS.escape(el.id);
    const parts = [];
    let node = el;
    while (node && node.nodeType === Node.ELEMENT_NODE && node !== document.body) {
      let part = node.localName.toLowerCase();
      const parent = node.parentElement;
      if (parent) {
        const same = Array.from(parent.children).filter(child => child.localName === node.localName);
        if (same.length > 1)
          part += `:nth-of-type(${same.indexOf(node) + 1})`;
      }
      parts.unshift(part);
      node = parent;
    }
    return parts.length ? 'body > ' + parts.join(' > ') : 'body';
  };

  const visible = (el) => {
    const style = getComputedStyle(el);
    const box = el.getBoundingClientRect();
    return style.visibility !== 'hidden' && style.display !== 'none' && box.width >= 0 && box.height >= 0;
  };

  const roleFor = (el) => {
    const explicit = el.getAttribute('role');
    if (explicit)
      return explicit;
    const tag = el.localName;
    if (tag === 'button') return 'button';
    if (tag === 'a' && el.href) return 'link';
    if (tag === 'input') {
      const type = (el.getAttribute('type') || 'text').toLowerCase();
      if (type === 'checkbox') return 'checkbox';
      if (type === 'radio') return 'radio';
      if (type === 'range') return 'slider';
      return 'textbox';
    }
    if (tag === 'textarea') return 'textbox';
    if (tag === 'select') return 'combobox';
    if (/^h[1-6]$/.test(tag)) return 'heading';
    if (tag === 'li') return 'listitem';
    if (tag === 'ul' || tag === 'ol') return 'list';
    return 'generic';
  };

  const nameFor = (el) => {
    const labelledBy = el.getAttribute('aria-labelledby');
    if (labelledBy) {
      const label = document.getElementById(labelledBy);
      if (label?.innerText?.trim()) return label.innerText.trim();
    }
    const aria = el.getAttribute('aria-label');
    if (aria) return aria;
    if (el.labels?.length) return Array.from(el.labels).map(label => label.innerText.trim()).join(' ').trim();
    if (el.alt) return el.alt;
    if (el.placeholder) return el.placeholder;
    if (el.innerText?.trim()) return el.innerText.trim().replace(/\s+/g, ' ');
    if (el.value && ['INPUT', 'TEXTAREA'].includes(el.tagName)) return el.value;
    return '';
  };

  const interesting = 'button,a[href],input,textarea,select,[role],h1,h2,h3,h4,h5,h6,li,ul,ol';
  const nodes = [];
  const bodyText = document.body?.innerText?.trim().replace(/\s+/g, ' ') || '';
  nodes.push({ ref: 'e1', role: 'generic', name: '', text: bodyText, selector: 'body', active: document.activeElement === document.body });
  let index = 2;
  for (const el of document.body.querySelectorAll(interesting)) {
    if (!visible(el)) continue;
    const role = roleFor(el);
    const name = nameFor(el);
    const value = ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName) ? el.value : '';
    nodes.push({
      ref: `e${index++}`,
      role,
      name,
      value,
      text: role === 'generic' ? (el.innerText || '').trim().replace(/\s+/g, ' ') : '',
      selector: selectorFor(el),
      active: document.activeElement === el,
    });
  }
  return nodes;
}
"""


async def dispatch_tool(name: str, arguments: dict, session: BrowserSession, config: LaunchConfig) -> types.CallToolResult:
    if name not in IMPLEMENTED_TOOLS:
        return tool_error(f"Tool registered but not implemented in this Python MCP server yet: {name}")

    try:
        if name == "browser_navigate":
            return await browser_navigate(arguments, session)
        if name == "browser_evaluate":
            return await browser_evaluate(arguments, session)
        if name == "browser_snapshot":
            return await browser_snapshot(arguments, session)
        if name == "browser_resize":
            return await browser_resize(arguments, session)
        if name == "browser_click":
            return await browser_click(arguments, session)
        if name == "browser_hover":
            return await browser_hover(arguments, session)
        if name == "browser_drag":
            return await browser_drag(arguments, session)
        if name == "browser_drop":
            return await browser_drop(arguments, session)
        if name == "browser_type":
            return await browser_type(arguments, session)
        if name == "browser_press_key":
            return await browser_press_key(arguments, session)
        if name == "browser_select_option":
            return await browser_select_option(arguments, session)
        if name == "browser_fill_form":
            return await browser_fill_form(arguments, session)
        if name == "browser_file_upload":
            return await browser_file_upload(arguments, session)
        if name == "browser_handle_dialog":
            return await browser_handle_dialog(arguments, session)
        if name == "browser_run_code_unsafe":
            return await browser_run_code_unsafe(arguments, session)
        if name == "browser_generate_locator":
            return await browser_generate_locator(arguments, session)
        if name == "browser_verify_element_visible":
            return await browser_verify_element_visible(arguments, session)
        if name == "browser_verify_text_visible":
            return await browser_verify_text_visible(arguments, session)
        if name == "browser_verify_list_visible":
            return await browser_verify_list_visible(arguments, session)
        if name == "browser_verify_value":
            return await browser_verify_value(arguments, session)
        if name == "browser_wait_for":
            return await browser_wait_for(arguments, session)
        if name == "browser_console_messages":
            return await browser_console_messages(arguments, session)
        if name == "browser_network_requests":
            return await browser_network_requests(arguments, session)
        if name == "browser_network_request":
            return await browser_network_request(arguments, session)
        if name == "browser_take_screenshot":
            return await browser_take_screenshot(arguments, session, config)
        if name == "browser_tabs":
            return await browser_tabs(arguments, session)
        if name == "browser_navigate_back":
            return await browser_navigate_back(arguments, session)
        if name == "browser_pdf_save":
            return await browser_pdf_save(arguments, session)
        if name.startswith("browser_mouse_"):
            return await browser_mouse_tool(name, arguments, session)
        if name == "browser_close":
            await session.close_browser()
            return text_result("Browser closed")
    except Exception as exc:
        return tool_error(f"{name} failed: {type(exc).__name__}: {exc}")

    return tool_error(f"Tool dispatch missing implementation: {name}")


async def _snapshot_text(session: BrowserSession) -> str:
    page = await session.page()
    nodes: list[dict[str, Any]] = await page.evaluate(SNAPSHOT_SCRIPT)
    session.refs = {node["ref"]: node["selector"] for node in nodes}
    lines = ["### Page", f"- Page URL: {page.url}", f"- Page Title: {await page.title()}", "### Snapshot", "```yaml"]
    for node in nodes:
        role = node["role"]
        active = " [active]" if node.get("active") else ""
        ref = f" [ref={node['ref']}]"
        name = node.get("name") or ""
        value = node.get("value") or ""
        text = node.get("text") or ""
        if name:
            line = f'- {role} "{name}"{active}{ref}'
        else:
            line = f"- {role}{active}{ref}"
        if value:
            line += f": {value}"
        elif text:
            line += f": {text}"
        lines.append(line)
    lines.append("```")
    return "\n".join(lines)


def _with_snapshot(code: str, snapshot: str) -> types.CallToolResult:
    return text_result(f"### Ran Playwright code\n```js\n{code}\n```\n\n{snapshot}")


async def _locator_for(session: BrowserSession, target: str):
    page = await session.page()
    return page.locator(session.resolve_target(target)).first


def _quote(value: str) -> str:
    return json.dumps(value)


async def _center(locator) -> tuple[float, float]:
    box = await locator.bounding_box()
    if not box:
        raise RuntimeError("Element has no bounding box")
    return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2


async def browser_navigate(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    url = arguments["url"]
    page = await session.page()
    await page.goto(url)
    if not any(entry.get("url") == url for entry in session.network_requests):
        session.network_requests.append({
            "url": url,
            "method": "GET",
            "resourceType": "document",
            "requestHeaders": {},
            "requestPostData": None,
            "status": None,
            "responseHeaders": None,
        })
    snapshot = await _snapshot_text(session)
    return _with_snapshot(f"await page.goto('{url}');", snapshot)


async def browser_evaluate(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    page = await session.page()
    function = arguments["function"]
    target = arguments.get("target")
    if target:
        locator = await _locator_for(session, target)
        value = await locator.evaluate(function)
        code = f"await page.locator('{session.resolve_target(target)}').evaluate({function});"
    else:
        value = await page.evaluate(function)
        code = f"await page.evaluate({function});"
    text = json.dumps(value, default=str)
    filename = arguments.get("filename")
    if filename:
        Path(filename).write_text(text)
        text += f"\nSaved to {filename}"
    return text_result(f"### Result\n{text}\n\n### Ran Playwright code\n```js\n{code}\n```")


async def browser_snapshot(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    snapshot = await _snapshot_text(session)
    filename = arguments.get("filename")
    if filename:
        Path(filename).write_text(snapshot)
        return text_result(f"Snapshot saved to {filename}")
    return text_result(snapshot)


async def browser_resize(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    page = await session.page()
    width = int(arguments["width"])
    height = int(arguments["height"])
    await page.set_viewport_size({"width": width, "height": height})
    return text_result(f"### Ran Playwright code\n```js\nawait page.setViewportSize({{ width: {width}, height: {height} }});\n```")


async def browser_click(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    target = arguments["target"]
    locator = await _locator_for(session, target)
    button = arguments.get("button", "left")
    modifiers = arguments.get("modifiers") or []
    if arguments.get("doubleClick"):
        await locator.dblclick(button=button, modifiers=modifiers)
        action = "dblclick"
    else:
        await locator.click(button=button, modifiers=modifiers)
        action = "click"
    snapshot = await _snapshot_text(session)
    return _with_snapshot(f"await page.locator({_quote(session.resolve_target(target))}).{action}();", snapshot)


async def browser_hover(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    target = arguments["target"]
    locator = await _locator_for(session, target)
    await locator.hover()
    snapshot = await _snapshot_text(session)
    return _with_snapshot(f"await page.locator({_quote(session.resolve_target(target))}).hover();", snapshot)


async def browser_drag(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    start = arguments["startTarget"]
    end = arguments["endTarget"]
    start_locator = await _locator_for(session, start)
    end_locator = await _locator_for(session, end)
    await start_locator.drag_to(end_locator)
    snapshot = await _snapshot_text(session)
    return _with_snapshot(
        f"await page.locator({_quote(session.resolve_target(start))}).dragTo(page.locator({_quote(session.resolve_target(end))}));",
        snapshot,
    )


async def browser_drop(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    target = arguments["target"]
    locator = await _locator_for(session, target)
    data = arguments.get("data") or {"text/plain": ""}
    await locator.evaluate(
        """
        (element, data) => {
          const transfer = new DataTransfer();
          for (const [type, value] of Object.entries(data))
            transfer.setData(type, value);
          element.dispatchEvent(new DragEvent('dragover', { bubbles: true, cancelable: true, dataTransfer: transfer }));
          element.dispatchEvent(new DragEvent('drop', { bubbles: true, cancelable: true, dataTransfer: transfer }));
        }
        """,
        data,
    )
    snapshot = await _snapshot_text(session)
    return _with_snapshot(f"await page.locator({_quote(session.resolve_target(target))}).dispatchEvent('drop');", snapshot)


async def browser_type(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    target = arguments["target"]
    text = arguments["text"]
    locator = await _locator_for(session, target)
    if arguments.get("slowly"):
        await locator.type(text)
        code = f"await page.locator({_quote(session.resolve_target(target))}).type({_quote(text)});"
    else:
        await locator.fill(text)
        code = f"await page.locator({_quote(session.resolve_target(target))}).fill({_quote(text)});"
    if arguments.get("submit"):
        await locator.press("Enter")
        code += "\nawait locator.press('Enter');"
    snapshot = await _snapshot_text(session)
    return _with_snapshot(code, snapshot)


async def browser_press_key(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    page = await session.page()
    key = arguments["key"]
    await page.keyboard.press(key)
    snapshot = await _snapshot_text(session)
    return _with_snapshot(f"await page.keyboard.press({_quote(key)});", snapshot)


async def browser_select_option(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    target = arguments["target"]
    values = arguments["values"]
    locator = await _locator_for(session, target)
    await locator.select_option(values)
    snapshot = await _snapshot_text(session)
    return _with_snapshot(f"await page.locator({_quote(session.resolve_target(target))}).selectOption({json.dumps(values)});", snapshot)


async def browser_fill_form(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    lines = []
    for field in arguments["fields"]:
        target = field["target"]
        value = field["value"]
        field_type = field["type"]
        locator = await _locator_for(session, target)
        if field_type in {"checkbox", "radio"}:
            checked = str(value).lower() == "true"
            await locator.set_checked(checked)
            lines.append(f"await page.locator({_quote(session.resolve_target(target))}).setChecked({str(checked).lower()});")
        elif field_type == "combobox":
            await locator.select_option(label=value)
            lines.append(f"await page.locator({_quote(session.resolve_target(target))}).selectOption({{ label: {_quote(value)} }});")
        else:
            await locator.fill(value)
            lines.append(f"await page.locator({_quote(session.resolve_target(target))}).fill({_quote(value)});")
    snapshot = await _snapshot_text(session)
    return _with_snapshot("\n".join(lines), snapshot)


async def browser_file_upload(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    paths = arguments.get("paths") or []
    if not session.pending_file_chooser:
        return tool_error("No file chooser is pending. Trigger a file chooser before calling browser_file_upload.")
    if paths:
        await session.pending_file_chooser.set_files(paths)
        message = f"Uploaded files: {', '.join(paths)}"
    else:
        await session.pending_file_chooser.set_files([])
        message = "File chooser cancelled"
    session.pending_file_chooser = None
    return text_result(message)


async def browser_handle_dialog(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    if not session.pending_dialog:
        return tool_error("No dialog is pending")
    dialog = session.pending_dialog
    if arguments["accept"]:
        await dialog.accept(arguments.get("promptText"))
        result = "accepted"
    else:
        await dialog.dismiss()
        result = "dismissed"
    session.pending_dialog = None
    return text_result(f"Dialog {result}")


async def browser_run_code_unsafe(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    page = await session.page()
    code = Path(arguments["filename"]).read_text() if arguments.get("filename") else arguments.get("code", "")
    if code.strip().startswith("()") or code.strip().startswith("async ()"):
        value = await page.evaluate(code)
        return text_result(json.dumps(value, default=str))
    return tool_error("browser_run_code_unsafe supports browser-context JavaScript functions only in this Python implementation")


async def browser_generate_locator(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    target = arguments["target"]
    return text_result(f"page.locator({_quote(session.resolve_target(target))})")


async def browser_verify_element_visible(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    page = await session.page()
    locator = page.get_by_role(arguments["role"], name=arguments["accessibleName"]).first
    await locator.wait_for(state="visible")
    return text_result(f"Element is visible: {arguments['role']} {arguments['accessibleName']}")


async def browser_verify_text_visible(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    page = await session.page()
    await page.get_by_text(arguments["text"]).first.wait_for(state="visible")
    return text_result(f"Text is visible: {arguments['text']}")


async def browser_verify_list_visible(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    locator = await _locator_for(session, arguments["target"])
    await locator.wait_for(state="visible")
    text = await locator.inner_text()
    missing = [item for item in arguments["items"] if item not in text]
    if missing:
        return tool_error(f"List is missing items: {', '.join(missing)}")
    return text_result(f"List is visible: {arguments['element']}")


async def browser_verify_value(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    locator = await _locator_for(session, arguments["target"])
    expected = arguments["value"]
    actual: str
    if arguments["type"] in {"checkbox", "radio"}:
        actual = str(await locator.is_checked()).lower()
    else:
        actual = await locator.input_value()
    if actual != expected:
        return tool_error(f"Expected {expected}, got {actual}")
    return text_result(f"Value verified: {expected}")


async def browser_wait_for(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    page = await session.page()
    if "time" in arguments:
        await asyncio.sleep(float(arguments["time"]))
        snapshot = await _snapshot_text(session)
        return text_result(f"### Result\nWaited for {arguments['time']} seconds\n\n{snapshot}")
    if "text" in arguments:
        await page.get_by_text(arguments["text"]).first.wait_for(state="visible")
        snapshot = await _snapshot_text(session)
        return text_result(
            f"### Result\nWaited for {arguments['text']}\n### Ran Playwright code\n```js\nawait page.getByText({_quote(arguments['text'])}).first().waitFor({{ state: 'visible' }});\n```\n\n{snapshot}"
        )
    if "textGone" in arguments:
        await page.get_by_text(arguments["textGone"]).first.wait_for(state="hidden")
        snapshot = await _snapshot_text(session)
        return text_result(
            f"### Result\nWaited for {arguments['textGone']} to disappear\n### Ran Playwright code\n```js\nawait page.getByText({_quote(arguments['textGone'])}).first().waitFor({{ state: 'hidden' }});\n```\n\n{snapshot}"
        )
    snapshot = await _snapshot_text(session)
    return text_result(f"### Result\nWait completed\n\n{snapshot}")


async def browser_console_messages(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    level = arguments.get("level", "info")
    severity = {"debug": 0, "info": 1, "warning": 2, "error": 3}
    minimum = severity.get(level, 1)
    lines = []
    for index, message in enumerate(session.console_messages, start=1):
        message_level = "warning" if message["level"] == "warning" else message["level"]
        if severity.get(message_level, 1) >= minimum:
            lines.append(f"{index}: [{message['level']}] {message['text']}")
    text = "\n".join(lines) if lines else "No console messages"
    filename = arguments.get("filename")
    if filename:
        Path(filename).write_text(text)
        return text_result(f"Console messages saved to {filename}")
    return text_result(text)


async def browser_network_requests(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    include_static = bool(arguments.get("static"))
    pattern = re.compile(arguments["filter"]) if arguments.get("filter") else None
    static_types = {"image", "font", "stylesheet", "script"}
    lines = []
    for index, request in enumerate(session.network_requests, start=1):
        if not include_static and request.get("resourceType") in static_types and request.get("status") and request["status"] < 400:
            continue
        if pattern and not pattern.search(request["url"]):
            continue
        status = request.get("status") or "pending"
        lines.append(f"{index}: {request['method']} {request['url']} {status}")
    text = "\n".join(lines) if lines else "No network requests"
    filename = arguments.get("filename")
    if filename:
        Path(filename).write_text(text)
        return text_result(f"Network requests saved to {filename}")
    return text_result(text)


async def browser_network_request(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    index = int(arguments["index"]) - 1
    if index < 0 or index >= len(session.network_requests):
        return tool_error(f"Network request index out of range: {arguments['index']}")
    request = session.network_requests[index]
    part = arguments.get("part")
    if part == "request-headers":
        data = request.get("requestHeaders")
    elif part == "request-body":
        data = request.get("requestPostData") or ""
    elif part == "response-headers":
        data = request.get("responseHeaders") or {}
    else:
        data = request
    text = json.dumps(data, indent=2, default=str)
    filename = arguments.get("filename")
    if filename:
        Path(filename).write_text(text)
        return text_result(f"Network request saved to {filename}")
    return text_result(text)


async def browser_take_screenshot(arguments: dict, session: BrowserSession, config: LaunchConfig) -> types.CallToolResult:
    page = await session.page()
    image_type = arguments.get("type", "png")
    filename = arguments.get("filename")
    target = arguments.get("target")
    full_page = bool(arguments.get("fullPage"))

    if target:
        locator = await _locator_for(session, target)
        data = await locator.screenshot(type=image_type)
    else:
        data = await page.screenshot(type=image_type, full_page=full_page)

    if filename:
        Path(filename).write_bytes(data)

    if not config.image_responses_allowed:
        return text_result(f"Screenshot captured{f' and saved to {filename}' if filename else ''}")

    encoded = base64.b64encode(data).decode("ascii")
    return image_result(encoded, f"image/{image_type}", f"Screenshot captured{f' and saved to {filename}' if filename else ''}")


async def browser_tabs(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    action = arguments["action"]
    page = await session.page()
    context = page.context

    if action == "new":
        new_page = await context.new_page()
        session.set_current_page(new_page)
        if arguments.get("url"):
            await new_page.goto(arguments["url"])
        page = new_page
    elif action == "select":
        index = int(arguments["index"])
        page = context.pages[index]
        session.set_current_page(page)
        await page.bring_to_front()
    elif action == "close":
        index = int(arguments["index"]) if "index" in arguments else context.pages.index(page)
        await context.pages[index].close()
        if context.pages:
            session.set_current_page(context.pages[min(index, len(context.pages) - 1)])
    elif action != "list":
        return tool_error(f"Unknown browser_tabs action: {action}")

    current = await session.page()
    lines = []
    for index, tab in enumerate(current.context.pages):
        marker = " [selected]" if tab == current else ""
        lines.append(f"{index}: {tab.url}{marker}")
    return text_result("\n".join(lines))


async def browser_navigate_back(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    page = await session.page()
    await page.go_back()
    snapshot = await _snapshot_text(session)
    return _with_snapshot("await page.goBack();", snapshot)


async def browser_pdf_save(arguments: dict, session: BrowserSession) -> types.CallToolResult:
    page = await session.page()
    filename = arguments.get("filename") or f"page-{int(time.time())}.pdf"
    await page.pdf(path=filename)
    return text_result(f"PDF saved to {filename}")


async def browser_mouse_tool(name: str, arguments: dict, session: BrowserSession) -> types.CallToolResult:
    page = await session.page()
    mouse = page.mouse
    if name == "browser_mouse_move_xy":
        await mouse.move(arguments["x"], arguments["y"])
    elif name == "browser_mouse_click_xy":
        await mouse.click(arguments["x"], arguments["y"], button=arguments.get("button", "left"), click_count=int(arguments.get("clickCount", 1)), delay=arguments.get("delay", 0))
    elif name == "browser_mouse_drag_xy":
        await mouse.move(arguments["startX"], arguments["startY"])
        await mouse.down()
        await mouse.move(arguments["endX"], arguments["endY"])
        await mouse.up()
    elif name == "browser_mouse_down":
        await mouse.down(button=arguments.get("button", "left"))
    elif name == "browser_mouse_up":
        await mouse.up(button=arguments.get("button", "left"))
    elif name == "browser_mouse_wheel":
        await mouse.wheel(arguments.get("deltaX", 0), arguments.get("deltaY", 0))
    else:
        return tool_error(f"Unknown mouse tool: {name}")
    snapshot = await _snapshot_text(session)
    return _with_snapshot(f"// {name}", snapshot)
