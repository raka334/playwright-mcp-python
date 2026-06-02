# Use Low-Level Python MCP SDK

We will build the Python-native Playwright MCP alternative on the official Python MCP SDK's lower-level server API rather than FastMCP decorators or hand-rolled JSON-RPC. The lower-level API gives us precise control over `tools/list` schemas and `CallToolResult` envelopes, which matters because the package's primary goal is tool-contract compatibility with Microsoft Playwright MCP; FastMCP would be faster to write but risks schema drift, while hand-rolled JSON-RPC would add protocol risk.
