"""Tests for file transfer primitives (SCP/TFTP) on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_scp_method_exists(device_manager):
    board = device_manager.get_device_by_type(CPE)

    assert hasattr(board.sw.nw_utility, 'scp'), "SCP method should exist"
    print("\nOK SCP method available")
    print("  SCP requires: ip, port, user, pwd, source_path, dest_path, action")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_tftp_method_exists(device_manager):
    board = device_manager.get_device_by_type(CPE)

    assert hasattr(board.sw.nw_utility, 'tftp'), "TFTP method should exist"
    print("\nOK TFTP method available")
    print("  TFTP requires: ip, filename, action")
