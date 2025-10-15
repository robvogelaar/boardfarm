"""Tests for Kasa Smart Plug power control.

This test suite verifies the KasaPDU implementation can control
Kasa/TP-Link smart plugs for power management.

Test plugs:
- Mv1: 192.168.2.101 (HS103)
- Mv2: 192.168.2.102 (HS103)
- Mv3: 192.168.2.103 (HS103)
"""

import time

import pytest

from boardfarm3.devices.power.kasa import KasaPDU
from boardfarm3.lib.power import get_pdu
from boardfarm3.templates.cpe import CPE


# Define power devices to test
POWER_DEVICES = [
    ("Mv1", "192.168.2.101"),
    ("Mv2", "192.168.2.102"),
    ("Mv3", "192.168.2.103"),
]


@pytest.mark.parametrize("plug_name,ip_address", POWER_DEVICES)
def test_power_on_off_cycle(plug_name, ip_address):
    """Test simple ON/OFF cycle on each discovered power device.

    This test performs a basic power control cycle:
    1. Turn OFF the device
    2. Wait 2 seconds
    3. Turn ON the device

    Args:
        plug_name: Name of the plug (e.g., Mv1, Mv2, Mv3)
        ip_address: IP address of the Kasa smart plug
    """
    print(f"\n=== Testing {plug_name} ({ip_address}) ===")
    plug = KasaPDU(ip_address)

    # Turn OFF
    print(f"{plug_name}: Turning OFF...")
    result = plug.power_off()
    assert result is True, f"Failed to turn OFF {plug_name}"
    print(f"✓ {plug_name} turned OFF")

    # Wait
    time.sleep(2)

    # Turn ON
    print(f"{plug_name}: Turning ON...")
    result = plug.power_on()
    assert result is True, f"Failed to turn ON {plug_name}"
    print(f"✓ {plug_name} turned ON")

    print(f"✓ {plug_name} ON/OFF cycle completed successfully")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_power_cycle_from_config(device_manager):
    """Test power cycle using the powerport from device configuration.

    This test verifies that the PDU configured in the inventory file
    (via the 'powerport' field) can be properly controlled using the
    get_pdu() function and the power cycle operation.

    This test requires a board configuration with a powerport specified.
    """
    board = device_manager.get_device_by_type(CPE)
    powerport = board.hw.config.get("powerport")

    if not powerport:
        pytest.skip("No powerport configured for this device")

    print(f"\n=== Testing powerport from config: {powerport} ===")

    # Get the PDU using the power module's get_pdu function
    pdu = get_pdu(powerport)

    # Verify it's a KasaPDU
    assert isinstance(pdu, KasaPDU), f"Expected KasaPDU, got {type(pdu)}"
    print("✓ PDU retrieved from config is a KasaPDU")

    # Test power cycle
    print("Performing power cycle...")
    result = pdu.power_cycle()
    assert result is True, "Power cycle should succeed"
    print("✓ Power cycle completed successfully")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
