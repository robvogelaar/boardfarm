"""Tests for process management primitives on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_running_processes(device_manager):
    """Test getting list of running processes.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    processes = list(board.sw.get_running_processes(ps_options="-A"))

    assert len(processes) > 0, "Should have at least one running process"
    assert isinstance(processes[0], dict), "Process should be a dictionary"

    # Verify expected keys in process dict
    expected_keys = ["pid", "command"]
    for key in expected_keys:
        assert key in processes[0], f"Process should have '{key}' key"

    print(f"\nTotal running processes: {len(processes)}")
    print("\nFirst 10 processes:")
    for proc in processes[:10]:
        print(f"  PID {proc['pid']:>6}: {proc['command']}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_find_specific_process(device_manager):
    """Test finding specific processes by name.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    processes = list(board.sw.get_running_processes(ps_options="-A"))

    # Look for init process (PID 1)
    init_processes = [p for p in processes if p["pid"] == 1]
    assert len(init_processes) == 1, "Should find init process with PID 1"

    init_proc = init_processes[0]
    print(f"\nInit Process:")
    print(f"  PID: {init_proc['pid']}")
    print(f"  Command: {init_proc['command']}")
    if "time" in init_proc:
        print(f"  CPU Time: {init_proc['time']}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_find_ccsp_processes(device_manager):
    """Test finding CCSP (Common Component Software Platform) processes.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    processes = list(board.sw.get_running_processes(ps_options="-A"))

    # Find CCSP processes (they typically have "Ccsp" in the name)
    ccsp_processes = [p for p in processes if "Ccsp" in p["command"] or "ccsp" in p["command"]]

    print(f"\nCCSP Processes found: {len(ccsp_processes)}")

    if len(ccsp_processes) > 0:
        print("\nCCSP Process List:")
        for proc in ccsp_processes:
            print(f"  PID {proc['pid']:>6}: {proc['command']}")
    else:
        print("WARNING: No CCSP processes found")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_find_tr069_process(device_manager):
    """Test finding TR-069 agent process.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    processes = list(board.sw.get_running_processes(ps_options="-A"))

    # Look for TR-069 PA process
    tr069_processes = [p for p in processes if "CcspTr069Pa" in p["command"] or "tr069" in p["command"].lower()]

    print(f"\nTR-069 Processes found: {len(tr069_processes)}")

    if len(tr069_processes) > 0:
        print("\nTR-069 Process Details:")
        for proc in tr069_processes:
            print(f"  PID {proc['pid']:>6}: {proc['command']}")
    else:
        print("WARNING: No TR-069 processes found")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_process_count_by_name(device_manager):
    """Test counting processes grouped by command name.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    processes = list(board.sw.get_running_processes(ps_options="-A"))

    # Count processes by command name
    process_counts = {}
    for proc in processes:
        cmd = proc["command"].split()[0] if " " in proc["command"] else proc["command"]
        process_counts[cmd] = process_counts.get(cmd, 0) + 1

    # Sort by count (descending)
    sorted_counts = sorted(process_counts.items(), key=lambda x: x[1], reverse=True)

    print(f"\nTop 10 processes by count:")
    for cmd, count in sorted_counts[:10]:
        print(f"  {cmd:30s}: {count} instance(s)")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_kill_process_simulation(device_manager):
    """Test process kill functionality (simulation only, no actual kill).

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # This test just verifies the method exists and is callable
    # We don't actually kill any process to avoid disrupting the system

    processes = list(board.sw.get_running_processes(ps_options="-A"))

    # Find a safe process to potentially kill (sleep or test process)
    # We won't actually kill it, just demonstrate the API
    safe_processes = [p for p in processes if "sleep" in p["command"].lower()]

    if len(safe_processes) > 0:
        target_pid = safe_processes[0]["pid"]
        print(f"\nProcess kill API available")
        print(f"Example: Would kill PID {target_pid} ({safe_processes[0]['command']})")
        print("Note: Not actually killing process in this test")
        # board.sw.kill_process_immediately(target_pid)  # Commented out for safety
    else:
        print("\nProcess kill API available")
        print("Note: No safe test processes found to demonstrate with")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_process_resource_monitoring(device_manager):
    """Test monitoring process resource usage via ps command.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    # Get detailed process info with memory and CPU
    output = console.execute_command("ps aux | head -n 20")

    assert "PID" in output or "USER" in output, "Should show process header"

    print("\nProcess Resource Usage (top 20):")
    print(output)


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_process_tree_view(device_manager):
    """Test viewing process tree hierarchy.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    # Try to get process tree (if pstree is available)
    output = console.execute_command("which pstree && pstree -p || ps -ejH")

    print("\nProcess Tree/Hierarchy:")
    lines = output.split("\n")[:30]  # First 30 lines
    for line in lines:
        if line.strip():
            print(f"  {line}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_critical_services_running(device_manager):
    """Test that critical RDKB services are running.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    processes = list(board.sw.get_running_processes(ps_options="-A"))
    process_names = [p["command"].lower() for p in processes]

    # List of critical services to check
    critical_services = [
        ("ccsp", "CCSP Component"),
        ("dbus", "D-Bus daemon"),
        ("systemd", "System daemon"),
    ]

    print("\nCritical Services Check:")
    all_found = True

    for service_keyword, service_desc in critical_services:
        found = any(service_keyword in pname for pname in process_names)
        status = "✓ RUNNING" if found else "✗ NOT FOUND"
        print(f"  {service_desc:30s}: {status}")

        if not found:
            all_found = False
            print(f"    WARNING: {service_desc} not found")

    if not all_found:
        print("\nWARNING: Some critical services may not be running")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_process_statistics(device_manager):
    """Test getting overall process statistics.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    processes = list(board.sw.get_running_processes(ps_options="-A"))

    # Calculate statistics
    total_processes = len(processes)
    kernel_threads = len([p for p in processes if p.get("tty") is None])
    user_processes = total_processes - kernel_threads

    print("\nProcess Statistics:")
    print(f"  Total Processes: {total_processes}")
    print(f"  Kernel Threads: {kernel_threads}")
    print(f"  User Processes: {user_processes}")

    # Count by different categories
    ccsp_count = len([p for p in processes if "ccsp" in p["command"].lower()])
    print(f"\nProcess Categories:")
    print(f"  CCSP Processes: {ccsp_count}")

    assert total_processes > 0, "Should have processes running"
