# Boardfarm Test Framework Architecture Documentation

## Table of Contents

- [Executive Summary](#executive-summary)
- [Core Architecture Principles](#core-architecture-principles)
- [Test Suite Organization](#test-suite-organization)
- [Use Case Libraries](#use-case-libraries)
- [Test Execution Framework](#test-execution-framework)
- [Key Architectural Benefits](#benefits)
- [Performance Metrics](#performance)
- [Integration Capabilities](#integration)
- [Future Architecture Evolution](#future)

## Executive Summary

**Boardfarm** is an enterprise-grade, open-source test automation framework designed for comprehensive testing of cable modems, gateways, and telecommunications infrastructure. The framework implements a **"build once, use many times"** philosophy through sophisticated abstraction layers, enabling the same test suite to execute across diverse hardware vendors, deployment environments, and network configurations.

## Core Architecture Principles

### 1. Multi-Layer Abstraction Architecture

The framework achieves universal test portability through five key architectural layers:

```
┌─────────────────────────────────────────────┐
│           Test Cases (1,336+ tests)         │
├─────────────────────────────────────────────┤
│         Use Cases (Reusable Blocks)         │
├─────────────────────────────────────────────┤
│      Pytest Fixtures (Device Manager)       │
├─────────────────────────────────────────────┤
│    Device Templates (Abstract Interfaces)   │
├─────────────────────────────────────────────┤
│   Vendor Plugins (Concrete Implementations) │
└─────────────────────────────────────────────┘
```

#### Layer 1: Device Templates (Abstract Base Classes)

Located in `boardfarm/boardfarm3/templates/`, these define standardized interfaces:

- `CableModem` - Cable modem operations
- `CMTS` - Cable Modem Termination System
- `CoreRouter` - Core routing functionality
- `WAN/LAN` - Network interface abstractions
- `SIPPhone/SIPServer` - Voice infrastructure
- `ACS` - Auto Configuration Server (TR-069)
- `Provisioner` - Device provisioning services

#### Layer 2: Pytest Integration Layer

The `pytest-boardfarm` package provides dynamic device resolution:

- **device_manager fixture**: Resolves abstract device types to concrete implementations at runtime
- **boardfarm_config fixture**: Manages environment configuration
- **bf_context fixture**: Stores test execution context
- **bf_logger fixture**: Provides standardized logging

#### Layer 3: Plugin Architecture

Vendor-specific implementations register as plugins using Pluggy:

- `boardfarm-sagemcom` - Sagemcom device implementations
- `boardfarm-docsis` - DOCSIS-specific functionality
- `boardfarm-lgi-shared` - Liberty Global shared components
- Custom vendor plugins can be added without modifying core framework

#### Layer 4: Use Cases Layer

Reusable test building blocks organized by functionality domain:

- **Core Operations**: Device management, provisioning, health checks
- **Network Services**: DHCP, DNS, routing, multicast
- **Voice Services**: VoIP registration, call handling, SIP operations
- **Management Protocols**: TR-069, SNMP, telemetry
- **Performance Testing**: iPerf, traffic generation, load testing

#### Layer 5: Test Cases

Over 1,336 test cases organized by functional area, all using abstract interfaces.

### 2. Environment Diversity Support

The framework seamlessly adapts to multiple deployment scenarios:

```
Physical Lab Setup:
  - Real hardware devices (CPE, CMTS, switches)
  - Physical network connections
  - Hardware-specific testing

Virtual/Containerized Setup:
  - Docker-based virtual CPEs
  - QEMU device emulation
  - Containerized services (ACS, DHCP, DNS)

Hybrid Setup:
  - Physical CPE with virtual services
  - Remote customer site testing
  - Cloud service integration

Scale Configurations:
  - Desktop: i5 PC, 16GB RAM (1 CPE)
  - Rack: Dell R650, 256GB RAM (16 CPEs)
  - Cloud: Unlimited scaling with containers
```

## Test Suite Organization

### Test Categories and Distribution

| Metric | Count |
|--------|-------|
| **Total Test Files** | 1,336 |
| **TR-069 Tests** | 494 |
| **GUI Tests** | 363 |
| **Voice Tests** | 67 |

### Major Test Categories

| Category | Count | Description | Location |
|----------|-------|-------------|----------|
| **TR-069** | 494 | Device management protocol tests | `tests/tr069/` |
| **GUI** | 363 | Web interface automation | `tests/gui/` |
| **Root Level** | 270 | Core functionality & integration | `tests/` |
| **Voice** | 67 | VoIP and telephony | `tests/voice/` |
| **Telemetry** | 44 | Data collection & reporting | `tests/telemetry/` |
| **SW Update** | 37 | Firmware upgrade/downgrade | `tests/sw_update/` |
| **SSAM** | 21 | Service assurance | `tests/ssam/` |
| **Reverse SSH** | 15 | Remote access testing | `tests/reverse_ssh/` |
| **Stability** | 10 | Long-running stability tests | `tests/stability/` |
| **SamKnows** | 7 | Speed test integration | `tests/samknows/` |
| **WiFi** | 5 | Wireless functionality | `tests/wifi/` |
| **RIPv2** | 3 | Routing protocol tests | `tests/ripv2/` |

### Voice Test Subcategories

| Subcategory | Count | Focus Area |
|-------------|-------|------------|
| Basic Call | 35 | Call establishment and teardown |
| Registration | 14 | SIP registration scenarios |
| Call Hold | 5 | Hold/resume functionality |
| Call Waiting | 4 | Multiple call handling |
| Authentication | 2 | SIP authentication |

### Test Naming Conventions

- **MVX_TST-{ID}**: Links tests to JIRA tickets for traceability
- **CSV Files**: Accompany tests for data-driven testing
- **Pytest Markers**: Categorize tests for selective execution

## Use Case Libraries

### Core Framework Use Cases

`boardfarm/boardfarm3/use_cases/`:

- **Device Operations**: `cpe.py`, `device_utilities.py`, `device_getters.py`
- **Network Services**: `dhcp.py`, `networking.py`, `multicast.py`
- **Performance**: `iperf.py`, `image_comparison.py`
- **Protocols**: `ripv2.py`, `wifi.py`, `voice.py`

### DOCSIS-Specific Use Cases

`boardfarm-docsis/boardfarm3_docsis/use_cases/`:

- **Cable Modem**: `docsis.py`, `connectivity.py`
- **Routing**: `erouter.py`, `net_tools.py`
- **Management**: `snmp.py`, `tr069.py`

### LGI Shared Use Cases (Most Comprehensive)

`boardfarm-lgi-shared/boardfarm3_lgi_shared/use_cases/` (29 modules):

#### Infrastructure & Provisioning

- `boot_file_helper.py` - Boot configuration management
- `provision_helper.py` - Automated provisioning workflows
- `health_check.py` - System health monitoring
- `software_update.py` - Firmware management

#### Network Technologies

- `gpon.py` - Fiber optic network operations
- `olt.py` - Optical Line Terminal management
- `tunnel_security.py` - VPN and tunnel operations
- `iproute.py` - Advanced routing configuration

#### Service Features

- `family_time.py` - Parental control features
- `plume.py` - Cloud network management
- `sam_knows.py` - Performance measurement
- `telemetry.py` - Data collection and reporting

#### Voice & Communication

- `voice.py` - VoIP operations
- `vmb_mode.py` - Voice message box functionality

## Test Execution Framework

### Pytest Integration

The framework leverages pytest's powerful features:

```python
# Test Environment Requirements
@pytest.mark.env_req({
    "board": {
        "eRouter_Provisioning_mode": ["ipv4", "ipv6"],
        "model": ["TG2492LG", "CH7465LG", "TG3492LG", "F3896LG"]
    }
})

# Test Markers for Categorization
@pytest.mark.gui          # GUI automation tests
@pytest.mark.voice        # Voice functionality
@pytest.mark.release3     # Release-specific tests
@pytest.mark.stability    # Long-running tests
```

### Configuration Management

#### Environment Configuration (JSON)

```json
{
  "environment_def": {
    "board": {
      "type": "cable_modem",
      "vendor": "sagemcom",
      "model": "F3896LG",
      "capabilities": ["docsis3.1", "wifi6", "voice"]
    },
    "cmts": {
      "type": "virtual",
      "vendor": "casa_systems"
    }
  }
}
```

#### Test Execution Command

```bash
pytest \
    --board-name <cpe-name> \
    --env-config <environment.json> \
    --inventory-config <devices.json> \
    --markers "gui and not stability" \
    tests/
```

## Key Architectural Benefits

### 1. True Test Portability

- **Same test, multiple environments**: Physical, virtual, or hybrid
- **Vendor agnostic**: Tests work across Sagemcom, Broadcom, Intel, etc.
- **Configuration driven**: JSON files determine runtime behavior

### 2. Scalability

- **Desktop to datacenter**: From single device to hundreds
- **Parallel execution**: Multiple devices tested simultaneously
- **Cloud native**: Container-based scaling

### 3. Maintainability

- **Single source of truth**: One test implementation for all variants
- **Plugin isolation**: Vendor changes don't affect core tests
- **Modular design**: Easy to extend and modify

### 4. Comprehensive Coverage

- **1,336+ automated tests**: Covering all device aspects
- **Protocol support**: DOCSIS, TR-069, SNMP, SIP, HTTP(S)
- **Full stack testing**: From physical layer to application services

## Performance Metrics

| Metric | Value |
|--------|-------|
| **System Boot Time** | ~15 minutes |
| **Test Execution** | 5-10 minutes |
| **Tests per Day per CPE** | 150-200 |
| **Devices per Rack Server** | 16+ |

## Integration Capabilities

### Test Management

- JIRA integration via MVX_TST naming
- Jenkins/CI pipeline support
- HTML and XML reporting
- ELK stack for analytics

### External Tools

- **CDRouter**: Commercial test suite integration
- **SamKnows**: Speed test platform
- **Selenium**: Web UI automation
- **Docker/QEMU**: Virtualization

### Protocol Support

- **Network**: SSH, Telnet, RS232, HTTP(S)
- **Management**: TR-069, SNMP, NETCONF
- **Voice**: SIP, RTP
- **Cable**: DOCSIS 3.0/3.1

## Future Architecture Evolution

### Planned Enhancements

1. **AI/ML Integration**: Intelligent test selection and failure prediction
2. **Cloud-Native Orchestration**: Kubernetes-based deployment
3. **Digital Twin Support**: Complete virtual device simulation
4. **Enhanced Analytics**: Real-time test insights and optimization

### Extension Points

- Custom plugin development for new vendors
- Additional protocol support
- New use case libraries
- Enhanced reporting capabilities

## Conclusion

Boardfarm's architecture represents a sophisticated approach to test automation that solves the fundamental challenge of multi-vendor, multi-environment testing in telecommunications. Through its layered abstraction model, plugin architecture, and comprehensive use case libraries, it achieves true **"build once, use many times"** test portability while maintaining the flexibility to adapt to diverse deployment scenarios and evolving technology requirements.

---

*Generated from Boardfarm Test Framework Analysis | Last Updated: 2025*
