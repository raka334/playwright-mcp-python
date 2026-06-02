# Python Playwright MCP Implementation Plan

## Goal

Build `playwright_mcp_python`, a Python-native MCP server that is tool-contract compatible with Microsoft Playwright MCP. Clients should be able to replace `npx @playwright/mcp` with `playwright-mcp-python` while keeping the same MCP tool calls.

## Compatibility Target

- Preserve tool names, input schemas, result envelopes, and client-visible error semantics.
- Use a pinned Microsoft Playwright MCP version as the compatibility target.
- Snapshot Microsoft `tools/list` into a versioned schema fixture.
- Validate the Python tool registry against the schema fixture.
- Use Microsoft Playwright MCP tests as upstream behavioral references and port relevant cases into Python.

## Architecture Decisions

- Use the official Python MCP SDK lower-level server API, not FastMCP decorators.
- Use stdio as the first transport.
- Use Python Playwright async API as the primary browser engine backend.
- Support local Chromium launch and `--cdp-endpoint` in the MVP.
- Keep CDP endpoint support vendor-neutral in package code and docs.
- Use one browser session per MCP server process.
- Use lazy browser startup on first tool call that needs a page.
- Treat `target` strings as selectors initially; add snapshot-ref resolution later.
- Return MCP-native tool errors with `isError=True` for tool-level failures.
- Expose tools only in the first MCP surface.

## Package Shape

```text
playwright_mcp_python/
  __init__.py
  cli.py
  server.py
  registry.py
  session.py
  results.py
  schemas/
    microsoft-tools-list.json
  tools/
    __init__.py
    browser.py
    navigation.py
    screenshots.py
    tabs.py
    unimplemented.py
tests/
  conformance/
    test_capabilities.py
    test_cli.py
    test_core.py
    test_click.py
```

## CLI MVP

Support Microsoft-style launch configuration first:

- `--cdp-endpoint <url>`
- `--browser chromium|chrome`
- `--headless`
- `--timeout-action <ms>`
- `--timeout-navigation <ms>`
- `--image-responses allow|omit`
- `--caps <capability>`
- legacy `--vision` if needed by ported capability tests

Generic CDP examples only:

```bash
playwright-mcp-python --cdp-endpoint http://localhost:9222
playwright-mcp-python --cdp-endpoint wss://host.example/devtools/browser/session
```

## First Milestone

Deliver a vertical slice proving package startup, MCP stdio lifecycle, CLI launch configuration, schema registry, browser lifecycle, and minimal browser tools.

Implemented tools:

- `browser_navigate`
- `browser_evaluate`
- `browser_take_screenshot`
- `browser_close`
- `browser_tabs` with `list`

Registered but explicitly unimplemented:

- All other tools from the schema fixture.
- These remain visible in `tools/list` and return a stable MCP tool error when called.

## Test Plan

Schema/conformance tests:

- Start Microsoft Playwright MCP at the pinned compatibility target.
- Capture or compare `tools/list` against `schemas/microsoft-tools-list.json`.
- Assert Python server exposes the same registry for the selected capabilities.

Ported upstream tests:

- `capabilities.spec.ts` -> tool list and capability-gated tools.
- `cli.spec.ts` -> CLI help/install-browser equivalent where applicable.
- `core.spec.ts` -> `browser_navigate` flow.
- `click.spec.ts` -> add after `browser_click` and target-ref resolution begin.

Milestone 1 acceptance criteria:

- `playwright-mcp-python --help` works.
- MCP initialize and `tools/list` work over stdio.
- Registry matches the pinned schema fixture for MVP capabilities.
- Local Chromium can navigate to a test page.
- `browser_evaluate` returns a valid MCP result envelope.
- `browser_take_screenshot` returns image content when image responses are allowed.
- `browser_tabs list` returns the current tab state.
- Unimplemented registered tools return `isError=True` with a clear message.

## Deferred

- Exact Microsoft snapshot formatting.
- Snapshot-ref target resolution.
- Full core tool set: click, type, keypress, wait, snapshot, console, network.
- PDF and vision capabilities beyond registry compatibility.
- Streamable HTTP/SSE transports.
- Firefox/WebKit support.
- Vendor-specific CDP helpers.
