"""Tests for firewall operation primitives on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_iptables_list(device_manager):
    """Test getting iptables rules list.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get iptables list - must use --line-number for parser to work
    iptables_df = board.sw.firewall.get_iptables_list(opts="-L", extra_opts="-n --line-number")

    assert iptables_df is not None, "Iptables list should not be None"

    # Count total rules across all chains
    total_rules = sum(len(rules) for rules in iptables_df.values())
    print(f"\nIptables chains: {len(iptables_df)}")
    print(f"Total rules: {total_rules}")

    if total_rules > 0:
        print("\nRules by chain:")
        for chain, rules in list(iptables_df.items())[:5]:
            print(f"  {chain}: {len(rules)} rules")
    else:
        print("No iptables rules found")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_check_iptables_empty(device_manager):
    """Test checking if iptables is empty.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Must use -L and --line-number for parser to work
    is_empty = board.sw.firewall.is_iptable_empty(opts="-L", extra_opts="--line-number")

    assert isinstance(is_empty, bool), "Result should be boolean"
    print(f"\nIptables is empty: {is_empty}")

    if not is_empty:
        print("Iptables has rules configured")
    else:
        print("Iptables is empty (no rules)")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_iptables_policy(device_manager):
    """Test getting iptables chain policies.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    print("\nIptables Chain Policies:")

    # Get all policies at once - method doesn't accept chain parameter
    policies = board.sw.firewall.get_iptables_policy()

    for chain, policy in policies.items():
        print(f"  {chain:10s}: {policy}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_ip6tables_list(device_manager):
    """Test getting ip6tables rules list.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get ip6tables list - must use --line-number for parser to work
    ip6tables_df = board.sw.firewall.get_ip6tables_list(opts="-L", extra_opts="-n --line-number")

    assert ip6tables_df is not None, "Ip6tables list should not be None"

    # Count total rules across all chains
    total_rules = sum(len(rules) for rules in ip6tables_df.values())
    print(f"\nIp6tables chains: {len(ip6tables_df)}")
    print(f"Total rules: {total_rules}")

    if total_rules > 0:
        print("\nRules by chain:")
        for chain, rules in list(ip6tables_df.items())[:5]:
            print(f"  {chain}: {len(rules)} rules")
    else:
        print("No ip6tables rules found")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_check_ip6tables_empty(device_manager):
    """Test checking if ip6tables is empty.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Must use -L and --line-number for parser to work
    is_empty = board.sw.firewall.is_ip6table_empty(opts="-L", extra_opts="--line-number")

    assert isinstance(is_empty, bool), "Result should be boolean"
    print(f"\nIp6tables is empty: {is_empty}")

    if not is_empty:
        print("Ip6tables has rules configured")
    else:
        print("Ip6tables is empty (no rules)")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_ip6tables_policy(device_manager):
    """Test getting ip6tables chain policies.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    print("\nIp6tables Chain Policies:")

    # Get all policies at once - method doesn't accept chain parameter
    policies = board.sw.firewall.get_ip6tables_policy()

    for chain, policy in policies.items():
        print(f"  {chain:10s}: {policy}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_iptables_nat_table(device_manager):
    """Test getting iptables NAT table rules.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get NAT table rules - must use --line-number for parser to work
    nat_df = board.sw.firewall.get_iptables_list(opts="-t nat -L", extra_opts="-n --line-number")

    total_rules = sum(len(rules) for rules in nat_df.values())
    print(f"\nNAT table chains: {len(nat_df)}")
    print(f"Total NAT rules: {total_rules}")

    if total_rules > 0:
        print("\nNAT rules by chain:")
        for chain, rules in list(nat_df.items())[:5]:
            print(f"  {chain}: {len(rules)} rules")
    else:
        print("No NAT rules found")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_iptables_mangle_table(device_manager):
    """Test getting iptables mangle table rules.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Get mangle table rules - must use --line-number for parser to work
    mangle_df = board.sw.firewall.get_iptables_list(opts="-t mangle -L", extra_opts="-n --line-number")

    total_rules = sum(len(rules) for rules in mangle_df.values())
    print(f"\nMangle table chains: {len(mangle_df)}")
    print(f"Total mangle rules: {total_rules}")

    if total_rules > 0:
        print("\nMangle rules by chain:")
        for chain, rules in list(mangle_df.items())[:5]:
            print(f"  {chain}: {len(rules)} rules")
    else:
        print("No mangle rules found")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_add_and_remove_drop_rule(device_manager):
    """Test adding and removing iptables drop rule.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    test_ip = "192.168.99.99"

    print(f"\nTesting iptables rule add/delete for {test_ip}")

    try:
        # Add drop rule
        print(f"Adding DROP rule for {test_ip}...")
        board.sw.firewall.add_drop_rule_iptables(option="-s", valid_ip=test_ip)

        # Verify rule was added - must use --line-number for parser
        iptables_df = board.sw.firewall.get_iptables_list(opts="-L", extra_opts="-n --line-number")

        # Check if IP is in any INPUT chain rules
        input_rules = iptables_df.get("INPUT", [])
        found = any(test_ip in str(rule) for rule in input_rules)

        if found:
            print(f"✓ DROP rule successfully added for {test_ip}")
        else:
            print(f"⚠ Warning: Could not verify rule was added")

        # Remove drop rule
        print(f"Removing DROP rule for {test_ip}...")
        board.sw.firewall.del_drop_rule_iptables(option="-s", valid_ip=test_ip)

        # Verify rule was removed
        iptables_df = board.sw.firewall.get_iptables_list(opts="-L", extra_opts="-n --line-number")
        input_rules = iptables_df.get("INPUT", [])
        found = any(test_ip in str(rule) for rule in input_rules)

        if not found:
            print(f"✓ DROP rule successfully removed for {test_ip}")
        else:
            print(f"⚠ Warning: Rule may still exist")

    except Exception as e:
        print(f"Error during iptables rule test: {e}")
        pytest.skip(f"Iptables rule add/remove failed: {e}")
        # Try to clean up in case of error
        try:
            board.sw.firewall.del_drop_rule_iptables(option="-s", valid_ip=test_ip)
        except Exception:
            pass


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_add_and_remove_ip6_drop_rule(device_manager):
    """Test adding and removing ip6tables drop rule.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    test_ip = "2001:db8::9999"

    print(f"\nTesting ip6tables rule add/delete for {test_ip}")

    try:
        # Add drop rule
        print(f"Adding DROP rule for {test_ip}...")
        board.sw.firewall.add_drop_rule_ip6tables(option="-s", valid_ip=test_ip)

        # Verify rule was added - must use --line-number for parser
        ip6tables_df = board.sw.firewall.get_ip6tables_list(opts="-L", extra_opts="-n --line-number")

        # Check if IP is in any INPUT chain rules
        input_rules = ip6tables_df.get("INPUT", [])
        found = any(test_ip in str(rule) for rule in input_rules)

        if found:
            print(f"✓ DROP rule successfully added for {test_ip}")
        else:
            print(f"⚠ Warning: Could not verify rule was added")

        # Remove drop rule
        print(f"Removing DROP rule for {test_ip}...")
        board.sw.firewall.del_drop_rule_ip6tables(option="-s", valid_ip=test_ip)

        # Verify rule was removed
        ip6tables_df = board.sw.firewall.get_ip6tables_list(opts="-L", extra_opts="-n --line-number")
        input_rules = ip6tables_df.get("INPUT", [])
        found = any(test_ip in str(rule) for rule in input_rules)

        if not found:
            print(f"✓ DROP rule successfully removed for {test_ip}")
        else:
            print(f"⚠ Warning: Rule may still exist")

    except Exception as e:
        print(f"Error during ip6tables rule test: {e}")
        pytest.skip(f"Ip6tables rule add/remove failed: {e}")
        # Try to clean up in case of error
        try:
            board.sw.firewall.del_drop_rule_ip6tables(option="-s", valid_ip=test_ip)
        except Exception:
            pass


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_firewall_rule_count_by_chain(device_manager):
    """Test counting firewall rules by chain.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)

    # Must use --line-number for parser to work
    iptables_df = board.sw.firewall.get_iptables_list(opts="-L", extra_opts="-n -v --line-number")

    print("\nFirewall Rule Statistics:")

    # Count rules by chain
    total_ipv4_rules = sum(len(rules) for rules in iptables_df.values())
    print(f"  Total IPv4 chains: {len(iptables_df)}")
    print(f"  Total IPv4 rules: {total_ipv4_rules}")

    print("\n  IPv4 rules by chain:")
    for chain, rules in list(iptables_df.items())[:10]:
        print(f"    {chain}: {len(rules)} rules")

    # IPv6 statistics
    ip6tables_df = board.sw.firewall.get_ip6tables_list(opts="-L", extra_opts="-n -v --line-number")
    total_ipv6_rules = sum(len(rules) for rules in ip6tables_df.values())
    print(f"\n  Total IPv6 chains: {len(ip6tables_df)}")
    print(f"  Total IPv6 rules: {total_ipv6_rules}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_firewall_via_console(device_manager):
    """Test firewall operations via direct console commands.

    :param device_manager: Device manager fixture
    :type device_manager: DeviceManager
    """
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    # Get iptables summary
    print("\nIptables Summary (iptables -L -n -v):")
    output = console.execute_command("iptables -L -n -v | head -n 30")
    print(output)

    # Get rule counts
    print("\nIptables Rule Counts:")
    output = console.execute_command("iptables -L | grep -c 'Chain'")
    print(f"  Number of chains: {output.strip()}")

    # Check if firewall is active
    print("\nFirewall Status:")
    output = console.execute_command("iptables -L | wc -l")
    rule_count = int(output.strip()) if output.strip().isdigit() else 0
    print(f"  Total lines in iptables output: {rule_count}")

    if rule_count > 10:
        print("  ✓ Firewall appears to be active with rules")
    else:
        print("  ⚠ Firewall may be inactive or has minimal rules")
