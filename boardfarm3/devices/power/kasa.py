"""Kasa Smart Plug PDU module."""

import asyncio
import logging
from typing import Any

from kasa import Discover

from boardfarm3.templates.pdu import PDU

_LOGGER = logging.getLogger(__name__)

# Suppress verbose debug logging from kasa library
logging.getLogger("kasa").setLevel(logging.WARNING)


class KasaPDU(PDU):
    """Class contains methods to interact with Kasa Smart Plugs.

    This implementation uses the python-kasa library to control
    TP-Link Kasa smart plugs for power management.
    """

    def __init__(self, uri: str) -> None:
        """Initialize Kasa Smart Plug PDU instance.

        The PDU is controlled via the python-kasa library which uses
        the local network protocol to communicate with Kasa devices.

        URI format: "ip_address" or "ip_address:username:password"

        Examples:
            "192.168.1.100"
            "192.168.1.100:user@example.com:password123"

        :param uri: URI containing IP address and optional credentials
        :type uri: str
        """
        parts = uri.split(":")
        self._ip_addr = parts[0].strip()
        self._username = parts[1].strip() if len(parts) > 1 else None
        self._password = parts[2].strip() if len(parts) > 2 else None
        self._device: Any = None

    async def _get_device(self) -> Any:
        """Get or discover the Kasa device.

        Always discovers the device fresh to avoid async event loop issues.

        :returns: Kasa device instance
        :rtype: Any
        """
        _LOGGER.info("Discovering Kasa device at %s", self._ip_addr)
        if self._username and self._password:
            device = await Discover.discover_single(
                self._ip_addr,
                username=self._username,
                password=self._password,
            )
        else:
            device = await Discover.discover_single(self._ip_addr)

        # Update device state after discovery
        await device.update()
        _LOGGER.info(
            "Kasa device discovered: %s (is_on: %s)",
            device.alias,
            device.is_on,
        )

        return device

    async def _async_power_off(self) -> bool:
        """Asynchronously power OFF the Kasa smart plug.

        :returns: True on success
        :rtype: bool
        """
        try:
            device = await self._get_device()
            _LOGGER.info("Turning OFF Kasa device: %s", device.alias)
            await device.turn_off()
            await device.update()
            success = device.is_off
            _LOGGER.info(
                "Kasa device power OFF %s: %s",
                "succeeded" if success else "failed",
                device.alias,
            )
            return success
        except Exception as e:
            _LOGGER.error("Failed to turn OFF Kasa device: %s", e)
            return False

    async def _async_power_on(self) -> bool:
        """Asynchronously power ON the Kasa smart plug.

        :returns: True on success
        :rtype: bool
        """
        try:
            device = await self._get_device()
            _LOGGER.info("Turning ON Kasa device: %s", device.alias)
            await device.turn_on()
            await device.update()
            success = device.is_on
            _LOGGER.info(
                "Kasa device power ON %s: %s",
                "succeeded" if success else "failed",
                device.alias,
            )
            return success
        except Exception as e:
            _LOGGER.error("Failed to turn ON Kasa device: %s", e)
            return False

    async def _async_power_cycle(self) -> bool:
        """Asynchronously power cycle the Kasa smart plug.

        Power cycles by turning off, waiting 5 seconds, then turning on.

        :returns: True on success
        :rtype: bool
        """
        try:
            device = await self._get_device()
            _LOGGER.info("Power cycling Kasa device: %s", device.alias)

            # Turn off
            await device.turn_off()
            await device.update()
            if not device.is_off:
                _LOGGER.error("Failed to turn OFF device during power cycle")
                return False

            # Wait 5 seconds
            _LOGGER.info("Waiting 5 seconds before turning back on...")
            await asyncio.sleep(5)

            # Turn on
            await device.turn_on()
            await device.update()
            success = device.is_on
            _LOGGER.info(
                "Kasa device power cycle %s: %s",
                "succeeded" if success else "failed",
                device.alias,
            )
            return success
        except Exception as e:
            _LOGGER.error("Failed to power cycle Kasa device: %s", e)
            return False

    def _run_async(self, coro):
        """Run an async coroutine, handling existing event loops.

        :param coro: The coroutine to run
        :returns: The result of the coroutine
        """
        try:
            # Check if there's already a running event loop
            loop = asyncio.get_running_loop()
            # If we're here, there's a running loop - we need to use it
            # Create a new task and run it
            import concurrent.futures
            import threading

            result = None
            exception = None

            def run_in_thread():
                nonlocal result, exception
                try:
                    result = asyncio.run(coro)
                except Exception as e:
                    exception = e

            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join()

            if exception:
                raise exception
            return result
        except RuntimeError:
            # No running loop, can use asyncio.run()
            return asyncio.run(coro)

    def power_off(self) -> bool:
        """Power OFF the Kasa smart plug.

        :returns: True on success
        :rtype: bool
        """
        return self._run_async(self._async_power_off())

    def power_on(self) -> bool:
        """Power ON the Kasa smart plug.

        :returns: True on success
        :rtype: bool
        """
        return self._run_async(self._async_power_on())

    def power_cycle(self) -> bool:
        """Power cycle the Kasa smart plug.

        Power cycles by turning off, waiting 5 seconds, then turning on.

        :returns: True on success
        :rtype: bool
        """
        return self._run_async(self._async_power_cycle())
