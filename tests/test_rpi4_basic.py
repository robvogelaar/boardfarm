"""Basic tests for RPI4 RDKB board."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.fixture(scope="session", autouse=True)
def setup_terminal_width(device_manager, request):
    """Set terminal width when using --skip-boot to prevent command wrapping.

    :param device_manager: Device manager fixture
    :param request: pytest request fixture
    """
    if request.config.getoption("--skip-boot", default=False):
        board = device_manager.get_device_by_type(CPE)
        console = board.hw.get_console("console")
        # Set wide terminal to prevent line wrapping in command echo
        # Use sendline + expect prompt to avoid the execute_command wrapping issue
        console.sendline("stty columns 200; export TERM=xterm")
        console.expect(console._shell_prompt, timeout=5)


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_board_accessible(device_manager):
    """Test that the board is accessible and responding.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Execute a simple command to verify board is accessible
    console = board.hw.get_console("console")
    output = console.execute_command("uname -a")

    assert "Linux" in output, "Board should be running Linux"
    print(f"\nBoard info: {output}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_board_uptime(device_manager):
    """Test board uptime and system status.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Check system uptime
    console = board.hw.get_console("console")
    output = console.execute_command("uptime")

    assert "load average" in output, "Uptime command should show load average"
    print(f"\nBoard uptime: {output}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_board_memory(device_manager):
    """Test board memory information.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Check memory info
    console = board.hw.get_console("console")
    output = console.execute_command("free -m")

    assert "Mem:" in output, "Should show memory information"
    print(f"\nBoard memory:\n{output}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_board_processes(device_manager):
    """Test board process list.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # List running processes
    console = board.hw.get_console("console")
    output = console.execute_command("ps aux | head -n 20")

    assert "PID" in output or "root" in output, "Should show process list"
    print(f"\nBoard processes (first 20):\n{output}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_dmcli_device_info(device_manager):
    """Test dmcli command to get device information.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get device info using dmcli
    result = board.sw.dmcli.GPV("Device.DeviceInfo.ModelName")

    assert result.status.startswith("Execution succeed."), "dmcli command should succeed"
    assert result.rval, "ModelName should have a value"
    print(f"\nDevice Model Name: {result.rval}")
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

    assert result.status.startswith("Execution succeed."), "dmcli command should succeed"
    assert result.rval, "SoftwareVersion should have a value"
    print(f"\nSoftware Version: {result.rval}")
    print(f"Value Type: {result.rtype}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_dmcli_wan_status(device_manager):
    """Test dmcli command to get WAN connection status.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get WAN connection status using dmcli
    result = board.sw.dmcli.GPV("Device.DeviceInfo.X_COMCAST-COM_WAN_IP")

    assert result.status.startswith("Execution succeed."), "dmcli command should succeed"
    print(f"\nWAN IP Address: {result.rval}")
    print(f"Value Type: {result.rtype}")
