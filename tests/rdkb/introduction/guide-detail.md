# BoardFarm: Getting Started Guide with Test Primitives

## Table of Contents

- [Quick Start](#quick-start)
- [Test Primitives Reference](#test-primitives-reference)
  - [1. SSH Connection to CPE Device](#1-ssh-connection-to-cpe-device)
  - [2. HTTP API Connection to ACS Server](#2-http-api-connection-to-acs-server)
  - [3. Network Testing Primitives](#3-network-testing-primitives)
  - [4. Packet Capture Primitives](#4-packet-capture-primitives)
  - [5. Web GUI Automation Primitives](#5-web-gui-automation-primitives)
  - [6. Device Configuration Primitives](#6-device-configuration-primitives)
  - [7. File Transfer Primitives](#7-file-transfer-primitives)
  - [8. Device Connection Types](#8-device-connection-types)
- [Example Complete Test](#example-complete-test)
- [Configuration Examples](#configuration-examples)

## Quick Start

BoardFarm is a Python testing framework for network equipment. It provides test primitives to connect to devices, execute commands, and validate results.

### Installation

```bash
pip install git+https://github.com/lgirdk/boardfarm.git@boardfarm3
pip install git+https://github.com/lgirdk/pytest-boardfarm.git@boardfarm3
```

### Basic Test Run

```bash
pytest --board-name my-cpe --env-config testbed.json --inventory-config devices.json ./tests/
```

## Test Primitives Reference

### 1. SSH Connection to CPE Device

#### Basic SSH Connection:

```python
from boardfarm3.lib.connections.ssh_connection import SSHConnection

# Establish SSH connection
device_console = SSHConnection(
    name="cpe.console",
    ip_addr="192.168.1.1",
    username="root",
    password="admin123",
    port=22,
    shell_prompt=["# ", "$ "]
)

# Login and execute commands
device_console.login_to_server(password="admin123")
result = device_console.execute_command("uname -a")
```

#### In Test Context:

```python
def test_device_info(devices):
    cpe = devices.board  # Main CPE device

    # Execute command on device
    output = cpe.execute_command("cat /proc/version")
    assert "Linux" in output

    # Check system uptime
    uptime = cpe.execute_command("uptime")
    assert "load average" in uptime
```

### 2. HTTP API Connection to ACS Server

#### GenieACS TR-069 Operations:

```python
from boardfarm3.devices.genie_acs import GenieACS

def test_tr069_operations(devices):
    acs = devices.acs  # ACS server device

    # Get Parameter Values (GPV)
    result = acs.GPV("Device.DeviceInfo.ModelName")
    model_name = result[0]["value"]
    assert model_name is not None

    # Set Parameter Values (SPV)
    status = acs.SPV([{
        "Device.WiFi.SSID.1.SSID": "TestNetwork"
    }])
    assert status in [0, 1]  # Success codes

    # Verify the change
    verify_result = acs.GPV("Device.WiFi.SSID.1.SSID")
    assert verify_result[0]["value"] == "TestNetwork"
```

#### Custom HTTP API Calls:

```python
import httpx

def test_custom_api_call():
    client = httpx.Client(
        auth=("admin", "password"),
        base_url="http://192.168.1.1:8080"
    )

    # GET request
    response = client.get("/api/status")
    assert response.status_code == 200

    # POST request
    data = {"interface": "eth0", "enable": True}
    response = client.post("/api/configure", json=data)
    assert response.status_code == 200
```

### 3. Network Testing Primitives

#### Ping Tests:

```python
def test_network_connectivity(devices):
    lan_client = devices.lan

    # Basic ping
    result = lan_client.ping("8.8.8.8", ping_count=3)
    assert result is True

    # Ping with JSON output for detailed analysis
    ping_data = lan_client.ping("8.8.8.8", json_output=True)
    assert ping_data["statistics"]["packet_loss"] < 10

    # Interface-specific ping
    result = lan_client.ping("192.168.1.1", ping_interface="eth0")
    assert result is True
```

#### Traceroute:

```python
def test_routing_path(devices):
    wan_client = devices.wan

    # IPv4 traceroute
    trace_output = wan_client.traceroute("8.8.8.8")
    assert "ms" in trace_output

    # IPv6 traceroute
    trace_output = wan_client.traceroute("2001:4860:4860::8888", version="6")
    assert "2001:4860:4860::8888" in trace_output
```

#### HTTP Connectivity:

```python
def test_web_access(devices):
    client = devices.lan

    # Test HTTP connectivity
    result = client.curl("http://example.com", protocol="http")
    assert result is True

    # Test HTTPS with specific options
    result = client.curl(
        "https://secure-site.com",
        protocol="https",
        port=443,
        options="--connect-timeout 30"
    )
    assert result is True
```

### 4. Packet Capture Primitives

#### TCPDump Context Manager:

```python
def test_with_packet_capture(devices):
    wan = devices.wan
    lan = devices.lan

    # Capture packets during test
    with wan.tcpdump_capture(
        fname="wan_capture.pcap",
        interface="eth0",
        additional_args="port 80"
    ) as process_id:
        # Perform network activity
        lan.curl("http://example.com", protocol="http")
        time.sleep(5)

    # Analyze captured packets
    output = wan.tshark_read_pcap(
        fname="wan_capture.pcap",
        additional_args="-Y 'http.request'"
    )
    assert "GET /" in output
```

#### Manual Packet Capture:

```python
def test_manual_capture(devices):
    device = devices.board

    # Start capture
    process_id = device.start_tcpdump(
        interface="br-lan",
        port="80",
        output_file="http_capture.pcap"
    )

    # Run test
    time.sleep(30)

    # Stop capture
    device.stop_tcpdump(process_id)

    # Read results
    packets = device.read_tcpdump_pcap("http_capture.pcap")
    assert len(packets) > 0
```

### 5. Web GUI Automation Primitives

#### Selenium-based GUI Testing:

```python
def test_web_gui_interaction(devices):
    cpe = devices.board

    # Initialize web GUI driver
    web_gui = cpe.webgui(devices)

    # Login to device web interface
    assert web_gui.check_page_load()

    # Navigate to specific page
    web_gui.navigate_to_target_page(["WiFi", "Settings"])
    time.sleep(2)

    # Find and interact with elements
    ssid_field = web_gui.driver.find_element_by_id("ssid_input")
    ssid_field.clear()
    ssid_field.send_keys("NewNetworkName")

    # Click apply button
    apply_btn = web_gui.driver.find_element_by_id("apply_btn")
    apply_btn.click()

    # Wait for changes to apply
    web_gui.driver.implicitly_wait(10)

    # Close driver
    web_gui.driver_close()
```

#### GUI Helper Functions:

```python
from boardfarm3.lib.gui_helper import click_button_id

def test_gui_helpers(devices):
    web_gui = devices.board.webgui(devices)

    # Click button by ID
    click_button_id(web_gui.driver, "home_button")

    # Enter input value
    web_gui.enter_input_value("device_name", "MyRouter")

    # Verify page elements
    element = web_gui.driver.find_element_by_id("status_text")
    assert "Connected" in element.text
```

### 6. Device Configuration Primitives

#### DMCLI Operations (Data Model CLI):

```python
def test_dmcli_operations(devices):
    cpe = devices.board

    # Get parameter value
    result = cpe.dmcli.GPV("Device.WiFi.SSID.1.SSID")
    current_ssid = result.rval

    # Set parameter value
    result = cpe.dmcli.SPV(
        "Device.WiFi.SSID.1.SSID",
        "TestNetwork",
        "string"
    )
    assert result.status == "succeed"

    # Verify change
    result = cpe.dmcli.GPV("Device.WiFi.SSID.1.SSID")
    assert result.rval == "TestNetwork"
```

#### Console Expect Patterns:

```python
import pexpect

def test_console_interaction(devices):
    board = devices.board

    # Send command and wait for specific output
    board.sendline("ifconfig")
    board.expect(["inet addr", "inet "], timeout=30)

    # Wait for timeout (useful for delays)
    board.expect(pexpect.TIMEOUT, timeout=60)

    # Look for multiple possible responses
    index = board.expect([
        "command not found",
        "Permission denied",
        board.prompt
    ], timeout=10)

    if index == 0:
        print("Command not available")
    elif index == 1:
        print("Need root access")
    else:
        print("Command successful")
```

### 7. File Transfer Primitives

#### SCP File Transfer:

```python
def test_file_operations(devices):
    device = devices.lan

    # Upload file to device
    device.scp(
        host="192.168.1.100",
        port=22,
        username="root",
        password="admin",
        src_path="/local/config.txt",
        dst_path="/tmp/config.txt",
        action="upload"
    )

    # Download file from device
    device.scp(
        host="192.168.1.100",
        port=22,
        username="root",
        password="admin",
        src_path="/var/log/messages",
        dst_path="/local/device.log",
        action="download"
    )
```

### 8. Device Connection Types

#### Connection Factory:

```python
from boardfarm3.lib.connection_factory import connection_factory

# SSH connection
ssh_console = connection_factory(
    "ssh",
    "device.console",
    username="root",
    password="admin",
    ip_addr="192.168.1.1",
    port=22,
    shell_prompt=["# "]
)

# Telnet connection
telnet_console = connection_factory(
    "telnet",
    "device.console",
    username="admin",
    password="admin",
    ip_addr="192.168.1.1",
    port=23,
    shell_prompt=["# "]
)

# Serial connection
serial_console = connection_factory(
    "ser2net",
    "device.console",
    ip_addr="192.168.1.50",
    port=2001,
    shell_prompt=["# "]
)
```

## Example Complete Test

**This example demonstrates how to combine multiple test primitives into a comprehensive workflow.**

```python
import pytest
import time
from boardfarm3.lib.device_manager import device_manager
from boardfarm3.lib.device_type import device_type

def test_complete_workflow():
    devices = device_manager()
    board = devices.get_device_by_type(device_type.board)
    lan = devices.get_device_by_type(device_type.lan)
    acs = devices.get_device_by_type(device_type.acs)

    # 1. Configure device via TR-069
    acs.SPV([{"Device.WiFi.SSID.1.SSID": "TestNet"}])
    acs.SPV([{"Device.WiFi.SSID.1.Enable": "true"}])

    # 2. Verify configuration on device
    result = board.execute_command("iwconfig")
    assert "TestNet" in result

    # 3. Test connectivity with packet capture
    with lan.tcpdump_capture("test.pcap", "eth0"):
        success = lan.ping("8.8.8.8", ping_count=5)
        assert success

    # 4. Validate web interface
    web_gui = board.webgui(devices)
    web_gui.navigate_to_target_page(["Status"])
    status_element = web_gui.driver.find_element_by_id("wifi_status")
    assert "Enabled" in status_element.text
    web_gui.driver_close()

    # 5. Cleanup
    acs.SPV([{"Device.WiFi.SSID.1.Enable": "false"}])
```

## Configuration Examples

### Device Inventory (`devices.json`):

```json
{
  "my-cpe": {
    "device_type": "board",
    "connection_type": "ssh",
    "ipaddr": "192.168.1.1",
    "username": "root",
    "password": "admin",
    "port": 22
  },
  "lan-client": {
    "device_type": "lan",
    "connection_type": "ssh",
    "ipaddr": "192.168.1.100",
    "username": "ubuntu",
    "password": "ubuntu"
  },
  "acs-server": {
    "device_type": "acs",
    "connection_type": "ssh",
    "ipaddr": "192.168.1.50",
    "http_port": 7547,
    "http_username": "admin",
    "http_password": "admin"
  }
}
```

### Environment Config (`testbed.json`):

```json
{
  "environment_def": {
    "board": {
      "model": "test-router",
      "lan_device": "my-cpe",
      "acs_device": "acs-server"
    }
  }
}
```

### Connection Types Summary

| Connection Type | Use Case | Required Fields |
|-----------------|----------|-----------------|
| `ssh` | Remote device access | ipaddr, username, password, port (22) |
| `telnet` | Legacy device access | ipaddr, username, password, port (23) |
| `ser2net` | Serial console access | ipaddr, port |
| `http` | API/Web interface access | ipaddr, http_port, http_username, http_password |

---

*These primitives provide the building blocks for comprehensive network device testing. Combine them to create complex test scenarios that validate device functionality across multiple protocols and interfaces.*
