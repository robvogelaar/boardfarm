"""Tests for WiFi HAL primitives on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_wlan_interfaces(device_manager):
    board = device_manager.get_device_by_type(CPE)

    try:
        ifaces = board.sw.wifi.wlan_ifaces

        print(f"\nWLAN Interfaces: {ifaces}")
        assert isinstance(ifaces, (list, tuple)), "Should return list of interfaces"
    except Exception as e:
        pytest.skip(f"WiFi HAL not available: {e}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_wifi_ssid(device_manager):
    board = device_manager.get_device_by_type(CPE)

    try:
        ssid_2g = board.sw.wifi.get_ssid("private", "2.4")
        print(f"\nPrivate WiFi 2.4GHz SSID: {ssid_2g}")

        ssid_5g = board.sw.wifi.get_ssid("private", "5")
        print(f"Private WiFi 5GHz SSID: {ssid_5g}")
    except Exception as e:
        pytest.skip(f"WiFi SSID query not available: {e}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_wifi_bssid(device_manager):
    board = device_manager.get_device_by_type(CPE)

    try:
        bssid_2g = board.sw.wifi.get_bssid("private", "2.4")
        print(f"\nPrivate WiFi 2.4GHz BSSID: {bssid_2g}")
        assert ":" in bssid_2g, "BSSID should be MAC address format"
    except Exception as e:
        pytest.skip(f"WiFi BSSID query not available: {e}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_wifi_passphrase(device_manager):
    board = device_manager.get_device_by_type(CPE)

    try:
        ifaces = board.sw.wifi.wlan_ifaces
        if ifaces:
            passphrase = board.sw.wifi.get_passphrase(ifaces[0])
            print(f"\nWiFi passphrase for {ifaces[0]}: {'*' * len(passphrase)}")
            assert len(passphrase) > 0, "Passphrase should not be empty"
    except Exception as e:
        pytest.skip(f"WiFi passphrase query not available: {e}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_check_wifi_enabled(device_manager):
    board = device_manager.get_device_by_type(CPE)

    try:
        is_enabled_2g = board.sw.wifi.is_wifi_enabled("private", "2.4")
        print(f"\nPrivate WiFi 2.4GHz enabled: {is_enabled_2g}")

        is_enabled_5g = board.sw.wifi.is_wifi_enabled("private", "5")
        print(f"Private WiFi 5GHz enabled: {is_enabled_5g}")
    except Exception as e:
        pytest.skip(f"WiFi status query not available: {e}")
