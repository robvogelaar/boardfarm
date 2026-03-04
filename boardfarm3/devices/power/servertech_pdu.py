"""Server Technology Switched PDU module."""

import asyncio
import logging

from pysnmp.hlapi import (
    CommunityData,
    ContextData,
    Integer,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    getCmd,
    setCmd,
)

from boardfarm3.templates.pdu import PDU

_LOGGER = logging.getLogger(__name__)

_DEFAULT_COMMUNITY = "private"
_URI_PARTS_WITH_COMMUNITY = 3

# sysDescr OID (SNMPv2-MIB)
_SYS_DESCR_OID = ".1.3.6.1.2.1.1.1.0"

# Sentry3-MIB: outletControlAction (CDU series, firmware v7.x)
_SENTRY3_CONTROL_OID = ".1.3.6.1.4.1.1718.3.2.3.1.11"

# Sentry4-MIB: st4OutletControlAction (PRO1/PRO2 series, firmware v8.x)
_SENTRY4_CONTROL_OID = ".1.3.6.1.4.1.1718.4.1.8.5.1.2"


class ServerTechPDU(PDU):
    """Class contains methods to interact with Server Technology PDU.

    Auto-detects Sentry3-MIB (CDU) vs Sentry4-MIB (PRO1/PRO2) by reading
    sysDescr via SNMP. Compatible with both firmware generations.
    """

    def __init__(self, uri: str) -> None:
        """Initialize Server Technology PDU.

        The PDU is driven by SNMP commands. The correct MIB (Sentry3 or Sentry4)
        is auto-detected on first use by reading sysDescr.

        :param uri: uri as "ip;outlet" or "ip;outlet;community"
        :type uri: str
        :raises ValueError: if an http port is provided
        """
        parts = uri.split(";")
        self._pdu_ip = parts[0].strip()
        outlet_part = parts[1].strip()
        self._community = (
            parts[2].strip()
            if len(parts) >= _URI_PARTS_WITH_COMMUNITY
            else _DEFAULT_COMMUNITY
        )
        if ":" in self._pdu_ip:
            msg = f"ServerTechPDU uses snmp, no port in {uri} allowed"
            raise ValueError(msg)
        if "." in outlet_part:
            self._outlet_index = outlet_part
        else:
            self._outlet_index = f"1.1.{outlet_part}"
        self._control_oid: str | None = None

    @staticmethod
    def _ensure_event_loop() -> None:
        """Ensure an asyncio event loop exists for the current thread.

        Python 3.12+ no longer auto-creates an event loop on get_event_loop().
        pysnmp's synchronous helpers rely on get_event_loop(), so we must
        ensure one is set before calling them.
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            try:
                asyncio.get_event_loop()
            except RuntimeError:
                asyncio.set_event_loop(asyncio.new_event_loop())

    def _detect_mib(self) -> str:
        """Detect Sentry3 vs Sentry4 MIB by reading sysDescr.

        'Sentry Switched CDU' -> Sentry3-MIB (CDU series)
        'Sentry Switched PDU' -> Sentry4-MIB (PRO1/PRO2 series)

        :returns: the base control OID for this device
        :raises ConnectionError: if sysDescr cannot be read
        """
        self._ensure_event_loop()
        (error_indication, error_status, _, var_binds) = getCmd(
            SnmpEngine(),
            CommunityData(self._community),
            UdpTransportTarget((self._pdu_ip, 161), timeout=10, retries=3),
            ContextData(),
            ObjectType(ObjectIdentity(_SYS_DESCR_OID)),
        )
        if error_indication or error_status:
            msg = f"Failed to read sysDescr from {self._pdu_ip}"
            if error_indication:
                msg += f", {error_indication}"
            raise ConnectionError(msg)

        sys_descr = str(var_binds[0][1])
        _LOGGER.info("ServerTechPDU sysDescr: %s", sys_descr)

        if "CDU" in sys_descr:
            _LOGGER.info("Detected Sentry3-MIB (CDU series)")
            return _SENTRY3_CONTROL_OID

        _LOGGER.info("Detected Sentry4-MIB (PRO1/PRO2 series)")
        return _SENTRY4_CONTROL_OID

    def _get_control_oid(self) -> str:
        """Get the control OID, detecting MIB version on first call.

        :returns: the base control OID for this device
        """
        if self._control_oid is None:
            self._control_oid = self._detect_mib()
        return self._control_oid

    def power_off(self) -> bool:
        """Power OFF the given PDU outlet.

        :returns: True on success
        """
        return self._perform_snmpset(2)

    def power_on(self) -> bool:
        """Power ON the given PDU outlet.

        :returns: True on success
        """
        return self._perform_snmpset(1)

    def power_cycle(self) -> bool:
        """Power cycle the given PDU outlet.

        :returns: True on success
        """
        return self._perform_snmpset(3)

    def _perform_snmpset(self, operation_id: int) -> bool:
        """Send snmp set command based on operation ID.

        Auto-detects Sentry3 vs Sentry4 OID on first call.

        :param operation_id: 1 (ON), 2 (OFF), 3 (REBOOT)
        :type operation_id: int
        :returns: True on success
        """
        snmp_status = True
        control_oid = self._get_control_oid()
        oid = f"{control_oid}.{self._outlet_index}"
        self._ensure_event_loop()
        (error_indication, error_status, _, _) = setCmd(
            SnmpEngine(),
            CommunityData(self._community),
            UdpTransportTarget((self._pdu_ip, 161), timeout=10, retries=3),
            ContextData(),
            ObjectType(ObjectIdentity(oid), Integer(operation_id)),
        )
        if error_indication or error_status:
            error_msg = "Snmp command execution has failed"
            if error_indication:
                error_msg += f", {error_indication}"
            if error_status:
                error_msg += f", {error_status.prettyPrint()}"
            _LOGGER.error(error_msg)
            snmp_status = False
        return snmp_status
