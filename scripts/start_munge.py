#!/usr/bin/env python3
from utils import run, get_hostname
from logger import get_logger

from pathlib import Path

RUNTIME_DEPS = [
    "munge",
]

logger = get_logger(__name__)


def install_runtime_deps() -> None:
    """Installs the runtime dependencies"""
    for dep in RUNTIME_DEPS:
        logger.info(f"Installing runtime dependency: {dep}")
        run(f"DEBIAN_FRONTEND=noninteractive apt-get install -y {dep}")


def start_munge() -> None:
    """Starts the munge service"""
    hostname = get_hostname()
    # Install the runtime dependencies
    install_runtime_deps()
    # Setting up munge service
    logger.info(f"Setting up munge service on {hostname}")

    # Essential directories for munge
    dirs = ["/etc/munge", "/var/log/munge", "/var/lib/munge", "/run/munge"]
    for dir in dirs:
        if not Path(dir).exists():
            logger.info(f"Creating directory : {dir}")
            run(f"mkdir -p {dir}")

    # Change permissions for munge directories
    logger.info(f"Changing permissions for munge directories and key : {dirs}")
    run("chown -R munge: /etc/munge /var/log/munge /var/lib/munge /run/munge")
    run("chmod 0700 /etc/munge /var/log/munge /var/lib/munge")
    run("chmod 0755 /run/munge")
    run("chmod 0700 /etc/munge/munge.key")
    run("chown munge: /etc/munge/munge.key")

    # Start the munge service
    logger.info("Starting munge service ...")
    run("sudo -u munge /usr/sbin/munged")
    logger.info(f"Munge service started successfully  on {hostname}")


if __name__ == "__main__":
    start_munge()
