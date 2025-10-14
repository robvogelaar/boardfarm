"""Tests for firewall operations (iptables/ip6tables) on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_iptables_list(device_manager):
    board = device_manager.get_device_by_type(CPE)

    rules = board.sw.firewall.get_iptables_list("", "INPUT")

    print(f"\nIPv4 Firewall Rules (filter/INPUT):")
    print(f"  Total chains: {len(rules)}")
    for chain_name, chain_rules in rules.items():
        print(f"  {chain_name}: {len(chain_rules)} rules")
        for i, rule in enumerate(chain_rules[:3], 1):
            print(f"    {i}. {rule}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_check_iptables_empty(device_manager):
    board = device_manager.get_device_by_type(CPE)

    is_empty = board.sw.firewall.is_iptable_empty()

    print(f"\nIPv4 Firewall empty: {is_empty}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_iptables_policy(device_manager):
    board = device_manager.get_device_by_type(CPE)

    policies = board.sw.firewall.get_iptables_policy("")

    print(f"\nIPv4 Firewall Policies (filter):")
    for chain, policy in policies.items():
        print(f"  {chain}: {policy}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_ip6tables_list(device_manager):
    board = device_manager.get_device_by_type(CPE)

    rules = board.sw.firewall.get_ip6tables_list("", "INPUT")

    print(f"\nIPv6 Firewall Rules (filter/INPUT):")
    print(f"  Total rules: {len(rules)}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_check_ip6tables_empty(device_manager):
    board = device_manager.get_device_by_type(CPE)

    is_empty = board.sw.firewall.is_ip6table_empty()

    print(f"\nIPv6 Firewall empty: {is_empty}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_get_ip6tables_policy(device_manager):
    board = device_manager.get_device_by_type(CPE)

    policies = board.sw.firewall.get_ip6tables_policy("")

    print(f"\nIPv6 Firewall Policies (filter):")
    for chain, policy in policies.items():
        print(f"  {chain}: {policy}")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_add_and_remove_drop_rule(device_manager):
    board = device_manager.get_device_by_type(CPE)

    test_ip = "192.168.99.99"
    print(f"\nTesting IPv4 firewall rule add/delete for {test_ip}")

    board.sw.firewall.add_drop_rule_iptables("src", test_ip)
    print("  OK Added drop rule")

    rules = board.sw.firewall.get_iptables_list("", "INPUT")
    found = any(test_ip in str(rule) for chain_rules in rules.values() for rule in chain_rules)
    if found:
        print(f"  OK Rule found in iptables")

    board.sw.firewall.del_drop_rule_iptables("src", test_ip)
    print("  OK Removed drop rule")


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_add_and_remove_ip6_drop_rule(device_manager):
    board = device_manager.get_device_by_type(CPE)

    test_ip = "2001:db8::99"
    print(f"\nTesting IPv6 firewall rule add/delete for {test_ip}")

    board.sw.firewall.add_drop_rule_ip6tables("src", test_ip)
    print("  OK Added drop rule")

    board.sw.firewall.del_drop_rule_ip6tables("src", test_ip)
    print("  OK Removed drop rule")
