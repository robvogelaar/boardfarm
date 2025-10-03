"""Pytest configuration for boardfarm tests."""

import logging


def pytest_configure(config):
    """Configure logging levels to reduce noise.

    :param config: pytest config object
    """
    # Reduce pexpect console logging noise (applies to all pexpect.* loggers)
    logging.getLogger("pexpect").setLevel(logging.WARNING)

    # Also reduce asyncio debug messages
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logging.getLogger("boardfarm3.plugins.core").setLevel(logging.ERROR)

    logging.getLogger("boardfarm3.plugins.setup_environment").setLevel(logging.ERROR)

def pytest_sessionstart(session):
    """Set logging levels at session start after loggers are created.

    :param session: pytest session object
    """
    # Set all pexpect child loggers to WARNING level
    for logger_name in logging.root.manager.loggerDict:
        if logger_name.startswith("pexpect"):
            logging.getLogger(logger_name).setLevel(logging.WARNING)
