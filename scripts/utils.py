# Runs the command in sudo mode
import os
from logger import get_logger
import socket
import subprocess


SUPERUSER_PASS_ON = "SLURM_USER_PASSWORD"
logger = get_logger(__name__)


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



def run(cmd: str, with_super_user: bool = True) -> None:
    """Run a command with sudo and handle errors.
    
    Args:
        cmd (str): The command to run
        with_super_user (bool): If True, run the command with sudo
    
    Raises:
        ValueError: If the command fails
    """
    try:
        # Print the command being executed
        print(f"Running command: {cmd}")

        # Get the password from environment variable and pass it to sudo
        if with_super_user:
            sudo_password = os.environ.get(SUPERUSER_PASS_ON)
            if sudo_password is None:
                raise ValueError(f"{SUPERUSER_PASS_ON} environment variable is not set.")
        
        # Create the sudo command with the command split as a list
        sudo_cmd = ["sudo", "-S"] + cmd.split()

        # Start the process without shell=True
        process = subprocess.Popen(
            sudo_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )
        
        # Pass the password to sudo if required
        if with_super_user:
            stdout, stderr = process.communicate(input=(sudo_password + "\n").encode())
        else:
            stdout, stderr = process.communicate()
        
        # Print the command output
        print("Command output:")
        print(stdout.decode())
        
        # Print any error output
        if stderr:
            print("Command error output:")
            print(stderr.decode())
        
        # Wait for the process to finish
        process.wait()

        # Check return code
        if process.returncode != 0:
            raise ValueError(f"Command '{cmd}' failed with return code {process.returncode}")
        
        print("Command executed successfully.")
        
    except Exception as e:
        print(f"Error: Command '{cmd}' failed with exception: {e}")
        exit(1)
        
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


def get_hostname() -> str:
    """Gets the hostname of the machine

    Returns:
        str: The hostname of the machine
    """
    return socket.gethostname()
