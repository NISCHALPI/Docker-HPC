"""Logger module for the navigator package."""

import logging
import os
import sys

__all__ = ["get_logger"]

if "LOGLEVEL" in os.environ and os.environ["LOGLEVEL"] in logging._nameToLevel:
    loglevel = logging._nameToLevel[os.environ["LOGLEVEL"]]
else:
    loglevel = logging.INFO


def get_logger(name: str, dummy: bool = False) -> logging.Logger:
    """Makes a logger for the request module.

    Args:
        name (str): The name of the logger
        dummy (bool, optional): Dummy logger that logs to NullHandler. Defaults to False.

    Returns:
        logging.Logger: The logger
    """
    logger = logging.getLogger(name)
    logger.handlers = []  # Remove any existing handlers

    # Set format for logs
    formatter = logging.Formatter(" %(levelname)s : %(asctime)s : %(message)s")

    if dummy:
        # Create a dummy logger that logs to a NullHandler
        null_handler = logging.NullHandler()
        logger.addHandler(null_handler)
    else:
        # Create a handler to print logs to stdout
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)
        # Set log level
        logger.setLevel(loglevel)

    return logger
