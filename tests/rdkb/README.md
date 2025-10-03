# RDKB Tests

This directory contains test files for RDK-B (Reference Design Kit - Broadband) devices, specifically targeting Raspberry Pi 4 boards running RDK-B firmware.

## Test Categories

- **test_rpi4_basic.py** - Basic RPI4 device connectivity
- **test_system_information.py** - System info, uptime, memory, CPU
- **test_process_management.py** - Process listing, monitoring, and management
- **test_network_interfaces.py** - Network interface configuration and status
- **test_network_utilities.py** - Network utilities (ping, traceroute, etc.)
- **test_dmcli.py** - DMCLI (Data Model CLI) basic operations
- **test_dmcli_advanced.py** - Advanced DMCLI operations
- **test_firewall_operations.py** - Firewall rules and configuration
- **test_logging_events.py** - Log retrieval and monitoring
- **test_advanced_logging.py** - Advanced logging primitives
- **test_time_management.py** - Time/date management and NTP
- **test_dns_operations.py** - DNS configuration and queries
- **test_http_operations.py** - HTTP client operations
- **test_file_transfer.py** - SCP/TFTP file transfers
- **test_tr069_status.py** - TR-069 agent status and operations
- **test_snmp_operations.py** - SNMP operations

## Connection Types

### Serial Connection

Uses a serial port connection (e.g., via picocom) to communicate with the device.

**Example:**
```bash
pytest -s --disable-warnings \
    --board-name rpi4-rdkb-1 \
    --skip-boot \
    --ignore-devices="acs_server,lan2,wan,provisioner,lan" \
    --env-config ./boardfarm3/configs/boardfarm_env_rpi4rdkb_example.json \
    --inventory-config ./boardfarm3/configs/boardfarm_rpi4rdkb_config_example.json \
    ./tests/rdkb/test_process_management.py
```

### SSH Connection

Uses SSH (key-based authentication) to communicate with the device.

**Example:**
```bash
pytest -s --disable-warnings \
    --board-name rpi4-rdkb-ssh \
    --skip-boot \
    --ignore-devices="acs_server,lan2,wan,provisioner,lan" \
    --env-config ./boardfarm3/configs/boardfarm_env_rpi4rdkb_ssh.json \
    --inventory-config ./boardfarm3/configs/boardfarm_rpi4rdkb_ssh_config.json \
    ./tests/rdkb/test_process_management.py
```

## Common Options

- `-s` - Show output (don't capture stdout)
- `--disable-warnings` - Suppress pytest warnings
- `--board-name` - Name of the board from inventory config
- `--skip-boot` - Skip device boot sequence (device already running)
- `--ignore-devices` - Comma-separated list of devices to ignore
- `--env-config` - Path to environment configuration file
- `--inventory-config` - Path to inventory configuration file

## Running All Tests

Run all RDKB tests:
```bash
pytest -s --disable-warnings \
    --board-name rpi4-rdkb-ssh \
    --skip-boot \
    --ignore-devices="acs_server,lan2,wan,provisioner,lan" \
    --env-config ./boardfarm3/configs/boardfarm_env_rpi4rdkb_ssh.json \
    --inventory-config ./boardfarm3/configs/boardfarm_rpi4rdkb_ssh_config.json \
    ./tests/rdkb/
```

## Running Specific Tests

Run a specific test file:
```bash
pytest ./tests/rdkb/test_network_interfaces.py [options...]
```

Run a specific test function:
```bash
pytest ./tests/rdkb/test_process_management.py::test_find_specific_process [options...]
```

## Configuration Files

### Serial Connection Configuration

**Inventory Config** (`boardfarm_rpi4rdkb_config_example.json`):
```json
{
    "rpi4-rdkb-1": {
        "devices": [
            {
                "conn_cmd": ["picocom -b 115200 /dev/ttyUSB0"],
                "connection_type": "serial",
                "gui_password": "admin",
                "mac": "dc:a6:32:25:8f:e0",
                "name": "board",
                "type": "bf_rpi4rdkb"
            }
        ]
    }
}
```

**Key fields for serial:**
- `connection_type`: `"serial"`
- `conn_cmd`: Array with serial connection command (e.g., picocom)
- `name`: Device identifier (must be `"board"`)
- `type`: Device type (`"bf_rpi4rdkb"`)
- `gui_password`: Password for web GUI (optional)
- `mac`: Device MAC address (optional)

### SSH Connection Configuration

**Inventory Config** (`boardfarm_rpi4rdkb_ssh_config.json`):
```json
{
    "rpi4-rdkb-ssh": {
        "devices": [
            {
                "connection_type": "ssh_connection",
                "ipaddr": "192.168.2.109",
                "port": 22,
                "username": "root",
                "gui_password": "admin",
                "name": "board",
                "type": "bf_rpi4rdkb"
            }
        ]
    }
}
```

**Key fields for SSH:**
- `connection_type`: `"ssh_connection"` (key-based) or `"authenticated_ssh"` (password-based)
- `ipaddr`: IP address of the device
- `port`: SSH port (typically 22)
- `username`: SSH username (typically `"root"`)
- `password`: SSH password (only for `"authenticated_ssh"`, omit for key-based auth)
- `name`: Device identifier (must be `"board"`)
- `type`: Device type (`"bf_rpi4rdkb"`)

### Environment Configuration

**Environment Config** (same for both serial and SSH):
```json
{
    "environment_def": {
        "board": {
            "model": "bf_rpi4rdkb"
        }
    }
}
```

This defines the expected device model for test environment requirements.
