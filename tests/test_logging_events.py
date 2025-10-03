"""Tests for logging and event primitives on RDKB devices."""

import pytest
import time

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_read_event_logs(device_manager):
    """Test reading system event logs via logread.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    event_logs = list(board.sw.read_event_logs())

    assert len(event_logs) > 0, "Should have at least some event logs"
    assert isinstance(event_logs[0], dict), "Event log entry should be a dictionary"

    print(f"\nTotal event log entries: {len(event_logs)}")

    # Display first 5 entries
    print("\nFirst 5 event log entries:")
    for i, log_entry in enumerate(event_logs[:5]):
        print(f"\n  Entry {i + 1}:")
        for key, value in log_entry.items():
            if value:  # Only print non-empty values
                # Truncate long content
                if key == "content" and isinstance(value, str) and len(value) > 80:
                    value = value[:80] + "..."
                print(f"    {key}: {value}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_filter_event_logs_by_tag(device_manager):
    """Test filtering event logs by tag.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    event_logs = list(board.sw.read_event_logs())

    # Count logs by tag
    tags = {}
    for log_entry in event_logs:
        tag = log_entry.get("tag", "unknown")
        tags[tag] = tags.get(tag, 0) + 1

    print("\nEvent logs by tag:")
    for tag, count in sorted(tags.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tag:20s}: {count} entries")

    # Show some kernel logs
    kern_logs = [log for log in event_logs if log.get("tag") == "kern"]
    if len(kern_logs) > 0:
        print(f"\nSample kernel logs (showing first 3):")
        for log in kern_logs[:3]:
            print(f"  {log.get('date')}: {log.get('content', '')[:80]}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_search_event_logs_for_errors(device_manager):
    """Test searching event logs for error messages.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    event_logs = list(board.sw.read_event_logs())

    # Search for error-related entries
    error_keywords = ["error", "fail", "critical", "alert", "emerg"]
    error_logs = []

    for log_entry in event_logs:
        content = log_entry.get("content", "").lower()
        if any(keyword in content for keyword in error_keywords):
            error_logs.append(log_entry)

    print(f"\nError-related log entries found: {len(error_logs)}")

    if len(error_logs) > 0:
        print("\nSample error log entries (first 5):")
        for log in error_logs[:5]:
            date = log.get("date", "N/A")
            tag = log.get("tag", "unknown")
            content = log.get("content", "")[:100]
            print(f"\n  [{date}] [{tag}]")
            print(f"    {content}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_board_logs_continuous(device_manager):
    """Test collecting continuous board logs for a time period.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    print("\nCollecting board logs for 5 seconds...")

    # Collect logs for 5 seconds
    logs = board.sw.get_board_logs(timeout=5)

    assert isinstance(logs, str), "Board logs should be a string"
    assert len(logs) > 0, "Should have collected some logs"

    lines = logs.split("\n")
    print(f"Collected {len(lines)} lines of console output")

    # Show first 10 lines
    print("\nFirst 10 lines of collected logs:")
    for line in lines[:10]:
        if line.strip():
            print(f"  {line[:100]}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_read_file_content(device_manager):
    """Test reading file content from device.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Read /etc/version file
    version_content = board.sw.get_file_content("/etc/version", timeout=10)

    assert isinstance(version_content, str), "File content should be a string"
    assert len(version_content) > 0, "Version file should not be empty"

    print(f"\n/etc/version content:")
    print(f"  {version_content.strip()}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_read_proc_files(device_manager):
    """Test reading various /proc files for system information.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    proc_files = [
        "/proc/uptime",
        "/proc/loadavg",
        "/proc/meminfo",
        "/proc/cpuinfo",
    ]

    print("\n/proc filesystem contents:")

    for proc_file in proc_files:
        try:
            content = board.sw.get_file_content(proc_file, timeout=10)
            lines = content.strip().split("\n")

            print(f"\n{proc_file}:")
            # Show first 5 lines only
            for line in lines[:5]:
                print(f"  {line}")

            if len(lines) > 5:
                print(f"  ... ({len(lines) - 5} more lines)")

        except Exception as e:
            print(f"\n{proc_file}: Error reading - {e}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_add_info_to_file(device_manager):
    """Test adding information to a file.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    test_file = "/tmp/boardfarm_test.log"
    test_content = f"Test entry at {time.strftime('%Y-%m-%d %H:%M:%S')}"

    # Add content to file
    board.sw.add_info_to_file(test_content, test_file)

    # Read back the content
    file_content = board.sw.get_file_content(test_file, timeout=10)

    assert test_content in file_content, "Test content should be in file"

    print(f"\nSuccessfully wrote to {test_file}")
    print(f"Content: {test_content}")

    # Clean up
    console = board.hw.get_console("console")
    console.execute_command(f"rm -f {test_file}")
    print(f"Cleaned up test file")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_system_log_analysis(device_manager):
    """Test analyzing system logs for patterns.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    event_logs = list(board.sw.read_event_logs())

    # Analyze logs
    analysis = {
        "total_entries": len(event_logs),
        "unique_tags": set(),
        "unique_hostnames": set(),
        "date_range": {"first": None, "last": None},
    }

    for log_entry in event_logs:
        if tag := log_entry.get("tag"):
            analysis["unique_tags"].add(tag)
        if hostname := log_entry.get("hostname"):
            analysis["unique_hostnames"].add(hostname)
        if date := log_entry.get("date"):
            if analysis["date_range"]["first"] is None:
                analysis["date_range"]["first"] = date
            analysis["date_range"]["last"] = date

    print("\nSystem Log Analysis:")
    print(f"  Total log entries: {analysis['total_entries']}")
    print(f"  Unique tags: {len(analysis['unique_tags'])}")
    print(f"  Tags: {', '.join(sorted(analysis['unique_tags']))}")
    print(f"  Unique hostnames: {len(analysis['unique_hostnames'])}")
    print(f"  Hostnames: {', '.join(sorted(analysis['unique_hostnames']))}")

    if analysis["date_range"]["first"]:
        print(f"  Date range:")
        print(f"    First: {analysis['date_range']['first']}")
        print(f"    Last: {analysis['date_range']['last']}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_dmesg_kernel_messages(device_manager):
    """Test reading kernel messages via dmesg.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    # Get kernel messages
    dmesg_output = console.execute_command("dmesg | tail -20")

    assert len(dmesg_output) > 0, "Should have kernel messages"

    print("\nRecent kernel messages (last 20):")
    print(dmesg_output)


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_log_file_locations(device_manager):
    """Test checking common log file locations.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    # Common log locations
    log_locations = [
        "/var/log",
        "/nvram/logs",
        "/tmp",
    ]

    print("\nChecking common log file locations:")

    for location in log_locations:
        output = console.execute_command(f"ls -lh {location}/*.log 2>/dev/null || echo 'No logs found'")
        print(f"\n{location}:")

        lines = output.split("\n")[:10]
        for line in lines:
            if line.strip() and "total" not in line.lower():
                print(f"  {line}")
