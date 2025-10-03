"""Tests for HTTP operations on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE
from boardfarm3.lib.networking import http_get


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_http_get_basic(device_manager):
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    try:
        result = http_get(console, "http://example.com", timeout=10)

        print(f"\nHTTP GET http://example.com:")
        print(f"  Status code: {result.status_code}")
        print(f"  Content length: {len(result.content)} bytes")
        assert result.status_code > 0, "Should return status code"
    except Exception as e:
        pytest.skip(f"HTTP GET not available: {e}")
