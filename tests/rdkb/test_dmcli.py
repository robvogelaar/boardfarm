"""Tests for DMCLI (Data Model CLI) basic operations on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_dmcli_get_parameter_value(device_manager):
    board = device_manager.get_device_by_type(CPE)

    result = board.sw.dmcli.GPV("Device.DeviceInfo.ModelName")

    print(f"\nDevice Model: {result.rval}")
    assert result.rval, "Should return model name"


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_dmcli_set_and_get_value(device_manager):
    board = device_manager.get_device_by_type(CPE)

    param = "Device.DeviceInfo.X_RDKCENTRAL-COM_DeviceFingerPrint.Enable"

    original = board.sw.dmcli.GPV(param)
    print(f"\nOriginal value: {original.rval}")

    new_value = "false" if original.rval == "true" else "true"
    board.sw.dmcli.SPV(param, new_value, "bool")
    print(f"Set to: {new_value}")

    current = board.sw.dmcli.GPV(param)
    print(f"Current value: {current.rval}")

    board.sw.dmcli.SPV(param, original.rval, "bool")
    print(f"Restored to: {original.rval}")
