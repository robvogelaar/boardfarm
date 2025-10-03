"""Tests for process management primitives on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_running_processes(device_manager):
    board = device_manager.get_device_by_type(CPE)

    processes = list(board.sw.get_running_processes(ps_options="-A"))

    assert len(processes) > 0, "Should have at least one running process"
    assert isinstance(processes[0], dict), "Process should be a dictionary"

    expected_keys = ["pid", "command"]
    for key in expected_keys:
        assert key in processes[0], f"Process should have '{key}' key"

    print(f"\nTotal running processes: {len(processes)}")
    print("\nFirst 10 processes:")
    for proc in processes[:10]:
        print(f"  PID {proc['pid']:>6}: {proc['command']}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_kill_process_immediately(device_manager):
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    print("\nTesting process kill:")

    output = console.execute_command("sleep 300 & echo $!")
    pid_line = output.strip().split("\n")[-1]

    try:
        pid = int(pid_line.strip())
        print(f"  Started sleep process: PID {pid}")

        board.sw.kill_process_immediately(pid)
        print(f"  OK Killed process {pid}")

        import time
        time.sleep(1)
        output = console.execute_command("pgrep -f 'sleep 300' || echo 'None'")
        if "None" in output:
            print("  OK Process successfully terminated")
    except (ValueError, IndexError):
        pytest.skip("Could not start test process")
