"""Tests for network interface primitives on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_interface_ipv4(device_manager):
    board = device_manager.get_device_by_type(CPE)

    ipv4 = board.sw.get_interface_ipv4addr("erouter0")

    print(f"\nErouter0 IPv4 Address: {ipv4}")
    assert ipv4, "Should have IPv4 address"


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_interface_ipv6(device_manager):
    board = device_manager.get_device_by_type(CPE)

    try:
        ipv6 = board.sw.get_interface_ipv6addr("erouter0")
        print(f"\nErouter0 IPv6 Address: {ipv6}")
    except Exception as e:
        pytest.skip(f"IPv6 not available: {e}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_link_local_ipv6(device_manager):
    board = device_manager.get_device_by_type(CPE)

    ipv6_ll = board.sw.get_interface_link_local_ipv6_addr("erouter0")

    print(f"\nErouter0 Link-Local IPv6: {ipv6_ll}")
    assert ipv6_ll, "Should have link-local IPv6"


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_interface_netmask(device_manager):
    board = device_manager.get_device_by_type(CPE)

    netmask = board.sw.get_interface_ipv4_netmask("brlan0")

    print(f"\nbrlan0 Netmask: {netmask}")
    assert netmask, "Should have netmask"


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_interface_mac(device_manager):
    board = device_manager.get_device_by_type(CPE)

    mac_erouter = board.sw.get_interface_mac_addr("erouter0")
    mac_brlan = board.sw.get_interface_mac_addr("brlan0")

    print(f"\nerouter0 MAC: {mac_erouter}")
    print(f"brlan0 MAC: {mac_brlan}")
    assert mac_erouter, "Should have MAC address"


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_interface_link_status(device_manager):
    board = device_manager.get_device_by_type(CPE)

    erouter_up = board.sw.is_link_up("erouter0")
    brlan_up = board.sw.is_link_up("brlan0")

    print(f"\nInterface Link Status:")
    print(f"  erouter0: {'UP' if erouter_up else 'DOWN'}")
    print(f"  brlan0: {'UP' if brlan_up else 'DOWN'}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_lan_gateway_addresses(device_manager):
    board = device_manager.get_device_by_type(CPE)

    print("\nLAN Gateway Addresses:")
    print(f"  IPv4: {board.sw.lan_gateway_ipv4}")
    print(f"  IPv6: {board.sw.lan_gateway_ipv6}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_mtu_size(device_manager):
    board = device_manager.get_device_by_type(CPE)

    mtu = board.sw.get_interface_mtu_size("erouter0")

    print(f"\nInterface MTU Sizes:")
    print(f"  erouter0: {mtu} bytes")
    assert mtu > 0, "MTU should be positive"
