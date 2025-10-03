"""Tests for logging and event primitives on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_read_event_logs(device_manager):
    board = device_manager.get_device_by_type(CPE)

    logs = board.sw.read_event_logs()

    assert len(logs) > 0, "Should have event logs"
    print(f"\nTotal event log entries: {len(logs)}")
    print("\nRecent log entries:")
    for log in logs[:5]:
        print(f"  {log}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_board_logs_continuous(device_manager):
    board = device_manager.get_device_by_type(CPE)

    print("\nCapturing board logs for 3 seconds:")
    logs = board.sw.get_board_logs(timeout=3)

    assert isinstance(logs, str), "Logs should be a string"
    lines = logs.split("\n")
    print(f"  Captured {len(lines)} lines")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_read_file_content(device_manager):
    board = device_manager.get_device_by_type(CPE)

    content = board.sw.get_file_content("/proc/version", timeout=5)

    print(f"\n/proc/version:")
    print(f"  {content[:100]}")
    assert len(content) > 0, "File should have content"


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_add_info_to_file(device_manager):
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    test_file = "/tmp/boardfarm_test_write.txt"
    test_content = "Boardfarm test line"

    print(f"\nTesting file write to {test_file}:")

    console.execute_command(f"rm -f {test_file}")

    board.sw.add_info_to_file(test_content, test_file)
    print("  OK Wrote to file")

    content = board.sw.get_file_content(test_file, timeout=5)
    assert test_content in content, "Content should match"
    print("  OK Content verified")

    console.execute_command(f"rm -f {test_file}")
