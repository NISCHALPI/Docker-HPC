#!/usr/bin/env python3
from deb_utils import (
    get_hostname,
    non_interactive_install,
    clear_apt_caches,
    set_uid_root,
)
from logger import get_logger
import subprocess
from pathlib import Path

RUNTIME_DEPS = [
    "munge",
]

logger = get_logger(__name__)


def start_munge() -> None:
    """Starts the munge service"""
    hostname = get_hostname()
    # Install the runtime dependencies
    for dep in RUNTIME_DEPS:
        non_interactive_install(dep)
    clear_apt_caches()

    # Setting up munge service
    logger.info(f"Setting up munge service on {hostname}")

    # Essential directories for munge
    dirs = ["/etc/munge", "/var/log/munge", "/var/lib/munge", "/run/munge"]
    for dir in dirs:
        if not Path(dir).exists():
            logger.info(f"Creating directory : {dir}")
            # Make the dirs and parent dirs if they don't exist
            subprocess.run(["mkdir", "-p", dir])

    # Change permissions for munge directories
    logger.info(f"Changing permissions for munge directories and key : {dirs}")
    subprocess.run(
        [
            "chown",
            "-R",
            "munge:",
            "/etc/munge",
            "/var/log/munge",
            "/var/lib/munge",
            "/run/munge",
        ]
    )
    subprocess.run(["chmod", "0700", "/etc/munge", "/var/log/munge", "/var/lib/munge"])
    subprocess.run(["chmod", "0755", "/run/munge"])
    subprocess.run(["chmod", "0700", "/etc/munge/munge.key"])
    subprocess.run(["chown", "munge:", "/etc/munge/munge.key"])

    # Start the munge service
    logger.info("Starting munge service ...")
    subprocess.run(["sudo", "-u", "munge", "/usr/sbin/munged"])
    logger.info(f"Munge service started successfully  on {hostname}")


if __name__ == "__main__":
    set_uid_root()
    start_munge()
