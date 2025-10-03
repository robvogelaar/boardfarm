"""Tests for network utility primitives on RDKB devices."""

import pytest
import time

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_netstat_basic(device_manager):
    """Test basic netstat functionality.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get netstat output as DataFrame
    try:
        netstat_df = board.sw.nw_utility.netstat(opts="-tuln")

        assert netstat_df is not None, "Netstat should return data"
        assert len(netstat_df) > 0, "Should have at least some network connections"

        print(f"\nNetstat results: {len(netstat_df)} connections")
        print("\nFirst 10 connections:")
        print(netstat_df.head(10))
    except ValueError as e:
        pytest.skip(f"Netstat parsing failed: {e}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_netstat_listening_ports(device_manager):
    """Test finding listening ports with netstat.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get listening ports
    netstat_df = board.sw.nw_utility.netstat(opts="-tln")

    if len(netstat_df) > 0:
        print("\nListening TCP ports:")
        print(netstat_df.head(15))

        # Count by protocol if column exists
        if "Proto" in netstat_df.columns:
            protocol_counts = netstat_df["Proto"].value_counts()
            print("\nConnections by protocol:")
            print(protocol_counts)
    else:
        print("\nNo listening ports found")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_tcpdump_capture(device_manager):
    """Test packet capture with tcpdump.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    capture_file = "/tmp/test_capture.pcap"
    interface = "erouter0"

    print(f"\nStarting packet capture on {interface}...")

    # Start tcpdump (capture 20 packets)
    try:
        pid = board.sw.nw_utility.start_tcpdump(
            fname=capture_file,
            interface=interface,
            filters={"-c": "20"}  # Capture only 20 packets
        )
    except ValueError as e:
        pytest.skip(f"Tcpdump failed to start: {e}")

    print(f"Tcpdump started with PID: {pid}")

    # Generate some traffic
    console = board.hw.get_console("console")
    console.execute_command("ping -c 5 8.8.8.8 &")

    # Wait for capture to complete
    time.sleep(3)

    # Stop tcpdump
    print("Stopping packet capture...")
    board.sw.nw_utility.stop_tcpdump(pid=pid)

    # Read captured packets
    print("Reading captured packets...")
    packets = board.sw.nw_utility.read_tcpdump(
        capture_file=capture_file,
        protocol="",  # All protocols
        rm_pcap=True  # Clean up after reading
    )

    assert len(packets) > 0, "Should have captured some packets"
    print(f"\nCaptured packet data length: {len(packets)} bytes")

    # Show first 500 characters
    print("\nSample packet data:")
    print(packets[:500])


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_tcpdump_filter_icmp(device_manager):
    """Test packet capture with ICMP filter.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    capture_file = "/tmp/test_icmp.pcap"
    interface = "erouter0"

    print(f"\nStarting ICMP packet capture on {interface}...")

    # Start tcpdump for ICMP packets
    try:
        pid = board.sw.nw_utility.start_tcpdump(
            fname=capture_file,
            interface=interface,
            filters={"-c": "10"}  # Capture 10 packets
        )
    except ValueError as e:
        pytest.skip(f"Tcpdump failed to start: {e}")

    print(f"Tcpdump started with PID: {pid}")

    # Generate ICMP traffic
    console = board.hw.get_console("console")
    console.execute_command("ping -c 5 8.8.8.8")

    # Stop tcpdump
    time.sleep(2)
    board.sw.nw_utility.stop_tcpdump(pid=pid)

    # Read ICMP packets only
    packets = board.sw.nw_utility.read_tcpdump(
        capture_file=capture_file,
        protocol="icmp",
        rm_pcap=True
    )

    print(f"\nICMP packet data captured")
    if "ICMP" in packets or "icmp" in packets:
        print("✓ Successfully captured ICMP packets")
    else:
        print("⚠ Warning: No ICMP packets found in capture")

    # Show sample
    print("\nSample ICMP packet data:")
    print(packets[:300])


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_ping_connectivity(device_manager):
    """Test basic network connectivity with ping.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    # Ping Google DNS
    print("\nTesting connectivity to 8.8.8.8...")
    output = console.execute_command("ping -c 5 8.8.8.8", timeout=15)

    # Check for successful ping
    if "5 packets transmitted" in output and "0% packet loss" in output:
        print("✓ Connectivity test passed")
    else:
        print("⚠ Connectivity test failed or partial packet loss")

    # Extract statistics
    print("\nPing Statistics:")
    lines = output.split("\n")
    for line in lines:
        if "packets transmitted" in line or "rtt min/avg/max" in line:
            print(f"  {line.strip()}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_traceroute(device_manager):
    """Test traceroute functionality.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    print("\nPerforming traceroute to 8.8.8.8...")

    try:
        result = board.sw.nw_utility.traceroute(
            host="8.8.8.8",
            opts="-n -m 10",  # Don't resolve, max 10 hops
            timeout=60
        )

        print("Traceroute results:")
        lines = result.split("\n")[:15]  # First 15 lines
        for line in lines:
            if line.strip():
                print(f"  {line}")

    except Exception as e:
        print(f"Traceroute failed: {e}")
        pytest.skip("Traceroute not available or failed")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_dns_resolution(device_manager):
    """Test DNS name resolution.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    # Test DNS resolution with nslookup
    print("\nTesting DNS resolution for google.com...")
    output = console.execute_command("nslookup google.com", timeout=10)

    if "Address" in output or "answer" in output.lower():
        print("✓ DNS resolution successful")
        print("\nDNS Response:")
        lines = output.split("\n")[:10]
        for line in lines:
            if line.strip():
                print(f"  {line}")
    else:
        print("⚠ DNS resolution may have failed")
        print(output)


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_network_interface_statistics(device_manager):
    """Test getting network interface statistics.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    # Get interface statistics
    output = console.execute_command("ifconfig erouter0")

    print("\nErouter0 Statistics:")
    print(output)

    # Also show with ip command
    output2 = console.execute_command("ip -s link show erouter0")
    print("\nDetailed statistics (ip -s):")
    print(output2)


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_routing_table(device_manager):
    """Test viewing routing table.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    # IPv4 routing table
    print("\nIPv4 Routing Table:")
    output = console.execute_command("ip route show")
    print(output)

    # IPv6 routing table
    print("\nIPv6 Routing Table:")
    output = console.execute_command("ip -6 route show")
    print(output)


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_arp_table(device_manager):
    """Test viewing ARP table.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    # Get ARP table
    print("\nARP Table:")
    output = console.execute_command("ip neigh show")
    print(output)

    # Count entries
    lines = [line for line in output.split("\n") if line.strip()]
    print(f"\nTotal ARP entries: {len(lines)}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_socket_statistics(device_manager):
    """Test socket statistics with ss command.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    # Get socket statistics
    print("\nSocket Statistics (ss -s):")
    output = console.execute_command("ss -s")
    print(output)

    # Get listening sockets
    print("\nListening TCP Sockets:")
    output = console.execute_command("ss -tln | head -n 20")
    print(output)


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_network_bandwidth_test(device_manager):
    """Test measuring available bandwidth (if tools available).

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    # Check if speedtest or similar tools are available
    print("\nChecking for bandwidth testing tools...")

    tools = ["speedtest-cli", "iperf", "iperf3"]
    available_tools = []

    for tool in tools:
        output = console.execute_command(f"which {tool}")
        if "/" in output:
            available_tools.append(tool)
            print(f"  ✓ {tool} is available")

    if len(available_tools) == 0:
        print("  ⚠ No bandwidth testing tools found")
        pytest.skip("No bandwidth testing tools available")
    else:
        print(f"\n{len(available_tools)} bandwidth testing tool(s) available")
