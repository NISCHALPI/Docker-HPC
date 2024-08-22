#!/usr/bin/env python3
from deb_utils import get_env_var, non_interactive_install
from logger import get_logger
import os
import subprocess

USER_UID = {
    "nbhattarai": 1002,
    "djay": 1003,
    "radkins": 1004,
    "rgriffin": 1005,
    "dcrocker": 1006,
}

RUNTIME_DEPS = ["sssd"]

# Get the environment variables
LDAP_IP = get_env_var("LDAP_SERVER_ADDRESS")
LDAP_PORT = get_env_var("LDAP_SERVER_PORT")
LDAP_AMDIN = get_env_var("LDAP_ADMIN_USERNAME")

logger = get_logger(__name__)


def sssd_config(config_file_at: str = "/opt/configurations/sssd.conf"):
    """SSSD configuration file"""
    # Install the sssd package
    logger.info("Installing sssd package")
    non_interactive_install("sssd")
    logger.info("SSSD package installed")
    # Copy the sssd configuration file to /etc/sssd/conf.d/
    logger.info("Copying the sssd configuration file")
    subprocess.run(["cp", config_file_at, "/etc/sssd/conf.d/"])
    # Change the permission of the file
    subprocess.run(["chmod", "700", "/etc/sssd/conf.d/sssd.conf"])
    # Pamd make home directory for the remote user
    env = os.environ.copy()
    env["DEBIAN_FRONTEND"] = "noninteractive"
    # Enable the mkhomedir
    logger.info("Enabling mkhomedir")
    cmd = "session optional pam_mkhomedir.so skel=/etc/skel umask=0022"
    # Append the line to the file  of /etc/pam.d/common-session
    with open("/etc/pam.d/common-session", "a") as f:
        f.write(cmd)
    # Run the sssd service
    logger.info("Starting the sssd service")
    subprocess.run(["sssd"])


if __name__ == "__main__":
    os.setuid(0)
    sssd_config()
