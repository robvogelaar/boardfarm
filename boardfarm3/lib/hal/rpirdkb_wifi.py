"""RPiRDKB WiFi HAL implementation using DMCLI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from boardfarm3.lib.hal.cpe_wifi import WiFiHal

if TYPE_CHECKING:
    from boardfarm3.devices.rpirdkb_cpe import RPiRDKBSW


class RPiRDKBWiFi(WiFiHal):
    """WiFi HAL implementation for RPiRDKB using DMCLI commands."""

    def __init__(self, sw: RPiRDKBSW) -> None:
        """Initialize WiFi HAL.

        :param sw: Software component reference
        :type sw: RPiRDKBSW
        """
        self.sw = sw

    def _get_wifi_index(self, network: str, band: str) -> int:
        """Map network type and band to WiFi radio index.

        :param network: network type (private/guest/community)
        :type network: str
        :param band: wifi band (5/2.4 GHz)
        :type band: str
        :return: WiFi radio index
        :rtype: int
        """
        if band == "2.4":
            if network == "private":
                return 1
            elif network == "guest":
                return 2
        elif band == "5":
            if network == "private":
                return 3
            elif network == "guest":
                return 4
        return 1

    @property
    def wlan_ifaces(self) -> dict[str, dict[str, str]]:
        """Get all the wlan interfaces on board.

        :return: interfaces e.g. private/guest/community
        :rtype: dict[str, dict[str, str]]
        """
        try:
            result = self.sw.dmcli.GPV("Device.WiFi.Radio.")
            ifaces = {}
            for line in result.output.split("\n"):
                if "wlan" in line.lower():
                    parts = line.split()
                    if len(parts) >= 2:
                        ifaces[parts[0]] = {"status": "up"}
            return ifaces
        except Exception:
            return {}

    def get_ssid(self, network: str, band: str) -> str | None:
        """Get the wifi ssid for the wlan client with specific network and band.

        :param network: network type(private/guest/community)
        :type network: str
        :param band: wifi band(5/2.4 GHz)
        :type band: str
        :return: SSID of the WiFi for a given network type and band
        :rtype: Optional[str]
        """
        index = self._get_wifi_index(network, band)
        try:
            result = self.sw.dmcli.GPV(f"Device.WiFi.SSID.{index}.SSID")
            if result.rval:
                return result.rval
        except Exception:
            pass
        return None

    def get_bssid(self, network: str, band: str) -> str | None:
        """Get the wifi Basic Service Set Identifier.

        :param network: network type(private/guest/community)
        :type network: str
        :param band: wifi band(5/2.4 GHz)
        :type band: str
        :return: MAC physical address of the access point
        :rtype: Optional[str]
        """
        index = self._get_wifi_index(network, band)
        try:
            result = self.sw.dmcli.GPV(f"Device.WiFi.SSID.{index}.BSSID")
            if result.rval:
                return result.rval
        except Exception:
            pass
        return None

    def get_passphrase(self, iface: str) -> str:
        """Get the passphrase for a network on an interface.

        :param iface: name of the interface
        :type iface: str
        :return: encrypted password for a network
        :rtype: str
        """
        try:
            result = self.sw.dmcli.GPV(f"Device.WiFi.AccessPoint.1.Security.KeyPassphrase")
            if result.rval:
                return result.rval
        except Exception:
            pass
        return ""

    def is_wifi_enabled(self, network_type: str, band: str) -> bool:
        """Check if specific wifi is enabled.

        :param network_type: network type(private/guest/community)
        :type network_type: str
        :param band: wifi band(5/2.4 GHz)
        :type band: str
        :return: True if enabled, False otherwise
        :rtype: bool
        """
        index = self._get_wifi_index(network_type, band)
        try:
            result = self.sw.dmcli.GPV(f"Device.WiFi.SSID.{index}.Enable")
            if result.rval:
                return result.rval.lower() == "true"
        except Exception:
            pass
        return False

    def enable_wifi(self, network: str, band: str) -> tuple[str, str, str]:
        """Use Wifi Hal API to enable the wifi if not already enabled.

        :param network: network type(private/guest/community)
        :type network: str
        :param band: wifi band(5/2.4 GHz)
        :type band: str
        :return: tuple of ssid,bssid,passphrase
        :rtype: tuple[str, str, str]
        """
        index = self._get_wifi_index(network, band)
        try:
            self.sw.dmcli.SPV(f"Device.WiFi.SSID.{index}.Enable", "true", "bool")
            ssid = self.get_ssid(network, band) or ""
            bssid = self.get_bssid(network, band) or ""
            passphrase = self.get_passphrase(f"wlan{index}")
            return (ssid, bssid, passphrase)
        except Exception as e:
            raise RuntimeError(f"Failed to enable WiFi: {e}") from e
