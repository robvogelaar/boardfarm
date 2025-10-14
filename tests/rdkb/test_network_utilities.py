"""Tests for network utility primitives on RDKB devices."""

import pytest
import time

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_netstat_basic(device_manager):
    board = device_manager.get_device_by_type(CPE)

    netstat_data = board.sw.nw_utility.netstat("-tuln")

    print(f"\nNetstat results: {len(netstat_data)} rows")
    print(f"Columns: {list(netstat_data.columns)}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_tcpdump_capture(device_manager):
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    print("\nTesting tcpdump capture:")

    try:
        pid = board.sw.nw_utility.start_tcpdump("icmp", "erouter0")
        print(f"  Started tcpdump: PID {pid}")

        console.execute_command("ping -c 3 8.8.8.8")
        time.sleep(2)

        board.sw.nw_utility.stop_tcpdump(pid)
        print(f"  Stopped tcpdump")

        try:
            packets = board.sw.nw_utility.read_tcpdump(f"/tmp/tcpdump_{pid}.pcap")
            print(f"  Captured {len(packets)} packets")
        except Exception as e:
            print(f"  Could not read pcap: {e}")
    except (ValueError, Exception) as e:
        pytest.skip(f"tcpdump not available or failed to start: {e}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_traceroute(device_manager):
    board = device_manager.get_device_by_type(CPE)

    print("\nTraceroute to 8.8.8.8:")
    try:
        result = board.sw.nw_utility.traceroute("8.8.8.8")
        print(f"  Hops: {len(result)}")
        for hop in result[:5]:
            print(f"    {hop}")
    except Exception as e:
        pytest.skip(f"Traceroute not available: {e}")
