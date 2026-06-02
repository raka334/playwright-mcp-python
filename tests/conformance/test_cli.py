from __future__ import annotations

import pytest

from playwright_mcp_python.cli import build_parser, parse_config


def test_install_browser_help(capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["install-browser", "--help"])
    output = capsys.readouterr().out
    assert "install" in output


def test_legacy_vision_option() -> None:
    config = parse_config(["--vision"])
    assert "vision" in config.caps


def test_cdp_endpoint_option() -> None:
    config = parse_config(["--cdp-endpoint", "http://localhost:9222"])
    assert config.cdp_endpoint == "http://localhost:9222"
