"""Tests for SNMP operations on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_snmp_methods_exist(device_manager):
    board = device_manager.get_device_by_type(CPE)

    try:
        assert hasattr(board.sw, 'snmp'), "SNMP component should exist"
        assert hasattr(board.sw.snmp, 'snmpget'), "snmpget method should exist"
        assert hasattr(board.sw.snmp, 'snmpset'), "snmpset method should exist"
        assert hasattr(board.sw.snmp, 'snmpwalk'), "snmpwalk method should exist"
        assert hasattr(board.sw.snmp, 'snmpbulkget'), "snmpbulkget method should exist"

        print("\nOK SNMP methods available:")
        print("  - snmpget(oid)")
        print("  - snmpset(oid, value, type)")
        print("  - snmpwalk(oid)")
        print("  - snmpbulkget(oid)")
    except AttributeError:
        pytest.skip("SNMP not available on this device")
