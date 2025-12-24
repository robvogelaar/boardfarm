"""LXD Container PDU module.

Provides power control for LXD containers by stopping and starting them.
"""

import logging
import subprocess
import time

from boardfarm3.templates.pdu import PDU

_LOGGER = logging.getLogger(__name__)


class LXDPDU(PDU):
    """PDU implementation using lxc stop/start for power control."""

    def __init__(self, uri: str) -> None:
        """Initialize LXD Container PDU instance.

        :param uri: URI containing container name
        :type uri: str
        """
        self._container_name = uri.strip()
        _LOGGER.info("LXD PDU initialized for container: %s", self._container_name)

    def _run_command(
        self, cmd: list[str], timeout: int = 60, check: bool = True
    ) -> tuple[bool, str, str]:
        """Run a shell command and return results."""
        _LOGGER.debug("Running command: %s", " ".join(cmd))

        try:
            result = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            if result.returncode != 0 and check:
                _LOGGER.error(
                    "Command failed: %s (exit %d): %s",
                    " ".join(cmd),
                    result.returncode,
                    result.stderr,
                )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            _LOGGER.exception("Command timed out: %s", " ".join(cmd))
            return False, "", "Command timed out"
        except (subprocess.SubprocessError, OSError) as e:
            _LOGGER.exception("Command error: %s", " ".join(cmd))
            return False, "", str(e)

    def _get_container_status(self) -> str:
        """Get the current status of the container."""
        success, output, _ = self._run_command(
            ["lxc", "list", self._container_name, "--format", "csv", "-c", "s"],
            check=False,
        )
        if success and output:
            return output.strip()
        return ""

    def _wait_for_status(
        self, target_status: str, timeout: int = 60, poll_interval: int = 2
    ) -> bool:
        """Wait for container to reach target status."""
        elapsed = 0
        while elapsed < timeout:
            status = self._get_container_status()
            if status.upper() == target_status.upper():
                return True
            time.sleep(poll_interval)
            elapsed += poll_interval
        return False

    def power_off(self) -> bool:
        """Stop the LXD container (power OFF)."""
        _LOGGER.info("Stopping LXD container: %s", self._container_name)

        status = self._get_container_status()
        if status.upper() == "STOPPED":
            _LOGGER.info("Container %s is already stopped", self._container_name)
            return True

        success, _, _ = self._run_command(
            ["lxc", "stop", self._container_name, "--force"]
        )
        if not success:
            return False

        if self._wait_for_status("STOPPED", timeout=30):
            _LOGGER.info("Container %s stopped successfully", self._container_name)
            return True
        _LOGGER.error("Container %s did not stop in time", self._container_name)
        return False

    def power_on(self) -> bool:
        """Start the LXD container (power ON)."""
        _LOGGER.info("Starting LXD container: %s", self._container_name)

        status = self._get_container_status()
        if status.upper() == "RUNNING":
            _LOGGER.info("Container %s is already running", self._container_name)
            return True

        success, _, _ = self._run_command(["lxc", "start", self._container_name])
        if not success:
            return False

        if self._wait_for_status("RUNNING", timeout=30):
            _LOGGER.info("Container %s started successfully", self._container_name)
            return True
        _LOGGER.error("Container %s did not start in time", self._container_name)
        return False

    def power_cycle(self) -> bool:
        """Power cycle the LXD container (stop, wait, start)."""
        _LOGGER.info("Power cycling LXD container: %s", self._container_name)

        if not self.power_off():
            _LOGGER.error("Failed to stop container during power cycle")
            return False

        time.sleep(5)  # power-off delay

        if not self.power_on():
            _LOGGER.error("Failed to start container during power cycle")
            return False

        _LOGGER.info("Container %s power cycled successfully", self._container_name)
        return True
