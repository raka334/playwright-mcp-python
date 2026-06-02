"""Launch configuration for the Python Playwright MCP server."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LaunchConfig:
    cdp_endpoint: str | None = None
    browser: str = "chromium"
    headless: bool = True
    timeout_action_ms: int = 30000
    timeout_navigation_ms: int = 60000
    image_responses: str = "allow"
    caps: set[str] = field(default_factory=lambda: {"testing"})

    @property
    def image_responses_allowed(self) -> bool:
        return self.image_responses != "omit"
