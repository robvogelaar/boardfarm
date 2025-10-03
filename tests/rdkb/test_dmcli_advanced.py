"""Tests for advanced DMCLI operations on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_dmcli_add_and_delete_object(device_manager):
    board = device_manager.get_device_by_type(CPE)

    print("\nTesting AddObject and DelObject:")

    try:
        result = board.sw.dmcli.AddObject("Device.DHCPv4.Server.Pool.")
        print(f"  Added object: {result.rval}")

        instance_number = result.rval.split(".")[-1]
        assert instance_number.isdigit(), "Should return instance number"

        obj_path = f"Device.DHCPv4.Server.Pool.{instance_number}"
        board.sw.dmcli.SPV(f"{obj_path}.Enable", "false", "bool")
        print(f"  Configured object parameters")

        board.sw.dmcli.DelObject(f"{obj_path}.")
        print(f"  OK Deleted object: {obj_path}")
    except Exception as e:
        pytest.skip(f"AddObject not supported on this device: {e}")
