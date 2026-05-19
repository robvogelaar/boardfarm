"""SSH-based CPE console connections that proxy through a docker container.

Two connection types are provided for reaching the SSH server running on a
CPE when no direct route exists from the test host:

* ``wan_ssh`` -- proxies through ``wan-cpe<slot>`` to the CPE's wan-side
  dropbear. The CPE IP is dynamic (WAN DHCP) and is discovered at connect
  time by scanning ``wan-cpe<slot>``'s subnets in parallel and picking the
  host whose SSH banner advertises dropbear (the lab's other hosts --
  provisioner, ACS, oktopus, etc. -- all run OpenSSH, so dropbear uniquely
  identifies the CPE).
* ``lan_ssh`` -- proxies through ``lan-cpe<slot>`` to the CPE's lan-side
  dropbear. The CPE LAN IP comes from an explicit ``ipaddr`` kwarg or
  is auto-discovered from ``lan-cpe<slot>``'s IPv4 default gateway.

Both classes inherit from :class:`SSHConnection` to reuse its login /
execute machinery, but bypass its ``__init__`` because they need to inject
an extra ``-o ProxyCommand=`` arg into the ssh invocation.
"""

from __future__ import annotations

import logging
import shlex
import subprocess
from typing import Any

from boardfarm3.exceptions import BoardfarmException
from boardfarm3.lib.boardfarm_pexpect import BoardfarmPexpect
from boardfarm3.lib.connections.ssh_connection import SSHConnection

_LOGGER = logging.getLogger(__name__)

_DEFAULT_USERNAME = "root"
_DEFAULT_PASSWORD = ""  # dropbear -B (blank-password root) on the CPE
_DEFAULT_PORT = 22
_WAN_SCAN_TIMEOUT = 6  # seconds budgeted for the parallel banner scan


def _ssh_args(username: str, ip: str, port: int, proxy_cmd: str) -> list[str]:
    return [
        f"{username}@{ip}",
        f"-p {port}",
        "-o StrictHostKeyChecking=no",
        "-o UserKnownHostsFile=/dev/null",
        "-o ServerAliveInterval=60",
        "-o ServerAliveCountMax=10",
        "-o IdentitiesOnly=yes",
        "-o HostKeyAlgorithms=+ssh-rsa",
        "-o PreferredAuthentications=password",
        "-o PubkeyAuthentication=no",
        f"-o ProxyCommand={proxy_cmd}",
    ]


def discover_cpe_wan_ip(container: str, port: int = _DEFAULT_PORT) -> str:
    """Find the CPE's WAN IP from inside *container* by SSH banner sniffing.

    Scans every IPv4 /N subnet attached to non-loopback interfaces in
    parallel, opens TCP *port* on each candidate host, reads the first line
    of its SSH banner, and returns the IP of the host that advertises
    dropbear. The lab's other hosts (provisioner, ACS, oktopus, lan/wan
    containers, ...) all run OpenSSH, so a dropbear banner uniquely
    identifies the CPE.

    Raises ``BoardfarmException`` if no dropbear responder is found.
    """
    script = (
        "set +e; "
        # For each non-loopback IPv4 address, derive the /24 prefix and the
        # container's own last octet, then scan the other 253 hosts.
        "ip -o -4 addr show | awk '$2 != \"lo\" {print $4}' | "
        "while read cidr; do "
        "  prefix=$(echo $cidr | cut -d/ -f1 | cut -d. -f1-3); "
        "  own=$(echo $cidr | cut -d/ -f1 | cut -d. -f4); "
        "  for i in $(seq 1 254); do "
        "    [ \"$i\" = \"$own\" ] && continue; "
        "    ( banner=$(echo '' | nc -w 1 ${prefix}.$i " + str(port) + " 2>/dev/null "
        "             | head -c 64); "
        "      case \"$banner\" in "
        "        *dropbear*|*Dropbear*) echo \"${prefix}.$i\" ;; "
        "      esac ) & "
        "  done; "
        "done; wait"
    )
    result = subprocess.run(  # noqa: S603
        ["docker", "exec", container, "sh", "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=_WAN_SCAN_TIMEOUT + 5,
    )
    responders = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not responders:
        msg = (
            f"no dropbear SSH responder found on any subnet visible to "
            f"{container} on port {port}; is the CPE wan-side dropbear up?"
        )
        raise BoardfarmException(msg)
    # If multiple, prefer the highest last octet (CPE typically gets a
    # DHCP-assigned address well above any static infra IPs).
    responders.sort(key=lambda ip: int(ip.split(".")[-1]))
    return responders[-1]


def resolve_lan_gateway(container: str) -> str:
    """Return the IPv4 default gateway visible from *container*.

    Convention: the LAN-side container picks up its address via the CPE's
    LAN DHCP, so its default gateway *is* the CPE's LAN IP. For cases where
    no DHCP is in play (e.g. a static-ip arrangement that doesn't add a
    default route), the caller must pass ``ipaddr`` explicitly.
    """
    result = subprocess.run(  # noqa: S603
        ["docker", "exec", container, "ip", "-4", "route", "show", "default"],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "default" and parts[1] == "via":
            return parts[2]
    msg = (
        f"no IPv4 default gateway in {container}; cannot auto-derive CPE LAN IP. "
        f"Set 'ipaddr' explicitly in inventory for lan_ssh."
    )
    raise BoardfarmException(msg)


class _DockerProxiedSSH(SSHConnection):
    """SSH via ``docker exec ... nc`` ProxyCommand.

    Bypasses :py:meth:`SSHConnection.__init__` so the args list can include
    ``-o ProxyCommand=``; the rest of SSHConnection (``login_to_server``,
    ``execute_command``, ``sudo_sendline`` …) is inherited unchanged.
    """

    def __init__(  # pylint: disable=super-init-not-called  # noqa: PLR0913
        self,
        name: str,
        ip_addr: str,
        proxy_container: str,
        shell_prompt: list[str],
        username: str = _DEFAULT_USERNAME,
        password: str = _DEFAULT_PASSWORD,
        port: int = _DEFAULT_PORT,
        save_console_logs: str = "",
        **_: Any,  # noqa: ANN401
    ) -> None:
        self._shell_prompt = shell_prompt
        self._username = username
        self._password = password if password is not None else ""
        proxy_cmd = (
            f"docker exec -i {shlex.quote(proxy_container)} "
            f"nc {shlex.quote(ip_addr)} {port}"
        )
        args = _ssh_args(username, ip_addr, port, proxy_cmd)
        _LOGGER.info(
            "SSH console %s -> %s@%s:%s via %s",
            name,
            username,
            ip_addr,
            port,
            proxy_container,
        )
        BoardfarmPexpect.__init__(self, name, "ssh", save_console_logs, args)


class WanSSHConsole(_DockerProxiedSSH):
    """SSH to the CPE's wan-side dropbear via ``wan-cpe<slot>``.

    The CPE's WAN IP is discovered at connect time by scanning the wan
    container's subnets for an SSH responder whose banner advertises
    dropbear -- see :func:`discover_cpe_wan_ip`. An explicit ``ip_addr``
    kwarg may be passed to skip discovery.
    """

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        slot: int | str,
        shell_prompt: list[str],
        ip_addr: str | None = None,
        username: str = _DEFAULT_USERNAME,
        password: str = _DEFAULT_PASSWORD,
        port: int = _DEFAULT_PORT,
        save_console_logs: str = "",
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        container = f"wan-cpe{slot}"
        resolved_ip = ip_addr if ip_addr else discover_cpe_wan_ip(container, port)
        super().__init__(
            name=name,
            ip_addr=resolved_ip,
            proxy_container=container,
            shell_prompt=shell_prompt,
            username=username,
            password=password,
            port=port,
            save_console_logs=save_console_logs,
            **kwargs,
        )


class LanSSHConsole(_DockerProxiedSSH):
    """SSH to the CPE's lan-side dropbear via ``lan-cpe<slot>``.

    The CPE's LAN IP can be supplied explicitly via ``ipaddr`` or, when
    omitted, is read from ``lan-cpe<slot>``'s IPv4 default gateway (which
    is the CPE itself when the LAN-side container picks up an address via
    the CPE's DHCP server).
    """

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        slot: int | str,
        shell_prompt: list[str],
        ip_addr: str | None = None,
        username: str = _DEFAULT_USERNAME,
        password: str = _DEFAULT_PASSWORD,
        port: int = _DEFAULT_PORT,
        save_console_logs: str = "",
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        container = f"lan-cpe{slot}"
        resolved_ip = ip_addr if ip_addr else resolve_lan_gateway(container)
        super().__init__(
            name=name,
            ip_addr=resolved_ip,
            proxy_container=container,
            shell_prompt=shell_prompt,
            username=username,
            password=password,
            port=port,
            save_console_logs=save_console_logs,
            **kwargs,
        )
