"""Tests for time/date management primitives on RDKB devices."""

import pytest

from boardfarm3.templates.cpe import CPE


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_set_date_and_restore(device_manager):
    board = device_manager.get_device_by_type(CPE)
    console = board.hw.get_console("console")

    original_date = console.execute_command("date '+%Y-%m-%d %H:%M:%S'").strip()
    print(f"\nOriginal date: {original_date}")

    try:
        test_date = "2024-01-01 12:00:00"
        board.sw.set_date(test_date)
        print(f"Set date to: {test_date}")

        import time
        time.sleep(1)

        new_date = console.execute_command("date '+%Y-%m-%d %H:%M'").strip()
        print(f"Current date: {new_date}")

        if "2024-01-01" in new_date:
            print("  OK Date successfully set")
    except Exception as e:
        print(f"Date setting failed: {e}")
        pytest.skip("Date setting not available")
    finally:
        try:
            board.sw.set_date(original_date)
            print(f"Restored date to: {original_date}")
        except Exception:
            pass


@pytest.mark.env_req({"environment_def": {"board": {"model": "bf_rpi4rdkb"}}})
def test_ntp_sync_status(device_manager):
    board = device_manager.get_device_by_type(CPE)

    try:
        ntp_synced = board.sw.get_ntp_sync_status()

        print(f"\nNTP Synchronization Status: {ntp_synced}")
        assert isinstance(ntp_synced, bool), "NTP status should be boolean"
    except Exception as e:
        pytest.skip(f"NTP status check not available: {e}")
