#!/usr/bin/env python3
from deb_utils import get_env_var, check_port_open, get_hostname, set_uid_root
from logger import get_logger
from pathlib import Path
import time
import subprocess

logger = get_logger(__name__)


SLURMD_DIRS = [
    "/var/spool/slurmd",
    "/var/log/slurmd",
    "/run/slurmd",
]  # See slurm.conf values
SLURMCTLD_DIRS = SLURMD_DIRS + ["/var/spool/slurmctld"]  #  See slurm.conf values


def create_dirs_with_permissions(dirs: list, uname: str) -> None:
    """Create directories with the correct permissions

    Args:
        dirs (list): A list of directories to create
        uname (str): The username to set the permissions to
    """
    for dir in dirs:
        # If the directory does not exist, create it
        if not Path(dir).exists():
            # Create the directory
            subprocess.run(["mkdir", "-p", dir])

        # Change the ownership of the directory
        subprocess.run(["chown", "-R", f"{uname}:{uname}", dir])
        # Set 700 permission
        subprocess.run(["chmod", "700", dir])
        logger.info(f"Created directory: {dir} with permissions 700")


def start_slurm_daemons(prefix: Path) -> None:
    """Start the slurm daemons.

    Args:
        prefix: The prefix where the slurm is installed.
    """
    # Start the slurm daemons
    hostname = get_hostname()

    SLURM_CTDL_WORKER_IP = get_env_var("SLURMCTLD_WORKER_IP")
    SLURM_CTDL_PORT = get_env_var("SLURMCTLD_PORT")
    SLURM_CONFIG_FILE = get_env_var("SLURM_CONF")
    SLURM_USER_NAME = get_env_var("SLURM_USER_NAME")

    logger.info(f"Node detected: {hostname}")

    if hostname.startswith("slurmctld"):
        logger.info(f"Controller node detected: {hostname}")
        logger.info("Starting the slurmctld daemon!")

        # Create the directories with the correct permissions
        create_dirs_with_permissions(SLURMCTLD_DIRS, SLURM_USER_NAME)

        logger.info("Starting the slurmctld daemon!")
        # Check if LDAP server is running
        LDAP_SERVER_ADDRESS = get_env_var("LDAP_SERVER_ADDRESS")
        LDAP_SERVER_PORT = get_env_var("LDAP_SERVER_PORT")
        check_port_open(LDAP_SERVER_ADDRESS, LDAP_SERVER_PORT)
        # Run the controller daemon as slurm user (i.e entrypoint user)q
        subprocess.run(
            [
                "sudo",
                "-u",
                SLURM_USER_NAME,
                f"{prefix}/sbin/slurmctld",
                "-D",
                "-vvv",
                "-c",
                "-f",
                SLURM_CONFIG_FILE,
            ]
        )

    elif hostname.startswith("compute"):
        logger.info(f"Compute node detected: {hostname}")
        logger.info("Starting the slurmd daemon!")

        # Create the directories with the correct permissions
        create_dirs_with_permissions(SLURMD_DIRS, SLURM_USER_NAME)

        # Wait for the controller node to start
        while not check_port_open(SLURM_CTDL_WORKER_IP, SLURM_CTDL_PORT):
            logger.info(
                f"Waiting for the controller node to start on {SLURM_CTDL_WORKER_IP}:{SLURM_CTDL_PORT}"
            )
            time.sleep(1)

        # Run the slurmd daemon as root user (uid=0)
        subprocess.run(
            [
                f"{prefix}/sbin/slurmd",
                "-c",
                "-D",
                "-vvv",
                "--conf-server",
                f"{SLURM_CTDL_WORKER_IP}:{SLURM_CTDL_PORT}",
            ]
        )


if __name__ == "__main__":
    set_uid_root()
    SLURM_INSTALL_PREFIX = get_env_var("SLURM_INSTALL_PREFIX")
    start_slurm_daemons(Path(SLURM_INSTALL_PREFIX))
