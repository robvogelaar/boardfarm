# Boardfarm Test Primitives Reference

Comprehensive list of all available test primitives in the boardfarm framework for RDK-B devices.

## Network Interface Primitives

### Interface Information
- **get_interface_ipv4addr(interface)** - Get IPv4 address of a network interface
- **get_interface_ipv6addr(interface)** - Get global IPv6 address of a network interface
- **get_interface_link_local_ipv6_addr(interface)** - Get link-local IPv6 address
- **get_interface_ipv4_netmask(interface)** - Get IPv4 netmask of an interface
- **get_interface_mac_addr(interface)** - Get MAC address of an interface
- **get_interface_mtu_size(interface)** - Get MTU size in bytes
- **is_link_up(interface)** - Check if network interface link is up

### Interface Properties
- **erouter_iface** - E-Router interface name (property)
- **lan_iface** - LAN interface name (property)
- **guest_iface** - Guest network interface name (property)
- **aftr_iface** - AFTR interface name (property)
- **lan_gateway_ipv4** - LAN Gateway IPv4 address (property)
- **lan_gateway_ipv6** - LAN Gateway IPv6 address (property)

## System Information Primitives

### System Status
- **get_seconds_uptime()** - Get system uptime in seconds
- **is_online()** - Check if CPE is online
- **get_load_avg()** - Get current load average (1-minute)
- **get_memory_utilization()** - Get memory stats (total, used, free, cache, available)
- **get_provision_mode()** - Get device provision mode
- **is_production()** - Check if running production software
- **get_date()** - Get system date and time string
- **set_date(date_string)** - Set system date and time
- **version** - Get CPE software version (property)

### Boot & Reset Operations
- **verify_cpe_is_booting()** - Verify CPE is in booting state
- **wait_for_boot()** - Wait for CPE to complete boot sequence
- **finalize_boot()** - Validate board settings after boot
- **reset(method)** - Perform device reset via specified method
- **factory_reset(method)** - Perform factory reset

## Process Management Primitives

- **get_running_processes()** - Get list of running processes (via ps)
- **kill_process_immediately(pid)** - Kill process by PID using SIGKILL
- **get_ntp_sync_status()** - Get NTP synchronization status via ntpq

## Logging Primitives

- **enable_logs(component, flag)** - Enable/disable logs for a component
- **get_board_logs(timeout)** - Capture console logs for specified duration
- **read_event_logs()** - Read and parse event logs from logread
- **get_boottime_log()** - Get boot time logs
- **get_tr069_log()** - Get TR-069 agent logs

## File Operations Primitives

- **get_file_content(fname, timeout)** - Read file content with timeout
- **add_info_to_file(to_add, fname)** - Append data to file

## Network Utilities (`board.sw.nw_utility`)

### Network Testing
- **netstat(opts, extra_opts)** - Execute netstat and return parsed DataFrame
- **start_tcpdump(iface, filters)** - Start packet capture on interface
- **stop_tcpdump(pid)** - Stop tcpdump by process ID
- **read_tcpdump(pcap_file)** - Read and parse tcpdump capture file
- **traceroute_host(host_ip)** - Run traceroute to destination host
- **gen_uuid()** - Generate unique identifier (UUID)

### File Transfer
- **scp(ip, port, user, pwd, source_path, dest_path, action)** - SCP file transfer (upload/download)
- **tftp(ip, filename, action)** - TFTP file transfer (get/put)

### Network Operations
- **http_get(url, timeout)** - Perform HTTP GET request via curl
- **dns_lookup(domain)** - DNS lookup via dig command
- **nmap(src_device, dst_device, opts)** - Run nmap scan

## Firewall Primitives (`board.sw.firewall`)

### IPv4 Firewall
- **get_iptables_list(table, chain)** - Get iptables rules as dictionary
- **is_iptable_empty(opts, extra_opts)** - Check if iptables is empty
- **get_iptables_policy(table)** - Get iptables policies
- **add_drop_rule_iptables(option, valid_ip)** - Add drop rule to iptables
- **del_drop_rule_iptables(option, valid_ip)** - Delete drop rule from iptables

### IPv6 Firewall
- **get_ip6tables_list(table, chain)** - Get ip6tables rules as dictionary
- **is_ip6table_empty(opts, extra_opts)** - Check if ip6tables is empty
- **get_ip6tables_policy(table)** - Get ip6tables policies
- **add_drop_rule_ip6tables(option, valid_ip)** - Add drop rule to ip6tables
- **del_drop_rule_ip6tables(option, valid_ip)** - Delete drop rule from ip6tables

## DMCLI Primitives (`board.sw.dmcli`)

### DMCLI Operations
- **GPV(parameter)** - Get Parameter Value (returns DMCLIResult)
- **SPV(parameter, value, type)** - Set Parameter Value
- **AddObject(object_path)** - Add new DMCLI object instance
- **DelObject(object_path)** - Delete DMCLI object instance

**Example:**
```python
result = board.sw.dmcli.GPV("Device.WiFi.SSID.1.SSID")
print(result.rval)  # Access return value

board.sw.dmcli.SPV("Device.WiFi.SSID.1.Enable", "true", "bool")
```

## WiFi HAL Primitives (`board.sw.wifi`)

### WiFi Information
- **wlan_ifaces** - Get all WLAN interfaces (property)
- **get_ssid(network_type, band)** - Get WiFi SSID
- **get_bssid(network_type, band)** - Get WiFi BSSID (AP MAC address)
- **get_passphrase(interface)** - Get WiFi passphrase

### WiFi Control
- **is_wifi_enabled(network_type, band)** - Check if WiFi is enabled
- **enable_wifi(network_type, band)** - Enable WiFi (returns ssid, bssid, passphrase)

**Parameters:**
- `network_type`: "private", "guest", "community"
- `band`: "2.4", "5" (GHz)

## TR-069 Primitives

- **is_tr069_connected()** - Check if TR-069 agent is connected
- **gui_password** - Get GUI login password (property)
- **cpe_id** - Get TR-069 CPE ID (property)
- **tr69_cpe_id** - Get TR-69 CPE Identifier (property)

## Hardware Interface (`board.hw`)

- **get_console(console_name)** - Get console connection object
- **power_cycle()** - Power cycle the device
- **wait_for_hw_boot()** - Wait for hardware boot completion
- **mac_address** - Get device MAC address (property)
- **wan_iface** - Get WAN interface name (property)

---

## Usage Examples

### Basic System Information
```python
from boardfarm3.templates.cpe import CPE

board = device_manager.get_device_by_type(CPE)

# System info
uptime = board.sw.get_seconds_uptime()
load = board.sw.get_load_avg()
memory = board.sw.get_memory_utilization()
```

### Network Interface Operations
```python
# Get interface information
ipv4 = board.sw.get_interface_ipv4addr("erouter0")
mac = board.sw.get_interface_mac_addr("erouter0")
mtu = board.sw.get_interface_mtu_size("erouter0")
link_up = board.sw.is_link_up("erouter0")
```

### Network Utilities
```python
# Network testing
netstat_data = board.sw.nw_utility.netstat("-tuln")
traceroute_result = board.sw.nw_utility.traceroute_host("8.8.8.8")

# HTTP operations
http_result = board.sw.nw_utility.http_get("http://example.com", timeout=10)
print(http_result.status_code)
```

### Firewall Operations
```python
# IPv4 firewall
rules = board.sw.firewall.get_iptables_list("filter", "INPUT")
is_empty = board.sw.firewall.is_iptable_empty()
board.sw.firewall.add_drop_rule_iptables("src", "192.168.1.100")
```

### DMCLI Operations
```python
# Get/Set TR-181 parameters
result = board.sw.dmcli.GPV("Device.DeviceInfo.SoftwareVersion")
print(result.rval)

board.sw.dmcli.SPV("Device.WiFi.Radio.1.Enable", "true", "bool")
```

### WiFi Operations
```python
# WiFi management
ssid = board.sw.wifi.get_ssid("private", "5")
bssid = board.sw.wifi.get_bssid("private", "5")
enabled = board.sw.wifi.is_wifi_enabled("guest", "2.4")

# Enable WiFi
ssid, bssid, passphrase = board.sw.wifi.enable_wifi("private", "2.4")
```

### Process Management
```python
# Process operations
processes = board.sw.get_running_processes()
ntp_synced = board.sw.get_ntp_sync_status()
board.sw.kill_process_immediately(1234)
```

### Logging
```python
# Enable component logs
board.sw.enable_logs("WiFi", "enable")

# Capture logs
logs = board.sw.get_board_logs(timeout=5)
boot_logs = board.sw.get_boottime_log()
tr069_logs = board.sw.get_tr069_log()
```

### Console Access
```python
# Direct console commands
console = board.hw.get_console("console")
output = console.execute_command("cat /proc/meminfo")
```

---

## Access Patterns Summary

| Component | Access Pattern | Example |
|-----------|---------------|---------|
| System Info | `board.sw.method()` | `board.sw.get_seconds_uptime()` |
| Network Utils | `board.sw.nw_utility.method()` | `board.sw.nw_utility.netstat()` |
| Firewall | `board.sw.firewall.method()` | `board.sw.firewall.get_iptables_list()` |
| DMCLI | `board.sw.dmcli.method()` | `board.sw.dmcli.GPV("param")` |
| WiFi | `board.sw.wifi.method()` | `board.sw.wifi.get_ssid()` |
| Console | `board.hw.get_console().method()` | `console.execute_command("cmd")` |

---

## Common Parameter Types

- **interface**: Network interface name (e.g., "erouter0", "brlan0", "wlan0")
- **network_type**: WiFi network type - "private", "guest", "community"
- **band**: WiFi band - "2.4", "5" (GHz)
- **timeout**: Time in seconds (int)
- **method**: Reset method string
- **component**: Component name (e.g., "WiFi", "TR69")
- **action**: Operation type - "upload"/"download", "get"/"put"
