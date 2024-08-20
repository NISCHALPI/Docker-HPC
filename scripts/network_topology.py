#!/usr/bin/env python3
from utils import run, get_env_var, get_hostname
from logger import get_logger

logger = get_logger("__name__")


NETWORKING_DEPS = [
    "net-tools",
    "iproute2",
    "iptables",
    "iputils-ping",
]


def install_networking_deps() -> None:
    """Installs the networking dependencies"""
    for dep in NETWORKING_DEPS:
        logger.info(f"Installing networking dependency: {dep}")
        run(f"DEBIAN_FRONTEND=noninteractive apt-get install -y {dep}")


def setup_network() -> None:
    """Sets up the network topology for the HPC cluster"""
    # Define the IP on the worker network of the slurmctld node (See compose file)
    SLURMCTDL_IP = get_env_var("SLURMCTLD_WORKER_IP")
    # Get the hostname of the machine
    hostname = get_hostname()

    # Install the networking dependencies
    install_networking_deps()

    # If the hostname is the slurmctld node, then we neet to set up NAT on eth0 to eth1 which is on the worker network
    if hostname.startswith("slurmctld"):
        logger.info("Setting up NAT for all traffic on eth0(gateway) on slurmctld node")
        run("sysctl -w net.ipv4.ip_forward=1")
        run("iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE")
        logger.info("Setting up forwarding rules for eth0 <--> eth1")
        run("iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT")
        run("iptables -A FORWARD -i eth0 -o eth1 -j ACCEPT")

        logger.info(
            """NAT forwarding setup complete on the slurmctld node. 
                    - eth0 is the gateway interface for all outgoing traffic
                    - eth1 is the interface of slurmctld node on the worker network
                    - All outgoing traffic on eth1 is forwarded to eth0 that will  be MASQUERADED as if the traffic is coming from slurmctld node
                    """
        )
    elif hostname.startswith("compute"):
        logger.info("Setting up default route to slurmctld node")
        # Remove the default route
        run("ip route del default")
        # Add the default route to the slurmctld node
        run(f"ip route add default via {SLURMCTDL_IP}")

        logger.info(
            f"{hostname} is now configured to route all outgoing traffic to {SLURMCTDL_IP}"
        )


if __name__ == "__main__":
    setup_network()
