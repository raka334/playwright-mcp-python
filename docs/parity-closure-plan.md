# Playwright MCP Parity Closure Plan

## Goal

Move from tool-contract parity to measured behavioral parity against pinned `@playwright/mcp@0.0.75`.

## Risk Areas And Closure Checks

1. Exact snapshot formatting for complex accessibility trees
   - Add live upstream comparisons for `browser_snapshot` on pages with buttons, inputs, lists, labels, and active elements.
   - Compare normalized semantic tokens: roles, names, refs, active marker, and visible text.

2. Generated Playwright code strings
   - Add live upstream comparisons for `browser_navigate`, `browser_click`, `browser_type`, and `browser_wait_for`.
   - Compare normalized code intent: operation name, target presence, URL/text/value.

3. Advanced tool behavior
   - Add smoke coverage for `browser_run_code_unsafe`, file upload, dialog handling, drag/drop, PDF, and vision mouse tools.
   - Treat non-translatable Node Playwright snippets as documented non-parity until a Python translation layer exists.

4. Downloads/uploads/dialog races
   - Add focused tests that create pending file chooser and pending dialog before calling the MCP tool.
   - Keep tests local and deterministic.

5. Remote CDP endpoint parity
   - Launch local Chrome with `--remote-debugging-port` and run the Python MCP server through `--cdp-endpoint`.
   - Verify tools/list, navigate, snapshot, click, and screenshot work over CDP connection mode.

6. Byte-for-byte output compatibility
   - Do not claim full byte-for-byte compatibility yet.
   - Add normalized live upstream comparisons first; promote individual tools to exact golden comparisons only when upstream output is stable and inline.

## Acceptance Criteria

- Non-live conformance suite passes.
- Live upstream registry/schema comparison passes.
- Live upstream normalized behavior comparisons pass for core action tools.
- Local CDP endpoint parity test passes.
- Any remaining non-parity is documented explicitly.
