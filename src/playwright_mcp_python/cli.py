"""CLI entrypoint for playwright-mcp-python."""

from __future__ import annotations

import argparse
import asyncio

from playwright_mcp_python.config import LaunchConfig
from playwright_mcp_python.server import run_stdio


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="playwright-mcp-python")
    subparsers = parser.add_subparsers(dest="command")
    install = subparsers.add_parser("install-browser", help="Install Playwright browser dependencies")
    install.set_defaults(command="install-browser")

    parser.add_argument("--cdp-endpoint")
    parser.add_argument("--browser", choices=["chromium", "chrome"], default="chromium")
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--timeout-action", type=int, default=30000)
    parser.add_argument("--timeout-navigation", type=int, default=60000)
    parser.add_argument("--image-responses", choices=["allow", "omit"], default="allow")
    parser.add_argument("--caps", action="append", default=[])
    parser.add_argument("--vision", action="store_true", help="Legacy alias for --caps vision")
    return parser


def parse_config(argv: list[str] | None = None) -> LaunchConfig:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "install-browser":
        parser.exit(0, "install browser dependencies with: python -m playwright install chromium\n")

    caps = set(args.caps or []) or {"testing"}
    if args.vision:
        caps.add("vision")
    return LaunchConfig(
        cdp_endpoint=args.cdp_endpoint,
        browser=args.browser,
        headless=args.headless,
        timeout_action_ms=args.timeout_action,
        timeout_navigation_ms=args.timeout_navigation,
        image_responses=args.image_responses,
        caps=caps,
    )


def main(argv: list[str] | None = None) -> None:
    config = parse_config(argv)
    asyncio.run(run_stdio(config))


if __name__ == "__main__":
    main()
