# Port Upstream Tests for Conformance

We will use Microsoft Playwright MCP's `tests/` directory as the behavioral conformance reference for the Python-native MCP server and port relevant cases into Python tests. This is preferable to only writing independent smoke tests because the package's goal is tool-contract compatibility with Microsoft Playwright MCP; ported tests make drift visible while avoiding the complexity of running the TypeScript test harness directly against the Python implementation.
