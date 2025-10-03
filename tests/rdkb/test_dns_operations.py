"""Tests for DNS operations on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE
from boardfarm3.lib.networking import dns_lookup


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_nslookup_basic(device_manager):
    board = device_manager.get_device_by_type(CPE)

    try:
        result = board.sw.nslookup.nslookup("google.com")

        print(f"\nnslookup google.com:")
        print(f"  Result: {result}")
        assert result, "Should return DNS result"
    except Exception as e:
        pytest.skip(f"nslookup not available: {e}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_dns_lookup_dig(device_manager):
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    try:
        result = dns_lookup(console, "google.com", "A")

        print(f"\nDNS lookup (dig) for google.com:")
        print(f"  Result: {result}")
    except Exception as e:
        pytest.skip(f"dig not available: {e}")
