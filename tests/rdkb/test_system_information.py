"""Tests for system information primitives on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_uptime(device_manager):
    board = device_manager.get_device_by_type(CPE)

    uptime = board.sw.get_seconds_uptime()

    assert uptime > 0, "Uptime should be greater than zero"
    print(f"\nSystem uptime: {uptime} seconds ({uptime / 3600:.2f} hours)")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_device_online_status(device_manager):
    board = device_manager.get_device_by_type(CPE)

    is_online = board.sw.is_online()

    assert isinstance(is_online, bool), "is_online should return boolean"
    print(f"\nDevice online status: {is_online}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_load_average(device_manager):
    board = device_manager.get_device_by_type(CPE)

    load = board.sw.get_load_avg()

    assert isinstance(load, float), "Load average should be float"
    assert load >= 0, "Load average should be non-negative"
    print(f"\nSystem load average (1-minute): {load}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_memory_utilization(device_manager):
    board = device_manager.get_device_by_type(CPE)

    memory = board.sw.get_memory_utilization()

    assert isinstance(memory, dict), "Memory info should be dictionary"
    assert "total" in memory, "Should have total memory"
    assert "free" in memory, "Should have free memory"

    print(f"\nMemory Utilization:")
    print(f"  Total: {memory.get('total', 0)} KB")
    print(f"  Used:  {memory.get('used', 0)} KB")
    print(f"  Free:  {memory.get('free', 0)} KB")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_device_date(device_manager):
    board = device_manager.get_device_by_type(CPE)

    date_str = board.sw.get_date()

    assert date_str is not None, "Date string should not be None"
    assert len(date_str) > 0, "Date string should not be empty"
    print(f"\nDevice date/time: {date_str}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_device_properties(device_manager):
    board = device_manager.get_device_by_type(CPE)

    print("\nDevice Properties:")
    print(f"  E-Router interface: {board.sw.erouter_iface}")
    print(f"  LAN interface:      {board.sw.lan_iface}")
    print(f"  Guest interface:    {board.sw.guest_iface}")
    print(f"  CPE ID:             {board.sw.cpe_id}")
    print(f"  TR-69 CPE ID:       {board.sw.tr69_cpe_id}")
    print(f"  Production mode:    {board.sw.is_production()}")
