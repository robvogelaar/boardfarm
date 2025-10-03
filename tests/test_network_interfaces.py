"""Tests for network interface primitives on RDKB devices."""

import pytest
from ipaddress import IPv4Address, IPv4Network, IPv6Address

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_interface_ipv4(device_manager):
    """Test getting IPv4 address of erouter interface.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    try:
        ipv4 = board.sw.get_interface_ipv4addr("erouter0")
        assert isinstance(ipv4, str), "IPv4 address should be a string"
        assert len(ipv4) > 0, "IPv4 address should not be empty"

        # Verify it's a valid IPv4 address
        IPv4Address(ipv4)
        print(f"\nErouter0 IPv4 Address: {ipv4}")
    except ValueError as e:
        print(f"\nWARNING: Could not get IPv4 address for erouter0: {e}")
        pytest.skip("erouter0 does not have an IPv4 address")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_interface_ipv6(device_manager):
    """Test getting IPv6 address of erouter interface.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    try:
        ipv6 = board.sw.get_interface_ipv6addr("erouter0")
        assert isinstance(ipv6, str), "IPv6 address should be a string"
        assert len(ipv6) > 0, "IPv6 address should not be empty"

        # Verify it's a valid IPv6 address
        IPv6Address(ipv6.split("/")[0])
        print(f"\nErouter0 IPv6 Address: {ipv6}")
    except ValueError as e:
        print(f"\nWARNING: Could not get IPv6 address for erouter0: {e}")
        pytest.skip("erouter0 does not have an IPv6 address")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_link_local_ipv6(device_manager):
    """Test getting link-local IPv6 address.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    try:
        link_local = board.sw.get_interface_link_local_ipv6_addr("erouter0")
        assert isinstance(link_local, str), "Link-local IPv6 should be a string"

        # Verify it's a valid link-local address
        ipv6_addr = IPv6Address(link_local.split("/")[0])
        assert ipv6_addr.is_link_local, "Address should be link-local"
        print(f"\nErouter0 Link-Local IPv6: {link_local}")
    except ValueError as e:
        print(f"\nWARNING: Could not get link-local IPv6 for erouter0: {e}")
        pytest.skip("erouter0 does not have a link-local IPv6 address")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_interface_netmask(device_manager):
    """Test getting interface netmask.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    netmask = board.sw.get_interface_ipv4_netmask("brlan0")

    assert isinstance(netmask, IPv4Address), "Netmask should be IPv4Address type"
    print(f"\nbrlan0 Netmask: {netmask}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_interface_mac(device_manager):
    """Test getting interface MAC address.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Test erouter0 MAC
    erouter_mac = board.sw.get_interface_mac_addr("erouter0")
    assert isinstance(erouter_mac, str), "MAC address should be a string"
    assert ":" in erouter_mac, "MAC address should contain colons"
    print(f"\nerouter0 MAC: {erouter_mac}")

    # Test brlan0 MAC
    lan_mac = board.sw.get_interface_mac_addr("brlan0")
    assert isinstance(lan_mac, str), "MAC address should be a string"
    print(f"brlan0 MAC: {lan_mac}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_interface_link_status(device_manager):
    """Test checking if interface link is up.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Check erouter0
    erouter_up = board.sw.is_link_up("erouter0")
    assert isinstance(erouter_up, bool), "Link status should be boolean"
    print(f"\nInterface Link Status:")
    print(f"  erouter0: {'UP' if erouter_up else 'DOWN'}")

    # Check brlan0
    lan_up = board.sw.is_link_up("brlan0")
    print(f"  brlan0: {'UP' if lan_up else 'DOWN'}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_lan_gateway_addresses(device_manager):
    """Test getting LAN gateway addresses.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get LAN gateway IPv4
    lan_gw_ipv4 = board.sw.lan_gateway_ipv4
    assert isinstance(lan_gw_ipv4, IPv4Address), "LAN gateway IPv4 should be IPv4Address type"
    print(f"\nLAN Gateway Addresses:")
    print(f"  IPv4: {lan_gw_ipv4}")

    # Get LAN gateway IPv6
    try:
        lan_gw_ipv6 = board.sw.lan_gateway_ipv6
        assert isinstance(lan_gw_ipv6, IPv6Address), "LAN gateway IPv6 should be IPv6Address type"
        print(f"  IPv6: {lan_gw_ipv6}")
    except ValueError as e:
        print(f"  IPv6: Not available ({e})")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_lan_network_ipv4(device_manager):
    """Test getting LAN IPv4 network.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    lan_network = board.sw.lan_network_ipv4
    assert isinstance(lan_network, IPv4Network), "LAN network should be IPv4Network type"

    print(f"\nLAN IPv4 Network: {lan_network}")
    print(f"  Network Address: {lan_network.network_address}")
    print(f"  Netmask: {lan_network.netmask}")
    print(f"  Broadcast: {lan_network.broadcast_address}")
    print(f"  Num Addresses: {lan_network.num_addresses}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_mtu_size(device_manager):
    """Test getting interface MTU size.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get MTU for erouter0
    mtu = board.sw.get_interface_mtu_size("erouter0")
    assert isinstance(mtu, int), "MTU should be an integer"
    assert mtu > 0, "MTU should be positive"
    assert mtu <= 9000, "MTU should be reasonable (<=9000)"

    print(f"\nInterface MTU Sizes:")
    print(f"  erouter0: {mtu} bytes")

    # Common MTU values: 1500 (Ethernet), 1492 (PPPoE), 9000 (Jumbo frames)
    if mtu == 1500:
        print("  (Standard Ethernet MTU)")
    elif mtu == 1492:
        print("  (PPPoE MTU)")
    elif mtu == 9000:
        print("  (Jumbo frame MTU)")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_all_interfaces_overview(device_manager):
    """Test getting overview of all main interfaces.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    interfaces = ["erouter0", "brlan0"]

    print("\nInterface Overview:")
    print("-" * 80)

    for iface in interfaces:
        print(f"\n{iface}:")

        # Get MAC
        try:
            mac = board.sw.get_interface_mac_addr(iface)
            print(f"  MAC: {mac}")
        except Exception as e:
            print(f"  MAC: Error - {e}")

        # Get IPv4
        try:
            ipv4 = board.sw.get_interface_ipv4addr(iface)
            print(f"  IPv4: {ipv4}")
        except ValueError:
            print(f"  IPv4: Not assigned")

        # Get link status
        try:
            is_up = board.sw.is_link_up(iface)
            print(f"  Status: {'UP' if is_up else 'DOWN'}")
        except Exception as e:
            print(f"  Status: Error - {e}")

        # Get MTU
        try:
            mtu = board.sw.get_interface_mtu_size(iface)
            print(f"  MTU: {mtu}")
        except Exception as e:
            print(f"  MTU: Error - {e}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_interface_via_console(device_manager):
    """Test getting interface information via console commands.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    # Get interface list
    output = console.execute_command("ip addr show")
    assert "erouter0" in output or "brlan0" in output, \
        "Should see at least one main interface"

    print("\nInterface Information (via ip addr):")
    # Print first 20 lines
    lines = output.split("\n")[:20]
    for line in lines:
        if line.strip():
            print(f"  {line}")
