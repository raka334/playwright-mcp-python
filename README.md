# playwright-mcp-python

Python-native MCP server for browser automation with Playwright.

This package is designed as a Python implementation of the Playwright MCP tool contract. It exposes the same tool names and input schemas as pinned `@playwright/mcp@0.0.75`, while running through the official Python MCP SDK and Python Playwright.

## Install

```bash
pip install playwright-mcp-python
python -m playwright install chromium
```

## Run

Local browser launch:

```bash
playwright-mcp-python --browser chromium
```

Connect to an existing Chrome DevTools Protocol endpoint:

```bash
playwright-mcp-python --cdp-endpoint http://localhost:9222
```

## Compatibility Target

- Tool names: captured from `@playwright/mcp@0.0.75`
- Input schemas: captured from `@playwright/mcp@0.0.75`
- Transport: MCP over stdio
- Browser backend: Python Playwright, Chromium-first

## Verification

```bash
pytest tests/conformance -v -m 'not upstream_live'
pytest tests/conformance/test_upstream_live.py -v -m upstream_live
```

The live upstream tests compare this package against pinned Microsoft Playwright MCP for tool registry/schema parity and normalized behavior on core browser actions.
