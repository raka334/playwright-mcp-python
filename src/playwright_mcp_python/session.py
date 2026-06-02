"""Stateful browser session for MCP tool calls."""

from __future__ import annotations

from typing import Any

from playwright.async_api import Browser, BrowserContext, Dialog, FileChooser, Page, Playwright, async_playwright

from playwright_mcp_python.config import LaunchConfig


class BrowserSession:
    def __init__(self, config: LaunchConfig) -> None:
        self._config = config
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._owns_browser = False
        self.refs: dict[str, str] = {}
        self.console_messages: list[dict[str, str]] = []
        self.network_requests: list[dict[str, Any]] = []
        self.pending_dialog: Dialog | None = None
        self.pending_file_chooser: FileChooser | None = None
        self._instrumented_pages: set[int] = set()

    async def page(self) -> Page:
        if self._page and not self._page.is_closed():
            return self._page

        await self._ensure_browser()
        assert self._context is not None
        self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()
        self._page.set_default_timeout(self._config.timeout_action_ms)
        self._page.set_default_navigation_timeout(self._config.timeout_navigation_ms)
        self._instrument_page(self._page)
        return self._page

    def set_current_page(self, page: Page) -> None:
        self._page = page
        self._instrument_page(page)

    def _instrument_page(self, page: Page) -> None:
        page_id = id(page)
        if page_id in self._instrumented_pages:
            return
        self._instrumented_pages.add(page_id)

        def on_console(message) -> None:
            self.console_messages.append({
                "level": message.type,
                "text": message.text,
                "location": str(message.location),
            })

        def on_request(request) -> None:
            self.network_requests.append({
                "url": request.url,
                "method": request.method,
                "resourceType": request.resource_type,
                "requestHeaders": request.headers,
                "requestPostData": request.post_data,
                "status": None,
                "responseHeaders": None,
            })

        async def on_response(response) -> None:
            for entry in reversed(self.network_requests):
                if entry["url"] == response.url and entry["status"] is None:
                    entry["status"] = response.status
                    try:
                        entry["responseHeaders"] = await response.all_headers()
                    except Exception:
                        entry["responseHeaders"] = response.headers
                    break

        def on_dialog(dialog: Dialog) -> None:
            self.pending_dialog = dialog

        def on_file_chooser(file_chooser: FileChooser) -> None:
            self.pending_file_chooser = file_chooser

        page.on("console", on_console)
        page.on("request", on_request)
        page.on("response", on_response)
        page.on("dialog", on_dialog)
        page.on("filechooser", on_file_chooser)

    def resolve_target(self, target: str) -> str:
        return self.refs.get(target, target)

    async def _ensure_browser(self) -> None:
        if self._browser and self._browser.is_connected():
            return

        self._playwright = await async_playwright().start()
        browser_type = self._playwright.chromium
        if self._config.cdp_endpoint:
            self._browser = await browser_type.connect_over_cdp(self._config.cdp_endpoint, timeout=self._config.timeout_navigation_ms)
            self._owns_browser = False
            self._context = self._browser.contexts[0] if self._browser.contexts else await self._browser.new_context()
        else:
            channel = "chrome" if self._config.browser == "chrome" else None
            self._browser = await browser_type.launch(headless=self._config.headless, channel=channel)
            self._owns_browser = True
            self._context = await self._browser.new_context()

    async def close_browser(self) -> None:
        if self._browser and self._browser.is_connected():
            await self._browser.close()
        self._browser = None
        self._context = None
        self._page = None
        self.refs = {}
        self.pending_dialog = None
        self.pending_file_chooser = None
        self._instrumented_pages = set()

    async def shutdown(self) -> None:
        if self._browser and self._browser.is_connected():
            if self._owns_browser:
                await self._browser.close()
            else:
                await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self.refs = {}
        self.pending_dialog = None
        self.pending_file_chooser = None
        self._instrumented_pages = set()
