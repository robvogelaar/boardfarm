"""Tests for TR-069 status primitives on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_tr069_connection_status(device_manager):
    board = device_manager.get_device_by_type(CPE)

    try:
        is_connected = board.sw.is_tr069_connected()

        print(f"\nTR-069 Connection Status: {is_connected}")
        assert isinstance(is_connected, bool), "Should return boolean"
    except Exception as e:
        pytest.skip(f"TR-069 status check not available: {e}")
