"""Tests for RDKB dmcli commands."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_dmcli_device_model(device_manager):
    """Test dmcli command to get device model name.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get device model name using dmcli
    result = board.sw.dmcli.GPV("Device.DeviceInfo.ModelName")

    assert "Execution succeed" in result.status, "dmcli command should succeed"
    assert result.rval, "ModelName should have a value"
    print(f"\nDevice Model Name: {result.rval}")
    print(f"Value Type: {result.rtype}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_dmcli_manufacturer(device_manager):
    """Test dmcli command to get device manufacturer.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get manufacturer using dmcli
    result = board.sw.dmcli.GPV("Device.DeviceInfo.Manufacturer")

    assert "Execution succeed" in result.status, "dmcli command should succeed"
    assert result.rval, "Manufacturer should have a value"
    print(f"\nManufacturer: {result.rval}")
    print(f"Value Type: {result.rtype}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_dmcli_software_version(device_manager):
    """Test dmcli command to get software version.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get software version using dmcli
    result = board.sw.dmcli.GPV("Device.DeviceInfo.SoftwareVersion")

    assert "Execution succeed" in result.status, "dmcli command should succeed"
    assert result.rval, "SoftwareVersion should have a value"
    print(f"\nSoftware Version: {result.rval}")
    print(f"Value Type: {result.rtype}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_dmcli_hardware_version(device_manager):
    """Test dmcli command to get hardware version.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get hardware version using dmcli
    result = board.sw.dmcli.GPV("Device.DeviceInfo.HardwareVersion")

    assert "Execution succeed" in result.status, "dmcli command should succeed"
    assert result.rval, "HardwareVersion should have a value"
    print(f"\nHardware Version: {result.rval}")
    print(f"Value Type: {result.rtype}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_dmcli_serial_number(device_manager):
    """Test dmcli command to get serial number.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get serial number using dmcli
    result = board.sw.dmcli.GPV("Device.DeviceInfo.SerialNumber")

    assert "Execution succeed" in result.status, "dmcli command should succeed"
    assert result.rval, "SerialNumber should have a value"
    print(f"\nSerial Number: {result.rval}")
    print(f"Value Type: {result.rtype}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_dmcli_uptime(device_manager):
    """Test dmcli command to get device uptime.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get uptime using dmcli
    result = board.sw.dmcli.GPV("Device.DeviceInfo.UpTime")

    assert "Execution succeed" in result.status, "dmcli command should succeed"
    assert result.rval, "UpTime should have a value"
    # Convert to hours for readability
    uptime_seconds = int(result.rval)
    uptime_hours = uptime_seconds / 3600
    print(f"\nDevice Uptime: {uptime_seconds} seconds ({uptime_hours:.2f} hours)")
    print(f"Value Type: {result.rtype}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_dmcli_wifi_ssid(device_manager):
    """Test dmcli command to get WiFi SSID.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get WiFi SSID using dmcli (2.4GHz)
    result = board.sw.dmcli.GPV("Device.WiFi.SSID.1.SSID")

    assert "Execution succeed" in result.status, "dmcli command should succeed"
    print(f"\nWiFi SSID (2.4GHz): {result.rval}")
    print(f"Value Type: {result.rtype}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_dmcli_set_and_get_value(device_manager):
    """Test dmcli SPV and GPV commands to set and get a value.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # First, get the current value
    original_result = board.sw.dmcli.GPV("Device.DeviceInfo.X_RDKCENTRAL-COM_xOpsDeviceMgmt.Logging.xOpsDMUploadLogsNow")
    print(f"\nOriginal value: {original_result.rval}")

    # Set a new value
    set_result = board.sw.dmcli.SPV(
        "Device.DeviceInfo.X_RDKCENTRAL-COM_xOpsDeviceMgmt.Logging.xOpsDMUploadLogsNow",
        "false",
        "bool"
    )

    assert "Execution succeed" in set_result.status, "dmcli SPV command should succeed"
    print(f"Set operation status: {set_result.status}")

    # Verify the value was set
    new_result = board.sw.dmcli.GPV("Device.DeviceInfo.X_RDKCENTRAL-COM_xOpsDeviceMgmt.Logging.xOpsDMUploadLogsNow")
    print(f"New value: {new_result.rval}")
