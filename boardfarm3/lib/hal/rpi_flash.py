"""RPi A/B partition flash hardware abstraction layer.

This module provides firmware flashing capabilities for RPi devices using
the A/B partition update system. The RPi SD card has two root partitions
(mmcblk0p2 and mmcblk0p3) that can alternate as the active system.

Required SD Card Layout:
    root@raspberrypi4-rdk-broadband:~# fdisk -l /dev/mmcblk0
    Disk /dev/mmcblk0: 29.81 GiB, 32010928128 bytes, 62521344 sectors
    Units: sectors of 1 * 512 = 512 bytes
    Sector size (logical/physical): 512 bytes / 512 bytes
    I/O size (minimum/optimal): 512 bytes / 512 bytes
    Disklabel type: dos
    Disk identifier: 0x45a08617

    Device         Boot   Start     End Sectors  Size Id Type
    /dev/mmcblk0p1 *       8192  117249  109058 53.3M  c W95 FAT32 (LBA)
    /dev/mmcblk0p2      2097152 4194303 2097152    1G 83 Linux
    /dev/mmcblk0p3      4194304 6291455 2097152    1G 83 Linux

    - mmcblk0p2: Exactly 2097152 sectors (1GB)
    - mmcblk0p3: Exactly 2097152 sectors (1GB)
    - Boot partition (p1) at standard location

Flash Process:
    1. Verify A/B partitions exist
    2. Verify SD card partition layout (1GB each)
    3. Determine current and target partitions
    4. Verify target partition not mounted
    5. Setup SSH keys for passwordless access
    6. Verify image host access
    7. Flash firmware (auto-detect WIC vs raw partition)
    8. Verify flash integrity
    9. Switch boot partition
    10. Reboot and wait for device

Usage:
    from boardfarm3.lib.hal.rpi_flash import RPiFlashManager

    flasher = RPiFlashManager(console, config)
    flasher.flash(
        image="rdkb-image.wic",
        image_host="10.101.0.10",
        image_username="root",
        image_password="optional",
    )
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

import pexpect

from boardfarm3.exceptions import BoardfarmException

if TYPE_CHECKING:
    from boardfarm3.lib.boardfarm_pexpect import BoardfarmPexpect

_LOGGER = logging.getLogger(__name__)


class RPiFlashManager:
    """Manages A/B partition firmware flashing for RPi devices.

    The RPi uses an A/B partition scheme with two root partitions
    (mmcblk0p2 and mmcblk0p3). This manager handles flashing the
    inactive partition and updating the boot configuration.
    """

    def __init__(
        self,
        console: BoardfarmPexpect,
        config: dict,
    ) -> None:
        """Initialize RPi flash manager.

        :param console: Device console connection
        :type console: BoardfarmPexpect
        :param config: Device configuration dictionary
        :type config: dict
        """
        self._console = console
        self._config = config

        # Handle both BoardfarmPexpect (uses _shell_prompt) and SimplePexpectWrapper (uses .prompt)
        if hasattr(console, 'prompt'):
            self._prompt = console.prompt
        elif hasattr(console, '_shell_prompt'):
            self._prompt = console._shell_prompt
        else:
            msg = "Console object must have either 'prompt' or '_shell_prompt' attribute"
            raise BoardfarmException(msg)

    def _execute_ssh_command(
        self,
        host: str,
        username: str,
        password: Optional[str],
        remote_command: str,
        timeout: int = 30,
    ) -> str:
        # Dropbear doesn't support -o options, use simple SSH command
        ssh_cmd = f"ssh {username}@{host} '{remote_command}'"

        self._console.sendline(ssh_cmd)

        # Accumulate all output
        full_output = ""

        # Handle possible prompts: host key verification, password, or command completion
        while True:
            index = self._console.expect(
                [
                    r"Do you want to continue connecting\? \(y/n\)",  # Dropbear host key
                    r"Are you sure you want to continue connecting",  # OpenSSH host key
                    r"password:",  # Password prompt (lowercase)
                    r"Password:",  # Password prompt (uppercase)
                    *self._prompt,  # Command completed
                ],
                timeout=timeout,
            )

            # Accumulate output from this iteration
            full_output += self._console.before

            if index in (0, 1):
                # Host key verification - accept it
                self._console.sendline("y")
            elif index in (2, 3):
                # Password prompt
                if password:
                    self._console.sendline(password)
                else:
                    msg = "SSH requested password but none provided"
                    raise BoardfarmException(msg)
            elif index == 4:
                # Command completed
                break

        return full_output

    def _setup_ssh_keys(
        self,
        host: str,
        username: str,
        password: Optional[str],
    ) -> None:
        _LOGGER.info("Setting up SSH keys for passwordless authentication...")

        # For now, always set up keys
        _LOGGER.info("Setting up SSH keys...")

        self._console.execute_command("mkdir -p ~/.ssh", timeout=5)

        # Generate Dropbear RSA key
        _LOGGER.info("Generating Dropbear RSA key...")
        self._console.execute_command(
            "dropbearkey -t rsa -f ~/.ssh/id_dropbear -s 2048", timeout=30
        )

        # Extract public key in OpenSSH format
        _LOGGER.info("Extracting public key...")
        self._console.execute_command(
            "dropbearkey -y -f ~/.ssh/id_dropbear | grep '^ssh-rsa' > ~/.ssh/id_dropbear.pub",
            timeout=10,
        )

        # Copy public key to remote server using password
        _LOGGER.info(f"Copying public key to {username}@{host}...")

        copy_cmd = (
            f"cat ~/.ssh/id_dropbear.pub | ssh {username}@{host} "
            f"'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && "
            f"chmod 600 ~/.ssh/authorized_keys'"
        )

        self._console.sendline(copy_cmd)

        # Handle interactive SSH prompts (host key verification, password)
        while True:
            index = self._console.expect(
                [
                    r"Do you want to continue connecting\? \(y/n\)",  # Dropbear host key
                    r"Are you sure you want to continue connecting",  # OpenSSH host key
                    r"password:",  # Password prompt (lowercase)
                    r"Password:",  # Password prompt (uppercase)
                    *self._prompt,  # Command completed
                ],
                timeout=30,
            )

            if index in (0, 1):
                # Host key verification - accept it
                _LOGGER.info("Accepting SSH host key...")
                self._console.sendline("y")
            elif index in (2, 3):
                # Password prompt
                if password:
                    _LOGGER.info("Providing password...")
                    self._console.sendline(password)
                else:
                    msg = "SSH requested password but none provided"
                    raise BoardfarmException(msg)
            elif index == 4:
                # Command completed successfully
                break

        _LOGGER.info("SSH keys configured (public key copied to server)")

    def flash(
        self,
        image: str,
        image_host: str,
        image_username: str = "root",
        image_password: Optional[str] = None,
        image_base_path: str = "/firmware",
    ) -> None:
        """Flash firmware using A/B partition system.

        Performs complete flash operation:
        1. Verify A/B partitions exist
        2. Determine current and target partitions
        3. Verify target partition not mounted
        4. Setup SSH keys for passwordless access
        5. Verify image host access
        6. Flash firmware (auto-detect image type)
        7. Verify flash integrity
        8. Switch boot partition
        9. Reboot and wait for device

        :param image: Image filename
        :type image: str
        :param image_host: Image server IP/hostname
        :type image_host: str
        :param image_username: Image server SSH username
        :type image_username: str
        :param image_password: Image server SSH password (optional)
        :type image_password: Optional[str]
        :param image_base_path: Base directory for images on server
        :type image_base_path: str
        :raises BoardfarmException: on flash failure
        """
        _LOGGER.info("Starting A/B partition flash for RPi")
        _LOGGER.info(f"Image: {image}")

        # Construct full image path
        # If image is already an absolute path, use it directly
        if image.startswith("/"):
            image_path = image
        else:
            # Otherwise combine base path and image name
            image_path = f"{image_base_path.rstrip('/')}/{image}"
        _LOGGER.info(f"Image location: {image_username}@{image_host}:{image_path}")

        try:
            # Step 1: Verify A/B partitions exist
            self.verify_ab_partitions()

            # Step 2: Verify SD card partition layout (1GB each)
            self.verify_partition_layout()

            # Step 3: Determine current and target partitions
            current_partition, target_partition = self.get_ab_partitions()
            _LOGGER.info(f"Current partition: {current_partition}")
            _LOGGER.info(f"Target partition: {target_partition}")

            # Step 4: Verify target partition is not mounted
            self.verify_target_not_mounted(target_partition)

            # Step 5: Setup SSH keys for passwordless access
            self._setup_ssh_keys(image_host, image_username, image_password)

            # Step 6: Verify connectivity to image host
            self.verify_image_host_access(
                image_host, image_username, image_password, image_path
            )

            # Step 7: Flash the target partition
            self.flash_image(
                image_host,
                image_username,
                image_password,
                image_path,
                target_partition,
            )

            # Step 7: Verify flash integrity
            self.verify_flash(target_partition)

            _LOGGER.info("Flash completed successfully")

            # Step 8: Switch boot partition (do this last before reboot)
            self.switch_boot_partition(current_partition, target_partition)
            _LOGGER.info(f"Next boot will use: {target_partition}")

            # Step 9: Reboot and wait for device to come back
            self.reboot_and_wait()

            _LOGGER.info("Device rebooted successfully with new firmware")

        except Exception as e:
            _LOGGER.error(f"Flash operation failed: {e}")
            raise BoardfarmException(f"RPi flash failed: {e}") from e

    def verify_ab_partitions(self) -> None:
        _LOGGER.info("Verifying A/B partitions exist...")

        output = self._console.execute_command("ls -l /dev/mmcblk0p* 2>&1")

        if "mmcblk0p2" not in output or "mmcblk0p3" not in output:
            msg = "A/B partitions not found (expected /dev/mmcblk0p2 and /dev/mmcblk0p3)"
            raise BoardfarmException(msg)

        _LOGGER.info("A/B partitions verified: /dev/mmcblk0p2 and /dev/mmcblk0p3")

    def verify_partition_layout(self) -> None:
        _LOGGER.info("Verifying SD card partition layout...")

        # Get partition table from SD card
        self._console.sendline("fdisk -l /dev/mmcblk0 > /tmp/sd_fdisk.txt 2>&1")
        self._console.expect(self._prompt, timeout=10)

        self._console.sendline("cat /tmp/sd_fdisk.txt")
        self._console.expect(self._prompt, timeout=10)
        fdisk_output = self._console.before

        self._console.sendline("rm -f /tmp/sd_fdisk.txt")
        self._console.expect(self._prompt, timeout=10)

        # Parse partition info
        p2_sectors = None
        p3_sectors = None

        for line in fdisk_output.splitlines():
            if "mmcblk0p2" in line:
                parts = line.split()
                # Find the sectors count (4th numeric field)
                nums = [p for p in parts if p.isdigit()]
                if len(nums) >= 3:
                    p2_sectors = int(nums[2])  # start, end, sectors
            elif "mmcblk0p3" in line:
                parts = line.split()
                nums = [p for p in parts if p.isdigit()]
                if len(nums) >= 3:
                    p3_sectors = int(nums[2])

        # Verify both partitions are exactly 1GB (2097152 sectors)
        EXPECTED_SECTORS = 2097152

        if p2_sectors != EXPECTED_SECTORS:
            msg = (
                f"SD card partition layout incorrect: mmcblk0p2 has {p2_sectors} sectors, "
                f"expected {EXPECTED_SECTORS} (1GB). Please resize partitions."
            )
            raise BoardfarmException(msg)

        if p3_sectors != EXPECTED_SECTORS:
            msg = (
                f"SD card partition layout incorrect: mmcblk0p3 has {p3_sectors} sectors, "
                f"expected {EXPECTED_SECTORS} (1GB). Please resize partitions."
            )
            raise BoardfarmException(msg)

        _LOGGER.info(f"SD card layout verified: p2={p2_sectors} sectors (1GB), p3={p3_sectors} sectors (1GB)")

    def get_ab_partitions(self) -> tuple[str, str]:

        output = self._console.execute_command("cat /boot/cmdline.txt")

        if "mmcblk0p2" in output:
            current = "mmcblk0p2"
            target = "mmcblk0p3"
        elif "mmcblk0p3" in output:
            current = "mmcblk0p3"
            target = "mmcblk0p2"
        else:
            msg = "Unable to determine current boot partition from /boot/cmdline.txt"
            raise BoardfarmException(msg)

        return current, target

    def verify_target_not_mounted(self, target_partition: str) -> None:
        _LOGGER.info(f"Verifying {target_partition} is not mounted...")

        mount_output = self._console.execute_command("mount")

        # Check if target partition is mounted
        if f"/dev/{target_partition}" in mount_output:
            msg = (
                f"Target partition /dev/{target_partition} is currently mounted. "
                f"This can happen if A/B switch was performed but device was not rebooted. "
                f"Please reboot the device before attempting to flash."
            )
            raise BoardfarmException(msg)

        _LOGGER.info(f"Target partition {target_partition} is not mounted (verified)")

    def verify_image_host_access(
        self,
        host: str,
        username: str,
        password: Optional[str],
        image_path: str,
    ) -> None:
        _LOGGER.info(f"Verifying access to image host: {host}")

        # Test network connectivity
        ping_result = self._console.execute_command(f"ping -c 3 {host} 2>&1")
        if "0 received" in ping_result or "100% packet loss" in ping_result:
            msg = f"Cannot reach image host: {host}"
            raise BoardfarmException(msg)

        _LOGGER.info(f"Image host {host} is reachable")

        # Test SSH connectivity (keys should already be set up)
        # Just try to execute a command - if it doesn't raise an exception, it worked
        try:
            self._execute_ssh_command(
                host=host,
                username=username,
                password=password,
                remote_command="echo test",
                timeout=15,
            )
            _LOGGER.info(f"SSH connection to {username}@{host} successful")
        except Exception as e:
            msg = f"SSH connection to {username}@{host} failed: {e}"
            raise BoardfarmException(msg) from e

        # Verify image file exists using test -f command
        # Use sendline/expect to get reliable output capture
        self._console.sendline(f"ssh {username}@{host} 'test -f {image_path} && echo FILE_EXISTS || echo FILE_NOT_FOUND'")

        # Handle possible SSH prompts or command completion
        while True:
            index = self._console.expect(
                [
                    r"Do you want to continue connecting\? \(y/n\)",
                    r"Are you sure you want to continue connecting",
                    r"FILE_EXISTS",
                    r"FILE_NOT_FOUND",
                    *self._prompt,
                ],
                timeout=15,
            )

            if index in (0, 1):
                # Host key prompt - accept it
                self._console.sendline("y")
            elif index == 2:
                # File exists - wait for prompt to complete
                self._console.expect(self._prompt, timeout=5)
                break
            elif index == 3:
                # File not found
                self._console.expect(self._prompt, timeout=5)
                msg = f"Image file not found on host: {image_path}"
                raise BoardfarmException(msg)
            elif index == 4:
                # Prompt appeared but no FILE marker
                # Check the output we got
                test_output = self._console.before
                if "FILE_EXISTS" in test_output:
                    break
                elif "FILE_NOT_FOUND" in test_output:
                    msg = f"Image file not found on host: {image_path}"
                    raise BoardfarmException(msg)
                else:
                    msg = f"Unable to verify image file existence: {image_path} (output: {test_output[:100]})"
                    raise BoardfarmException(msg)

        _LOGGER.info(f"Image file verified: {image_path}")

        # Get file size for informational purposes
        self._console.sendline(f"ssh {username}@{host} 'ls -lh {image_path}'")
        self._console.expect(self._prompt, timeout=10)
        size_output = self._console.before

        # Try to extract and log file size
        for line in size_output.splitlines():
            if image_path in line or any(c.isdigit() for c in line):
                _LOGGER.info(f"Image details: {line.strip()}")
                break

    def flash_image(
        self,
        host: str,
        username: str,
        password: Optional[str],
        image_path: str,
        target_partition: str,
    ) -> None:
        # Detect image type using fdisk
        _LOGGER.info("Detecting image type...")

        # Copy image metadata to local RPi temp file, then read it locally
        # This avoids SSH output buffering issues
        self._console.sendline(f"ssh {username}@{host} 'fdisk -l {image_path}' > /tmp/rpi_fdisk_check.txt 2>&1")
        self._console.expect(self._prompt, timeout=30)

        # Now read the local temp file
        self._console.sendline("cat /tmp/rpi_fdisk_check.txt")
        self._console.expect(self._prompt, timeout=30)
        fdisk_output = self._console.before.strip()

        # Clean up
        self._console.sendline("rm -f /tmp/rpi_fdisk_check.txt")
        self._console.expect(self._prompt, timeout=10)

        if "error" in fdisk_output.lower() or "cannot open" in fdisk_output.lower():
            msg = f"Failed to read image: {fdisk_output}"
            raise BoardfarmException(msg)

        # Check if image has partition table (WIC) or is raw partition
        has_partition_table = False
        partition_info = None

        for line in fdisk_output.splitlines():
            if "Disklabel type:" in line:
                has_partition_table = True
            if "83" in line and "Linux" in line:
                partition_info = line

        if has_partition_table and partition_info:
            # WIC image - extract partition
            _LOGGER.info("Detected WIC image with partition table")
            _LOGGER.info(f"Linux partition found: {partition_info.strip()}")
            self._flash_wic_partition(
                host, username, password, image_path, target_partition, partition_info
            )
        elif not has_partition_table:
            # Raw partition image - direct copy
            _LOGGER.info("Detected raw partition image (no partition table)")
            self._flash_raw_partition(host, username, password, image_path, target_partition)
        else:
            msg = "Unable to determine image type or no Linux partition found"
            raise BoardfarmException(msg)

    def _flash_raw_partition(
        self,
        host: str,
        username: str,
        password: Optional[str],
        image_path: str,
        target_partition: str,
    ) -> None:
        _LOGGER.info(f"Flashing raw partition to /dev/{target_partition}")

        # Build SSH pipe command for streaming (uses passwordless SSH with keys)
        flash_cmd = f"ssh {username}@{host} 'cat {image_path}' | dd of=/dev/{target_partition} bs=4M"

        _LOGGER.info("Starting image transfer (this may take several minutes)...")

        try:
            # Execute flash with extended timeout (120 seconds for 500MB image)
            result = self._console.execute_command(flash_cmd, timeout=120)

            # Verify dd completed successfully
            if "error" in result.lower() or "failed" in result.lower():
                msg = f"Flash operation failed: {result}"
                raise BoardfarmException(msg)

        except pexpect.TIMEOUT as e:
            msg = "Flash operation timed out (image too large or connection slow)"
            raise BoardfarmException(msg) from e

        _LOGGER.info(f"Raw partition successfully written to /dev/{target_partition}")

    def _flash_wic_partition(
        self,
        host: str,
        username: str,
        password: Optional[str],
        image_path: str,
        target_partition: str,
        partition_info: str,
    ) -> None:
        _LOGGER.info(f"Extracting Linux partition from WIC to /dev/{target_partition}")

        # Parse partition geometry from fdisk output
        # Example: "...wic2  122880 1049393  926514 452.4M 83 Linux"
        parts = partition_info.split()

        try:
            # Find start sector, end sector, and sector count (all numeric)
            # Example: "...wic2  122880 1049393  926514 452.4M 83 Linux"
            #                     ^start ^end     ^count
            start_sector = None
            end_sector = None
            sector_count = None

            for part in parts:
                if part.isdigit():
                    if start_sector is None:
                        start_sector = part
                    elif end_sector is None:
                        end_sector = part
                    elif sector_count is None:
                        sector_count = part
                        break

            if not start_sector or not end_sector or not sector_count:
                msg = f"Unable to parse partition info: {partition_info}"
                raise BoardfarmException(msg)

            # Safety check: Ensure WIC partition won't overflow 1GB target partition
            TARGET_PARTITION_SECTORS = 2097152  # 1GB target partition
            sector_count_int = int(sector_count)

            if sector_count_int > TARGET_PARTITION_SECTORS:
                msg = (
                    f"WIC partition too large: {sector_count_int} sectors "
                    f"({sector_count_int * 512 / 1024 / 1024:.1f}MB) exceeds target "
                    f"partition size {TARGET_PARTITION_SECTORS} sectors (1GB)"
                )
                raise BoardfarmException(msg)

        except (ValueError, IndexError) as e:
            msg = f"Failed to parse partition geometry: {partition_info}"
            raise BoardfarmException(msg) from e

        _LOGGER.info(
            f"Extracting partition: start={start_sector}, "
            f"end={end_sector}, count={sector_count} sectors "
            f"({int(sector_count) * 512 / 1024 / 1024:.1f}MB)"
        )

        # Build SSH pipe command for streaming (uses passwordless SSH with keys)
        flash_cmd = (
            f"ssh {username}@{host} 'dd if={image_path} bs=512 skip={start_sector} count={sector_count}' | "
            f"dd of=/dev/{target_partition} bs=4M"
        )

        _LOGGER.info("Starting WIC partition extraction and transfer...")
        _LOGGER.info("This may take > 1 minute for large images...")

        try:
            result = self._console.execute_command(flash_cmd, timeout=120)

            if "error" in result.lower() or "failed" in result.lower():
                msg = f"Flash operation failed: {result}"
                raise BoardfarmException(msg)

        except pexpect.TIMEOUT as e:
            msg = "Flash operation timed out"
            raise BoardfarmException(msg) from e

        _LOGGER.info(f"WIC partition successfully written to /dev/{target_partition}")

    def verify_flash(self, target_partition: str) -> None:
        _LOGGER.info(f"Verifying flash integrity for /dev/{target_partition}...")

        # Create temporary mount point
        self._console.execute_command("mkdir -p /mnt/flash_verify 2>&1")

        # Attempt to mount partition
        mount_result = self._console.execute_command(
            f"mount /dev/{target_partition} /mnt/flash_verify 2>&1"
        )

        if "error" in mount_result.lower() or "failed" in mount_result.lower():
            msg = f"Failed to mount flashed partition: {mount_result}"
            raise BoardfarmException(msg)

        # Check for critical system files
        check_result = self._console.execute_command(
            "ls /mnt/flash_verify/bin /mnt/flash_verify/etc 2>&1"
        )

        if "No such file" in check_result:
            # Unmount before raising exception
            self._console.execute_command("umount /mnt/flash_verify 2>&1")
            self._console.execute_command("rmdir /mnt/flash_verify 2>&1")
            msg = f"Flashed partition verification failed: {check_result}"
            raise BoardfarmException(msg)

        # Show version information if available
        version_result = self._console.execute_command(
            "cat /mnt/flash_verify/version.txt 2>&1"
        )
        if version_result and "No such file" not in version_result:
            _LOGGER.info("New firmware version information:")
            for line in version_result.strip().split("\n"):
                if line.strip():
                    _LOGGER.info(f"  {line.strip()}")

        # Unmount
        self._console.execute_command("umount /mnt/flash_verify 2>&1")
        self._console.execute_command("rmdir /mnt/flash_verify 2>&1")

        _LOGGER.info("Flash integrity verified successfully")

    def switch_boot_partition(
        self, current_partition: str, target_partition: str
    ) -> None:
        _LOGGER.info(
            f"Switching boot partition from {current_partition} to {target_partition}"
        )

        # Update cmdline.txt
        sed_cmd = (
            f"sed -i 's/{current_partition}/{target_partition}/g' /boot/cmdline.txt"
        )
        result = self._console.execute_command(sed_cmd)

        if result and "error" in result.lower():
            msg = f"Failed to update boot configuration: {result}"
            raise BoardfarmException(msg)

        # Verify the change
        verify_result = self._console.execute_command("cat /boot/cmdline.txt")

        if target_partition not in verify_result:
            msg = f"Boot config update verification failed: {verify_result}"
            raise BoardfarmException(msg)

        _LOGGER.info("Boot configuration updated successfully")

    def reboot_and_wait(self) -> None:
        _LOGGER.info("Rebooting device to activate new firmware...")

        # Send reboot command (don't wait for prompt, device will start shutting down)
        self._console.sendline("reboot")
        _LOGGER.info("Reboot command sent")

        # Wait for device to start rebooting
        # We'll see shutdown messages, not a prompt
        import time
        time.sleep(5)

        # Wait for hardware boot to complete
        # This expects boot messages and login prompt
        try:
            _LOGGER.info("Waiting for device to boot...")
            # Wait for boot message (increased timeout for slow shutdown services)
            self._console.expect("Booting Linux on physical CPU", timeout=240)
            _LOGGER.info("Boot started, waiting for login prompt...")

            # Wait for automatic login (increased timeout for slow boot)
            self._console.expect("automatic login", timeout=180)
            _LOGGER.info("Device booted successfully")

        except Exception as e:
            msg = f"Device failed to boot after reboot: {e}"
            raise BoardfarmException(msg) from e
