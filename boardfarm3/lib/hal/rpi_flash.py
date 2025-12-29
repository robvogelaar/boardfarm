"""RPi A/B partition flash hardware abstraction layer.

This module provides firmware flashing capabilities for RPi devices using
the A/B partition update system. The RPi SD card has two root partitions
(mmcblk0p2 and mmcblk0p3) that can alternate as the active system.

The image is expected to be available on the WAN container (10.101.0.x)
with standard credentials (root/bigfoot1). The standalone rpi_flash.py
script handles copying the image from the build server to the WAN container.

Required SD Card Layout:
    Device         Boot   Start     End Sectors  Size Id Type
    /dev/mmcblk0p1 *       8192  117249  109058 53.3M  c W95 FAT32 (LBA)
    /dev/mmcblk0p2      2097152 4194303 2097152    1G 83 Linux
    /dev/mmcblk0p3      4194304 6291455 2097152    1G 83 Linux

Flash Process:
    1. Verify A/B partitions exist
    2. Verify SD card partition layout (1GB each)
    3. Determine current and target partitions
    4. Verify target partition not mounted
    5. Verify image host access (WAN container)
    6. Flash firmware (auto-detect WIC vs raw partition)
    7. Verify flash integrity
    8. Switch boot partition
    9. Reboot and wait for device

Usage:
    from boardfarm3.lib.hal.rpi_flash import RPiFlashManager

    flasher = RPiFlashManager(console, config)
    flasher.flash(
        image="rdkb-image.wic",
        image_host="10.101.0.20",  # WAN container static IP
    )
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Optional

import pexpect

from boardfarm3.exceptions import BoardfarmException

if TYPE_CHECKING:
    from boardfarm3.lib.boardfarm_pexpect import BoardfarmPexpect

_LOGGER = logging.getLogger(__name__)

# Standard WAN container credentials
DEFAULT_IMAGE_USERNAME = "root"
DEFAULT_IMAGE_PASSWORD = "bigfoot1"
DEFAULT_IMAGE_BASE_PATH = "/tmp"


class RPiFlashManager:
    """Manages A/B partition firmware flashing for RPi devices."""

    def __init__(
        self,
        console: BoardfarmPexpect,
        config: dict,
        wan_device: Optional[object] = None,
        rpi_ip: Optional[str] = None,
    ) -> None:
        """Initialize RPi flash manager.

        :param console: Device console connection (used for reboot and fallback)
        :param config: Device configuration dictionary
        :param wan_device: Optional WAN device for SSH command execution
        :param rpi_ip: Optional RPi IP address for SSH access via WAN
        """
        self._console = console
        self._config = config
        self._wan = wan_device
        self._rpi_ip = rpi_ip

        # Get prompt from console (supports both BoardfarmPexpect and SimplePexpectWrapper)
        if hasattr(console, "prompt"):
            prompt = console.prompt
        elif hasattr(console, "_shell_prompt"):
            prompt = console._shell_prompt
        else:
            msg = "Console object must have either 'prompt' or '_shell_prompt' attribute"
            raise BoardfarmException(msg)

        # Normalize prompt to a list for consistent handling
        self._prompt_list = prompt if isinstance(prompt, list) else [prompt]

        if self._wan and self._rpi_ip:
            _LOGGER.info(f"SSH mode enabled: commands via WAN to {self._rpi_ip}")
        else:
            _LOGGER.info("Serial mode: commands via console")

    def _build_expect_patterns(self, *patterns) -> list:
        """Build expect pattern list with prompts appended."""
        return list(patterns) + self._prompt_list

    def _clear_console_buffer(self) -> None:
        """Clear console buffer and ensure clean prompt state.

        This is essential after long operations (like dd) that may leave
        garbage in the serial buffer, especially on ser2net connections.
        """
        # Send Ctrl+C to interrupt any pending operation
        self._console.sendcontrol("c")
        time.sleep(0.3)

        # Read and discard any garbage - do this multiple times
        for _ in range(5):
            try:
                garbage = self._console.read_nonblocking(size=10000, timeout=0.1)
                if garbage:
                    _LOGGER.debug(f"Cleared {len(garbage)} bytes from buffer")
            except pexpect.TIMEOUT:
                break

        # Send empty line and wait for prompt
        self._console.sendline("")
        try:
            self._console.expect(self._prompt_list, timeout=5)
        except pexpect.TIMEOUT:
            _LOGGER.debug("Prompt not found after buffer clear, continuing...")

    def _robust_command(self, command: str, timeout: int = 30) -> str:
        """Execute command with buffer clearing - robust for noisy serial connections.

        Unlike execute_command which uses expect_exact for echo matching,
        this method just waits for the prompt, making it tolerant of garbage.

        :param command: Command to execute
        :param timeout: Timeout in seconds
        :return: Command output (content before prompt)
        """
        self._clear_console_buffer()
        self._console.sendline(command)
        self._console.expect(self._prompt_list, timeout=timeout)
        return self._console.before

    def _run_command(self, command: str, timeout: int = 30, force_serial: bool = False) -> str:
        """Execute command via SSH (preferred) or serial console (fallback).

        Uses SSH via WAN container when available for reliable command execution.
        Falls back to serial console when SSH is not configured or force_serial=True.

        :param command: Command to execute on RPi
        :param timeout: Timeout in seconds
        :param force_serial: Force serial console (e.g., for reboot operations)
        :return: Command output
        """
        if self._wan and self._rpi_ip and not force_serial:
            # Execute via SSH through WAN container
            # Use UserKnownHostsFile=/dev/null to avoid host key issues after RPi re-flash
            ssh_cmd = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 root@{self._rpi_ip} '{command}'"
            try:
                # WAN device uses console.execute_command or _console.execute_command
                if hasattr(self._wan, 'console'):
                    result = self._wan.console.execute_command(ssh_cmd, timeout=timeout)
                elif hasattr(self._wan, '_console'):
                    result = self._wan._console.execute_command(ssh_cmd, timeout=timeout)
                else:
                    raise AttributeError("WAN device has no console attribute")
                _LOGGER.debug(f"SSH command result ({len(result)} chars): {repr(result[:200] if result else 'empty')}")
                return result
            except Exception as e:
                _LOGGER.warning(f"SSH command failed, falling back to serial: {e}")
                return self._robust_command(command, timeout)
        else:
            # Use serial console
            return self._robust_command(command, timeout)

    def _handle_ssh_prompts(self, password: Optional[str], timeout: int = 30) -> str:
        """Handle SSH host key and password prompts, wait for command completion.

        :param password: SSH password (optional)
        :param timeout: Timeout in seconds
        :return: Command output (content before prompt)
        :raises BoardfarmException: If password required but not provided
        """
        patterns = self._build_expect_patterns(
            r"Do you want to continue connecting\? \(y/n\)",  # Dropbear
            r"Are you sure you want to continue connecting",  # OpenSSH
            r"[Pp]assword:",
        )
        prompt_start_index = 3
        full_output = ""

        while True:
            index = self._console.expect(patterns, timeout=timeout)
            full_output += self._console.before

            if index in (0, 1):
                self._console.sendline("y")
            elif index == 2:
                if password:
                    self._console.sendline(password)
                else:
                    raise BoardfarmException("SSH requested password but none provided")
            elif index >= prompt_start_index:
                break

        return full_output

    def _execute_ssh_command(
        self,
        host: str,
        username: str,
        password: Optional[str],
        remote_command: str,
        timeout: int = 30,
    ) -> str:
        """Execute command on remote host via SSH.

        :param host: Remote host
        :param username: SSH username
        :param password: SSH password
        :param remote_command: Command to execute
        :param timeout: Timeout in seconds
        :return: Command output
        """
        self._console.sendline(f"ssh {username}@{host} '{remote_command}'")
        return self._handle_ssh_prompts(password, timeout)

    def _stream_from_host(
        self,
        host: str,
        username: str,
        password: Optional[str],
        stream_cmd: str,
        timeout: int = 300,
    ) -> str:
        """Stream data from remote host via SSH pipe.

        :param host: Remote host
        :param username: SSH username
        :param password: SSH password
        :param stream_cmd: Full command with SSH pipe (e.g., "ssh host 'cat file' | dd ...")
        :param timeout: Timeout in seconds
        :return: Command output
        :raises BoardfarmException: On timeout or error
        """
        _LOGGER.info("Starting image transfer (this may take several minutes)...")
        self._console.sendline(stream_cmd)

        try:
            result = self._handle_ssh_prompts(password, timeout)
            if "error" in result.lower() and "0+0 records" not in result.lower():
                raise BoardfarmException(f"Flash operation failed: {result}")
            return result
        except pexpect.TIMEOUT as e:
            raise BoardfarmException("Flash operation timed out") from e

    def flash(
        self,
        image: str,
        image_host: str,
        image_username: str = DEFAULT_IMAGE_USERNAME,
        image_password: str = DEFAULT_IMAGE_PASSWORD,
        image_base_path: str = DEFAULT_IMAGE_BASE_PATH,
    ) -> None:
        """Flash firmware using A/B partition system.

        :param image: Image filename
        :param image_host: WAN container static IP (e.g., 10.101.0.20)
        :param image_username: SSH username (default: root)
        :param image_password: SSH password (default: bigfoot1)
        :param image_base_path: Base directory for images (default: /tmp)
        :raises BoardfarmException: On flash failure
        """
        _LOGGER.info("Starting A/B partition flash for RPi")
        _LOGGER.info(f"Image: {image}")

        # Construct full image path
        if image.startswith("/"):
            image_path = image
        else:
            image_path = f"{image_base_path.rstrip('/')}/{image}"
        _LOGGER.info(f"Image location: {image_username}@{image_host}:{image_path}")

        try:
            self.verify_ab_partitions()
            self.verify_partition_layout()

            current_partition, target_partition = self.get_ab_partitions()
            _LOGGER.info(f"Current: {current_partition}, Target: {target_partition}")

            self.verify_target_not_mounted(target_partition)
            self.verify_image_host_access(
                image_host, image_username, image_password, image_path
            )
            self.flash_image(
                image_host, image_username, image_password, image_path, target_partition
            )
            self.verify_flash(target_partition)

            _LOGGER.info("Flash completed successfully")

            self.switch_boot_partition(current_partition, target_partition)
            _LOGGER.info(f"Next boot will use: {target_partition}")

            self.reboot_and_wait()
            _LOGGER.info("Device rebooted successfully with new firmware")

        except Exception as e:
            _LOGGER.error(f"Flash operation failed: {e}")
            raise BoardfarmException(f"RPi flash failed: {e}") from e

    def verify_ab_partitions(self) -> None:
        """Verify A/B partitions exist on the SD card."""
        _LOGGER.info("Verifying A/B partitions exist...")
        output = self._run_command("ls -l /dev/mmcblk0p* 2>&1")

        if "mmcblk0p2" not in output or "mmcblk0p3" not in output:
            msg = "A/B partitions not found (expected /dev/mmcblk0p2 and /dev/mmcblk0p3)"
            raise BoardfarmException(msg)

        _LOGGER.info("A/B partitions verified: /dev/mmcblk0p2 and /dev/mmcblk0p3")

    def verify_partition_layout(self) -> None:
        """Verify SD card partitions are exactly 1GB each."""
        _LOGGER.info("Verifying SD card partition layout...")

        # Use full path - SSH shell may have different PATH than login shell
        fdisk_output = self._run_command("/sbin/fdisk -l /dev/mmcblk0 2>&1")
        _LOGGER.debug(f"fdisk output: {repr(fdisk_output[:500] if fdisk_output else 'empty')}")

        p2_sectors = p3_sectors = None
        for line in fdisk_output.splitlines():
            if "mmcblk0p2" in line or "mmcblk0p3" in line:
                _LOGGER.debug(f"Partition line: {repr(line)}")
                nums = [p for p in line.split() if p.isdigit()]
                _LOGGER.debug(f"Parsed numbers: {nums}")
                if len(nums) >= 3:
                    if "mmcblk0p2" in line:
                        p2_sectors = int(nums[2])
                    else:
                        p3_sectors = int(nums[2])

        _LOGGER.debug(f"Parsed sectors: p2={p2_sectors}, p3={p3_sectors}")

        EXPECTED_SECTORS = 2097152  # 1GB
        for name, sectors in [("mmcblk0p2", p2_sectors), ("mmcblk0p3", p3_sectors)]:
            if sectors != EXPECTED_SECTORS:
                msg = f"Partition {name} has {sectors} sectors, expected {EXPECTED_SECTORS} (1GB)"
                raise BoardfarmException(msg)

        _LOGGER.info("SD card layout verified: both partitions are 1GB")

    def get_ab_partitions(self) -> tuple[str, str]:
        """Determine current and target partitions from boot config."""
        output = self._run_command("cat /boot/cmdline.txt")

        if "mmcblk0p2" in output:
            return "mmcblk0p2", "mmcblk0p3"
        elif "mmcblk0p3" in output:
            return "mmcblk0p3", "mmcblk0p2"
        else:
            raise BoardfarmException("Unable to determine current boot partition")

    def verify_target_not_mounted(self, target_partition: str) -> None:
        """Verify target partition is not currently mounted, unmounting if needed."""
        _LOGGER.info(f"Verifying {target_partition} is not mounted...")
        mount_output = self._run_command("mount")

        if f"/dev/{target_partition}" in mount_output:
            _LOGGER.warning(
                f"Target partition /dev/{target_partition} is mounted, attempting unmount..."
            )
            # Try to unmount
            self._run_command(f"umount /dev/{target_partition} 2>&1")
            time.sleep(1)

            # Verify unmount succeeded
            mount_output = self._run_command("mount")
            if f"/dev/{target_partition}" in mount_output:
                msg = f"Target partition /dev/{target_partition} is still mounted after unmount attempt. Reboot first."
                raise BoardfarmException(msg)
            _LOGGER.info(f"Successfully unmounted /dev/{target_partition}")

        _LOGGER.info(f"Target partition {target_partition} is not mounted")

    def verify_image_host_access(
        self,
        host: str,
        username: str,
        password: Optional[str],
        image_path: str,
    ) -> None:
        """Verify network access and image file exists on host."""
        _LOGGER.info(f"Verifying access to image host: {host}")

        # Test network connectivity
        ping_result = self._run_command(f"ping -c 3 {host} 2>&1")
        if "0 received" in ping_result or "100% packet loss" in ping_result:
            raise BoardfarmException(f"Cannot reach image host: {host}")
        _LOGGER.info(f"Image host {host} is reachable")

        # Test SSH connectivity
        try:
            self._execute_ssh_command(host, username, password, "echo test", timeout=15)
            _LOGGER.info(f"SSH connection to {username}@{host} successful")
        except Exception as e:
            raise BoardfarmException(f"SSH connection failed: {e}") from e

        # Verify image file exists (use unique markers to avoid matching command echo)
        file_check = self._execute_ssh_command(
            host, username, password,
            f"test -f {image_path} && echo FILE_OK_1748 || echo FILE_MISSING_1748",
            timeout=30,
        )
        _LOGGER.debug(f"File check output: {repr(file_check)}")

        if "FILE_OK_1748" in file_check:
            pass  # File exists
        elif "FILE_MISSING_1748" in file_check:
            raise BoardfarmException(f"Image file not found: {image_path}")
        else:
            raise BoardfarmException(f"Unable to verify image: {image_path}")

        _LOGGER.info(f"Image file verified: {image_path}")

    def flash_image(
        self,
        host: str,
        username: str,
        password: Optional[str],
        image_path: str,
        target_partition: str,
    ) -> None:
        """Flash image to target partition (auto-detects WIC vs raw)."""
        _LOGGER.info("Detecting image type...")

        fdisk_output = self._execute_ssh_command(
            host, username, password, f"fdisk -l {image_path}", timeout=30
        )

        if "error" in fdisk_output.lower() or "cannot open" in fdisk_output.lower():
            raise BoardfarmException(f"Failed to read image: {fdisk_output}")

        # Check for partition table (WIC image)
        has_partition_table = "Disklabel type:" in fdisk_output
        partition_line = None
        for line in fdisk_output.splitlines():
            if "83" in line and "Linux" in line:
                partition_line = line
                break

        if has_partition_table and partition_line:
            _LOGGER.info("Detected WIC image with partition table")
            self._flash_wic_partition(
                host, username, password, image_path, target_partition, partition_line
            )
        elif not has_partition_table:
            _LOGGER.info("Detected raw partition image")
            self._flash_raw_partition(
                host, username, password, image_path, target_partition
            )
        else:
            raise BoardfarmException("Unable to determine image type")

    def _flash_raw_partition(
        self,
        host: str,
        username: str,
        password: Optional[str],
        image_path: str,
        target_partition: str,
    ) -> None:
        """Flash raw partition image directly."""
        _LOGGER.info(f"Flashing raw partition to /dev/{target_partition}")
        cmd = f"ssh {username}@{host} 'cat {image_path}' | dd of=/dev/{target_partition} bs=4M"
        self._stream_from_host(host, username, password, cmd)
        _LOGGER.info(f"Raw partition written to /dev/{target_partition}")

    def _flash_wic_partition(
        self,
        host: str,
        username: str,
        password: Optional[str],
        image_path: str,
        target_partition: str,
        partition_line: str,
    ) -> None:
        """Extract and flash Linux partition from WIC image."""
        _LOGGER.info(f"Extracting Linux partition to /dev/{target_partition}")

        # Parse partition geometry: "...wic2  122880 1049393  926514 452.4M 83 Linux"
        nums = [p for p in partition_line.split() if p.isdigit()]
        if len(nums) < 3:
            raise BoardfarmException(f"Cannot parse partition info: {partition_line}")

        start_sector, _, sector_count = nums[0], nums[1], nums[2]
        sector_count_int = int(sector_count)

        # Safety check
        TARGET_SECTORS = 2097152  # 1GB
        if sector_count_int > TARGET_SECTORS:
            size_mb = sector_count_int * 512 / 1024 / 1024
            raise BoardfarmException(f"WIC partition too large: {size_mb:.1f}MB > 1GB")

        _LOGGER.info(f"Partition: start={start_sector}, count={sector_count} sectors")

        cmd = (
            f"ssh {username}@{host} 'dd if={image_path} bs=512 "
            f"skip={start_sector} count={sector_count}' | "
            f"dd of=/dev/{target_partition} bs=4M"
        )
        self._stream_from_host(host, username, password, cmd)
        _LOGGER.info(f"WIC partition written to /dev/{target_partition}")

    def verify_flash(self, target_partition: str) -> None:
        """Verify flashed partition is mountable and contains system files."""
        _LOGGER.info(f"Verifying flash integrity for /dev/{target_partition}...")

        self._run_command("mkdir -p /mnt/flash_verify 2>&1")
        mount_result = self._run_command(
            f"mount /dev/{target_partition} /mnt/flash_verify 2>&1"
        )

        if "error" in mount_result.lower() or "failed" in mount_result.lower():
            raise BoardfarmException(f"Failed to mount partition: {mount_result}")

        check_result = self._run_command(
            "ls /mnt/flash_verify/bin /mnt/flash_verify/etc 2>&1"
        )

        if "No such file" in check_result:
            self._run_command("umount /mnt/flash_verify 2>&1")
            raise BoardfarmException(f"Verification failed: {check_result}")

        # Show version if available
        version = self._run_command("cat /mnt/flash_verify/version.txt 2>&1")
        if version and "No such file" not in version:
            _LOGGER.info(f"New firmware version: {version.strip()}")

        self._run_command("umount /mnt/flash_verify 2>&1")
        self._run_command("rmdir /mnt/flash_verify 2>&1")
        _LOGGER.info("Flash integrity verified")

    def switch_boot_partition(self, current: str, target: str) -> None:
        """Update boot configuration to use target partition."""
        _LOGGER.info(f"Switching boot: {current} -> {target}")

        result = self._run_command(
            f"sed -i 's/{current}/{target}/g' /boot/cmdline.txt"
        )
        if result and "error" in result.lower():
            raise BoardfarmException(f"Failed to update boot config: {result}")

        verify = self._run_command("cat /boot/cmdline.txt")
        if target not in verify:
            raise BoardfarmException(f"Boot config update failed: {verify}")

        _LOGGER.info("Boot configuration updated")

    def reboot_and_wait(self, max_wait: int = 180, poll_interval: int = 5) -> None:
        """Reboot device and wait for it to come back up.

        Uses polling approach instead of expecting specific boot messages,
        which is more robust across different kernel versions and configurations.

        :param max_wait: Maximum time to wait for device to boot (seconds)
        :param poll_interval: Time between poll attempts (seconds)
        """
        _LOGGER.info("Rebooting device...")
        self._console.sendline("reboot")

        # Wait for device to go down
        time.sleep(10)

        # Poll until console responds
        elapsed = 0
        _LOGGER.info(f"Waiting up to {max_wait}s for device to boot...")

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            try:
                # Clear any garbage and try a simple command
                self._console.sendcontrol("c")
                time.sleep(0.2)
                try:
                    self._console.read_nonblocking(size=10000, timeout=0.1)
                except pexpect.TIMEOUT:
                    pass

                self._console.sendline("echo boot_ready")
                index = self._console.expect(
                    ["boot_ready"] + self._prompt_list, timeout=5
                )
                if index >= 0:
                    _LOGGER.info(f"Console responsive after {elapsed}s")
                    break
            except pexpect.TIMEOUT:
                _LOGGER.debug(f"  ... waiting ({elapsed}s)")
            except Exception as e:
                _LOGGER.debug(f"  ... waiting ({elapsed}s) - {type(e).__name__}")
        else:
            raise BoardfarmException(
                f"Device did not respond within {max_wait} seconds after reboot"
            )

        # Re-initialize console after reboot
        time.sleep(2)
        self._clear_console_buffer()

        # Suppress kernel messages
        try:
            self._console.sendline("dmesg -n 1")
            self._console.expect(self._prompt_list, timeout=10)
        except pexpect.TIMEOUT:
            _LOGGER.debug("dmesg -n 1 timed out, continuing...")

        # Set terminal width to prevent command wrapping
        try:
            self._console.sendline("stty columns 200; export TERM=xterm")
            self._console.expect(self._prompt_list, timeout=10)
        except pexpect.TIMEOUT:
            _LOGGER.debug("stty columns timed out, continuing...")

        _LOGGER.debug("Console re-initialized after reboot")
