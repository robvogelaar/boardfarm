"""Tests for system information primitives on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_uptime(device_manager):
    """Test getting device uptime in seconds.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    uptime = board.sw.get_seconds_uptime()

    assert isinstance(uptime, float), "Uptime should be a float"
    assert uptime > 0, "Uptime should be positive"
    print(f"\nDevice uptime: {uptime:.2f} seconds ({uptime/3600:.2f} hours)")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_device_online_status(device_manager):
    """Test checking if device is online.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    is_online = board.sw.is_online()

    assert isinstance(is_online, bool), "Online status should be boolean"
    print(f"\nDevice online status: {is_online}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_load_average(device_manager):
    """Test getting system load average.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    load_avg = board.sw.get_load_avg()

    assert isinstance(load_avg, float), "Load average should be a float"
    assert load_avg >= 0, "Load average should be non-negative"
    print(f"\nSystem load average (1 min): {load_avg}")

    # Warn if load is high
    if load_avg > 2.0:
        print(f"WARNING: High load average detected: {load_avg}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_memory_utilization(device_manager):
    """Test getting memory utilization.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    memory = board.sw.get_memory_utilization()

    # Verify expected keys exist
    expected_keys = ["total", "used", "free", "shared", "cache", "available"]
    for key in expected_keys:
        assert key in memory, f"Memory dict should contain '{key}' key"
        assert isinstance(memory[key], int), f"Memory['{key}'] should be an integer"

    # Verify memory values are reasonable
    assert memory["total"] > 0, "Total memory should be positive"
    assert memory["used"] >= 0, "Used memory should be non-negative"
    assert memory["free"] >= 0, "Free memory should be non-negative"
    assert memory["used"] + memory["free"] <= memory["total"] * 1.1, \
        "Used + Free should be approximately equal to total"

    # Calculate and display usage percentage
    usage_percent = (memory["used"] / memory["total"]) * 100
    print(f"\nMemory Utilization:")
    print(f"  Total: {memory['total']} MB")
    print(f"  Used: {memory['used']} MB ({usage_percent:.1f}%)")
    print(f"  Free: {memory['free']} MB")
    print(f"  Available: {memory['available']} MB")
    print(f"  Cache: {memory['cache']} MB")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_software_version(device_manager):
    """Test getting software version.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    version = board.sw.version

    assert isinstance(version, str), "Version should be a string"
    assert len(version) > 0, "Version should not be empty"
    print(f"\nSoftware Version: {version}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_device_date(device_manager):
    """Test getting device date and time.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    date = board.sw.get_date()

    if date is not None:
        assert isinstance(date, str), "Date should be a string"
        print(f"\nDevice Date/Time: {date}")
    else:
        print("\nWARNING: Could not retrieve device date")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_device_properties(device_manager):
    """Test accessing various device properties.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Test interface names
    erouter_iface = board.sw.erouter_iface
    lan_iface = board.sw.lan_iface
    guest_iface = board.sw.guest_iface

    assert isinstance(erouter_iface, str), "Erouter interface should be a string"
    assert isinstance(lan_iface, str), "LAN interface should be a string"
    assert isinstance(guest_iface, str), "Guest interface should be a string"

    print(f"\nDevice Interface Names:")
    print(f"  E-Router: {erouter_iface}")
    print(f"  LAN: {lan_iface}")
    print(f"  Guest: {guest_iface}")

    # Test CPE ID
    cpe_id = board.sw.cpe_id
    tr69_cpe_id = board.sw.tr69_cpe_id

    assert isinstance(cpe_id, str), "CPE ID should be a string"
    assert isinstance(tr69_cpe_id, str), "TR-069 CPE ID should be a string"

    print(f"\nDevice Identifiers:")
    print(f"  CPE ID: {cpe_id}")
    print(f"  TR-069 CPE ID: {tr69_cpe_id}")

    # Test production status
    is_production = board.sw.is_production()

    assert isinstance(is_production, bool), "Production status should be boolean"
    print(f"  Production Mode: {is_production}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_hardware_information(device_manager):
    """Test getting hardware information.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get MAC address
    mac = board.hw.mac_address
    assert isinstance(mac, str), "MAC address should be a string"
    assert len(mac) > 0, "MAC address should not be empty"
    print(f"\nHardware Information:")
    print(f"  MAC Address: {mac}")

    # Get serial number
    serial = board.hw.serial_number
    assert isinstance(serial, str), "Serial number should be a string"
    print(f"  Serial Number: {serial}")

    # Get WAN interface
    wan_iface = board.hw.wan_iface
    assert isinstance(wan_iface, str), "WAN interface should be a string"
    print(f"  WAN Interface: {wan_iface}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_json_values(device_manager):
    """Test getting CPE-specific JSON values (UCI output).

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    json_values = board.sw.json_values

    assert isinstance(json_values, dict), "JSON values should be a dictionary"
    print(f"\nRetrieved {len(json_values)} UCI configuration values")

    # Display sample values (first 5)
    sample_count = min(5, len(json_values))
    if sample_count > 0:
        print("\nSample UCI values:")
        for i, (key, value) in enumerate(list(json_values.items())[:sample_count]):
            print(f"  {key} = {value}")
