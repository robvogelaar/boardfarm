# RDKB Tests

This directory contains test files for RDK-B (Reference Design Kit - Broadband) devices, specifically targeting Raspberry Pi 4 boards running RDK-B firmware.

## Installation

### Initial Setup

Create a development environment and install boardfarm with pytest plugin:

```bash
mkdir boardfarm-open-dev3
cd boardfarm-open-dev3

python3.13 -m venv --prompt bf-venv venv
source venv/bin/activate
pip install --upgrade pip wheel

git clone https://github.com/robvogelaar/boardfarm
cd boardfarm
pip install -e .[doc,dev,test]
cd ..

git clone https://github.com/robvogelaar/pytest-boardfarm
cd pytest-boardfarm
pip install -e .[doc,dev,test]
cd ..
```

### Verify Installation

After installation, verify you're in the boardfarm directory:

```bash
cd boardfarm
```

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
- **test_wifi_operations.py** - WiFi HAL operations

## Connection Types

### Serial Connection

Uses a serial port connection (e.g., via picocom) to communicate with the device.

#### Verify Serial Access

First, check that you can connect to the device via serial:

```bash
picocom -b 115200 /dev/ttyUSB0
```

Verify the prompt matches the expected format:
```
root@RaspberryPi-Gateway:~#
```

Press `Ctrl-A` then `Ctrl-X` to exit picocom.

#### Run Tests with Serial Connection

```bash
pytest \
    -s \
    --disable-warnings \
    --board-name rpi4-rdkb-1 \
    --env-config ./boardfarm3/configs/boardfarm_env_rpi4rdkb.json \
    --inventory-config ./boardfarm3/configs/boardfarm_inv_rpi4rdkb_serial.json \
    --skip-boot \
    ./tests/rdkb/test_rpi4_basic.py
```

### SSH Connection

Uses SSH to communicate with the device.

#### Verify SSH Access

First, check that you can connect to the device via SSH:

```bash
ssh root@192.168.2.111
```

If successful, exit the SSH session and update the IP address in the inventory config:

```bash
# Edit the SSH inventory config file
vim ./boardfarm3/configs/boardfarm_inv_rpi4rdkb_ssh.json
```

Update the `ipaddr` field to match your device's IP address.

#### Run Tests with SSH Connection

```bash
pytest \
    -s \
    --disable-warnings \
    --board-name rpi4-rdkb-1 \
    --env-config ./boardfarm3/configs/boardfarm_env_rpi4rdkb.json \
    --inventory-config ./boardfarm3/configs/boardfarm_inv_rpi4rdkb_ssh.json \
    --skip-boot \
    ./tests/rdkb/test_rpi4_basic.py
```

## Common Options

- `-s` - Show output (don't capture stdout)
- `--disable-warnings` - Suppress pytest warnings
- `--board-name` - Name of the board from inventory config
- `--skip-boot` - Skip device boot sequence (device already running)
- `--env-config` - Path to environment configuration file
- `--inventory-config` - Path to inventory configuration file

## Running All Tests

Run all RDKB tests:

```bash
# Serial connection
pytest \
    -s \
    --disable-warnings \
    --board-name rpi4-rdkb-1 \
    --env-config ./boardfarm3/configs/boardfarm_env_rpi4rdkb.json \
    --inventory-config ./boardfarm3/configs/boardfarm_inv_rpi4rdkb_serial.json \
    --skip-boot \
    ./tests/rdkb/

# SSH connection
pytest \
    -s \
    --disable-warnings \
    --board-name rpi4-rdkb-1 \
    --env-config ./boardfarm3/configs/boardfarm_env_rpi4rdkb.json \
    --inventory-config ./boardfarm3/configs/boardfarm_inv_rpi4rdkb_ssh.json \
    --skip-boot \
    ./tests/rdkb/
```

## Running Specific Tests

Run a specific test file:
```bash
pytest \
    -s \
    --disable-warnings \
    --board-name rpi4-rdkb-1 \
    --env-config ./boardfarm3/configs/boardfarm_env_rpi4rdkb.json \
    --inventory-config ./boardfarm3/configs/boardfarm_inv_rpi4rdkb_ssh.json \
    --skip-boot \
    ./tests/rdkb/test_network_interfaces.py
```

Run a specific test function:
```bash
pytest \
    -s \
    --disable-warnings \
    --board-name rpi4-rdkb-1 \
    --env-config ./boardfarm3/configs/boardfarm_env_rpi4rdkb.json \
    --inventory-config ./boardfarm3/configs/boardfarm_inv_rpi4rdkb_ssh.json \
    --skip-boot \
    ./tests/rdkb/test_process_management.py::test_get_process_count
```

## Configuration Files

### Serial Connection Configuration

**Inventory Config** (`boardfarm_inv_rpi4rdkb_serial.json`):
```json
{
    "rpi4-rdkb-1": {
        "devices": [
            {
                "conn_cmd": [
                    "picocom -b 115200 /dev/ttyUSB0"
                ],
                "connection_type": "serial",
                "name": "board",
                "type": "bf_rpi4rdkb"
            }
        ]
    }
}
```

**Required fields for serial:**
- `conn_cmd`: Array with serial connection command (update `/dev/ttyUSB0` to match your serial device)
- `connection_type`: `"serial"`
- `name`: Device identifier (must be `"board"`)
- `type`: Device type (`"bf_rpi4rdkb"`)

### SSH Connection Configuration

**Inventory Config** (`boardfarm_inv_rpi4rdkb_ssh.json`):
```json
{
    "rpi4-rdkb-1": {
        "devices": [
            {
                "connection_type": "ssh_connection",
                "ipaddr": "192.168.2.111",
                "port": 22,
                "username": "root",
                "name": "board",
                "type": "bf_rpi4rdkb"
            }
        ]
    }
}
```

**Required fields for SSH:**
- `connection_type`: `"ssh_connection"` (for key-based auth) or `"authenticated_ssh"` (for password-based auth)
- `ipaddr`: IP address of the device (update this to match your device)
- `port`: SSH port (typically 22)
- `username`: SSH username (typically `"root"`)
- `name`: Device identifier (must be `"board"`)
- `type`: Device type (`"bf_rpi4rdkb"`)

**Optional fields:**
- `password`: SSH password (only needed if using `"authenticated_ssh"` connection type)

### Environment Configuration

**Environment Config** (`boardfarm_env_rpi4rdkb.json` - same for both serial and SSH):
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

## Troubleshooting

### Serial Connection Issues

- Ensure `/dev/ttyUSB0` (or your serial device) has proper permissions: `sudo chmod 666 /dev/ttyUSB0`
- Verify the device is connected and the serial port is correct: `ls -l /dev/ttyUSB*`
- Check the baud rate matches your device (115200 is standard for RDK-B)

### SSH Connection Issues

- Verify the IP address is correct and reachable: `ping 192.168.2.111`
- Ensure SSH key is set up or use `authenticated_ssh` with password
- Check SSH service is running on the device
- Verify firewall rules allow SSH connections

### Test Failures

- Some tests may be skipped if certain features are not available (e.g., SNMP, IPv6)
- Use `-v` or `-vv` flags for more verbose output
- Check device logs for any error messages during test execution
