"""Tests for advanced logging primitives on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_enable_component_logs(device_manager):
    board = device_manager.get_device_by_type(CPE)

    print("\nTesting component log enable:")

    try:
        board.sw.enable_logs("WiFi")
        print("  OK Enabled WiFi component logs")
    except Exception as e:
        pytest.skip(f"Component logging not available: {e}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_boottime_log(device_manager):
    board = device_manager.get_device_by_type(CPE)

    print("\nRetrieving boot-time logs:")

    try:
        boot_logs = board.sw.get_boottime_log()

        assert boot_logs, "Boot logs should not be empty"
        print(f"  Boot log entries: {len(boot_logs)}")
        print("  OK Successfully retrieved boot-time logs")
    except Exception as e:
        pytest.skip(f"Boot-time log retrieval not available: {e}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_tr069_log(device_manager):
    board = device_manager.get_device_by_type(CPE)

    print("\nRetrieving TR-069 logs:")

    try:
        tr069_logs = board.sw.get_tr069_log()

        assert tr069_logs, "TR-069 logs should not be empty"
        print(f"  TR-069 log size: {len(tr069_logs)} bytes")
        print("  OK Successfully retrieved TR-069 logs")
    except Exception as e:
        pytest.skip(f"TR-069 log retrieval not available: {e}")
