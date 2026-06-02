# Python Playwright MCP Alternative

This context describes a Python-native replacement for Microsoft's Playwright MCP server, intended to preserve the MCP tool contract while improving control over browser connection modes.

## Language

**Python-native MCP Server**:
A Python package that implements the same MCP tool contract as Microsoft's Playwright MCP server.
_Avoid_: Python helper library, wrapper script

**MCP Tool Contract**:
The externally visible tool names, input schemas, outputs, and behavior that MCP clients depend on.
_Avoid_: API, function list

**MCP Surface**:
The set of MCP primitives exposed by the Python-native MCP Server.
_Avoid_: package API, browser API

**Tool-contract Compatibility**:
Compatibility at the MCP boundary: same tool names, same required and optional arguments, same JSON schema shape, and same client-visible success or error semantics.
_Avoid_: exact clone, full behavioral parity

**Browser Engine Backend**:
The internal mechanism used by the Python-native MCP Server to drive browsers.
_Avoid_: endpoint, transport

**Raw CDP Escape Hatch**:
Direct Chrome DevTools Protocol calls used only where the primary backend cannot provide the required browser behavior.
_Avoid_: primary implementation, replacement backend

**Connection Mode**:
The way the Python-native MCP Server obtains a browser session: launching a local browser or connecting to an existing CDP endpoint.
_Avoid_: transport, backend

**CDP Endpoint**:
A Chrome DevTools Protocol endpoint supplied by the user, such as `http://localhost:9222` or `wss://host.example/devtools/browser/session`.
_Avoid_: product-specific endpoint, Playwright wire endpoint

**Tool Registry**:
The complete catalog of MCP tools exposed by the Python-native MCP Server, including tools whose behavior is not implemented yet.
_Avoid_: implemented tools, feature list

**Core Tool Set**:
The first implemented group of high-value MCP tools: navigation, evaluation, screenshot, snapshot, click, type, keypress, wait, tabs, console, and network.
_Avoid_: all tools, MVP contract

**First Milestone**:
The first vertical slice proving package startup, MCP stdio lifecycle, CLI launch configuration, schema registry, browser lifecycle, and a minimal set of working browser tools.
_Avoid_: full implementation, test-only milestone

**Implementation Boundary**:
A source-code separation between protocol handling, tool registry, browser session state, and individual tool behavior.
_Avoid_: monolithic server module, framework-shaped structure

**Async Runtime**:
The internal execution model where MCP handling and browser operations use Python async APIs.
_Avoid_: sync wrapper, mixed runtime

**Registered-but-Unimplemented Tool**:
A tool that appears in the Tool Registry with its schema but returns a clear MCP tool error until its behavior is implemented.
_Avoid_: hidden tool, fake success

**Schema Fixture**:
A versioned snapshot of Microsoft Playwright MCP's `tools/list` output used as the source of truth for tool-contract compatibility.
_Avoid_: docs copy, handwritten schema

**Conformance Test**:
A test that compares the Python-native MCP Server against Microsoft Playwright MCP at the MCP boundary.
_Avoid_: ordinary unit test, smoke test

**Upstream Test Reference**:
Microsoft Playwright MCP's own tests used as behavioral validation references for the Python-native MCP Server.
_Avoid_: copied contract, unrelated examples

**Ported Upstream Test**:
A Python test mapped from a Microsoft Playwright MCP test case, preserving the scenario and expected compatibility assertion where feasible.
_Avoid_: loose smoke test, unrelated regression test

**Compatibility Target**:
The pinned Microsoft Playwright MCP package version that the Schema Fixture and conformance tests compare against.
_Avoid_: latest, floating dependency

**MCP SDK Layer**:
The part of the official Python MCP SDK used to implement protocol behavior and tool registration.
_Avoid_: framework, transport

**Browser Session**:
The stateful browser, context, current page, and tab list owned by one MCP server process.
_Avoid_: request session, shared global browser

**Lazy Browser Startup**:
Creating the browser, context, and initial page only when the first tool call needs them.
_Avoid_: explicit open tool, mandatory startup launch

**Browser Ownership**:
Whether the MCP server created the browser and is responsible for closing it, or only connected to an externally owned browser.
_Avoid_: connection status, page lifecycle

**Launch Configuration**:
The command-line options that define how the Python-native MCP Server starts and connects to browsers.
_Avoid_: environment-only config, Python-only config

**Distribution Name**:
The installable Python package and console command used to run the Python-native MCP Server.
_Avoid_: internal module name, repo name

**Result Envelope**:
The MCP `CallToolResult` shape returned to clients, including content items and error status.
_Avoid_: prose output, structured-only response

**Tool Error**:
A client-visible MCP tool result with `isError=True` and explanatory content.
_Avoid_: Python exception for browser action failure, custom error dict

**Browser Snapshot**:
The accessibility-oriented page representation used by clients to identify elements for later tool calls.
_Avoid_: raw HTML dump, screenshot

**Image Response**:
An MCP content item that returns screenshot bytes to the client when image responses are allowed.
_Avoid_: base64 text message, disk-only screenshot

**Target Resolution**:
The process of turning a tool's `target` string into a Playwright locator or element.
_Avoid_: selector-only API, human label matching

**Supported Browser Family**:
The browser engine family the Python-native MCP Server is expected to drive correctly.
_Avoid_: cloud platform, browser brand

## Relationships

- A **Python-native MCP Server** preserves the **MCP Tool Contract** through **Tool-contract Compatibility**.
- The first **MCP Surface** is tools only.
- A **Python-native MCP Server** uses Python Playwright as its primary **Browser Engine Backend**.
- A **Raw CDP Escape Hatch** supplements the primary **Browser Engine Backend** when needed.
- A **Connection Mode** may be local browser launch or CDP endpoint connection in the MVP.
- A **CDP Endpoint** is accepted through **Launch Configuration** without product-specific assumptions.
- A **Tool Registry** may include tools outside the implemented **Core Tool Set**.
- The **First Milestone** implements `browser_navigate`, `browser_evaluate`, `browser_take_screenshot`, `browser_close`, and `browser_tabs list`.
- **Implementation Boundaries** separate `server.py`, `cli.py`, `registry.py`, `session.py`, `tools/*.py`, and schema fixtures.
- The Python-native MCP Server uses an **Async Runtime** internally.
- A **Registered-but-Unimplemented Tool** remains visible to clients through the **Tool Registry**.
- A **Schema Fixture** defines the expected **Tool Registry**.
- A **Conformance Test** protects **Tool-contract Compatibility**.
- An **Upstream Test Reference** guides behavioral validation beyond schema compatibility.
- A **Ported Upstream Test** validates the Python-native MCP Server against an upstream scenario.
- A **Compatibility Target** defines which Microsoft Playwright MCP version is being matched.
- The **MCP SDK Layer** should be the official Python MCP SDK's lower-level server API.
- One **Browser Session** belongs to one MCP server process.
- **Lazy Browser Startup** creates a **Browser Session** on first use.
- **Browser Ownership** determines shutdown cleanup behavior.
- **Launch Configuration** should use Microsoft-style CLI flags first.
- The **Distribution Name** is `playwright_mcp_python` for imports and `playwright-mcp-python` for the console command.
- **Result Envelope** compatibility is required before exact human-readable text parity.
- Browser action failures should become **Tool Errors** where possible.
- **Browser Snapshot** should start from an accessibility or ARIA tree rather than raw DOM HTML.
- Screenshots should produce an **Image Response** when configured to allow image responses.
- **Target Resolution** initially treats target strings as selectors when possible.
- The first **Supported Browser Family** is Chromium.

## Example Dialogue

> **Dev:** "Can clients swap from `npx @playwright/mcp` to our Python package without changing tool calls?"
> **Domain expert:** "Yes — preserving the MCP Tool Contract is the point of the Python-native MCP Server."

## Flagged Ambiguities

- "1:1 alternative" was resolved to mean same MCP tool contract, not just similar Python helper functions.
- "1:1 alternative" does not initially mean exact behavioral cloning of Microsoft's implementation.
- Resources and prompts are deferred unless the **Compatibility Target** requires them.
- Playwright wire-protocol endpoint support is not part of the first **Connection Mode** set.
- The first release preserves the full **Tool Registry** but implements the **Core Tool Set** first.
- The **First Milestone** should be validated with Python tests plus mapped cases from Microsoft `capabilities.spec.ts`, `cli.spec.ts`, and the simplest `core.spec.ts` flows.
- The MCP boundary should stay separate from browser behavior so schema compatibility can be tested independently.
- The first release exposes a CLI entrypoint, not separate sync Python library wrappers.
- Unimplemented tools should fail explicitly rather than being hidden or returning fake success.
- Tool schemas should be validated against a versioned **Schema Fixture**, not recreated manually.
- Conformance tests may depend on Node and Microsoft Playwright MCP but should be separable from ordinary test runs.
- Microsoft Playwright MCP's `tests/` directory is the first **Upstream Test Reference**.
- Microsoft `capabilities.spec.ts`, `cli.spec.ts`, `core.spec.ts`, and `click.spec.ts` should be ported into Python conformance tests early.
- Ported upstream tests should preserve scenario names and assertions where feasible, relaxing exact response text only until the formatter supports it.
- The **Compatibility Target** should be updated intentionally, not by tracking `latest` automatically.
- FastMCP decorator-generated schemas are avoided for tool-contract compatibility because schema drift would be hard to detect.
- Tool calls operate on the current page in the process-owned **Browser Session** unless the tool explicitly changes tabs.
- Tools that need a page may create an initial `about:blank` page if no page exists yet.
- On shutdown, launched browsers are closed; externally connected CDP browsers are disconnected unless `browser_close` was explicitly called.
- JSON config may be added later, but CLI compatibility is the first **Launch Configuration** target.
- Exact result prose may differ in the MVP if the **Result Envelope** remains compatible.
- Startup and protocol failures may still raise server-level errors rather than **Tool Errors**.
- Exact Microsoft **Browser Snapshot** formatting can be improved through golden tests after the MVP.
- Screenshot filename saving can be added alongside or shortly after **Image Response** support.
- Snapshot-reference **Target Resolution** can be added after selector-based targeting works.
- Firefox and WebKit support are deferred until Chromium support is reliable.
- CDP examples should use local Chrome remote debugging or placeholder remote WebSocket URLs, not vendor-specific names.
