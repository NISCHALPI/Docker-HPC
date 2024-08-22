# Runs the command in sudo mode
import os
from logger import get_logger
import socket
import subprocess
import sys

logger = get_logger(__name__)


__all__ = [
    "get_env_var",
    "non_interactive_install",
    "check_port_open",
    "get_hostname",
    "clear_apt_caches",
]


def get_env_var(var_name: str) -> str:
    """Gets the environment variable value

    Args:
        var_name (str): The name of the environment variable

    Returns:
        str: The value of the environment variable
    """
    if var_name not in os.environ:
        raise ValueError(f"{var_name} environment variable is not set!")
    return os.environ[var_name]


def non_interactive_install(dep: str) -> None:
    """Installs the package without any prompts

    Args:
        dep (str): The package to install
    """
    logger.info(f"Installing {dep} non-interactively")
    env = os.environ
    env["DEBIAN_FRONTEND"] = "noninteractive"
    subprocess.run(["apt-get", "install", "-y", dep], env=env)


def check_port_open(host_ip: str, port: str) -> bool:
    """Checks if the port is open on the host

    Args:
        host_ip (str): The IP address of the host
        port (str): The port to check

    Returns:
        bool: True if the port is open, False otherwise
    """
    port = int(port)
    try:
        logger.info(f"Checking if port {port} is open on {host_ip}")
        # Create a socket object
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Set the timeout to 1 second
            s.settimeout(1)
            # Try to connect to the host and port
            s.connect((host_ip, port))
        return True
    # Not responding error
    except ConnectionRefusedError as e:
        logger.error(f"Port {port} is not open on {host_ip}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error checking port {port} on {host_ip}: {e}")
        return False


def clear_apt_caches() -> None:
    """Clears the apt caches"""
    logger.info("Cleaning up temporary files")
    subprocess.run(["apt-get", "clean"])
    subprocess.run(["apt-get", "autoremove"])
    subprocess.run(["rm", "-rf", "/var/lib/apt/lists/*"])
    logger.info("Temporary files cleaned up")


def get_hostname() -> str:
    """Gets the hostname of the machine

    Returns:
        str: The hostname of the machine
    """
    return socket.gethostname()


def set_uid_root() -> None:
    """Sets the UID to root"""
    try:
        os.setuid(0)
    except PermissionError:
        logger.error("Error! Must run the program as UID 0 (root)")
        sys.exit(1)
    except Exception as e:
        raise e
