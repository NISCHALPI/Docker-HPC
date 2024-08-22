#!/usr/bin/env python3
from compile_slurm import compile_slurm
from network_topology import setup_network
from start_munge import start_munge
from start_slurm_daemons import start_slurm_daemons
from deb_utils import get_hostname, get_env_var
from start_ldap import sssd_config
from logger import get_logger
from pathlib import Path


logger = get_logger(__name__)

if __name__ == "__main__":
    hostname = get_hostname()
    logger.info(f"Starting the HPC cluster setup on {hostname}")
    prefix = get_env_var("SLURM_INSTALL_PREFIX")
    # Add the slurm binaries to the PATH (/etc/skel/.bashrc)
    with open("/etc/skel/.bashrc", "a") as f:
        f.write(f'export PATH="{prefix}/bin:$PATH"\n')

    if hostname.startswith("slurmctld"):
        # Compile the slurm
        compile_slurm(prefix=Path(prefix))
        # Setup the network
        setup_network()
        # Start Network Switch Service
        sssd_config()
        # Start  Munge
        start_munge()
        # Start the slurm daemons
        start_slurm_daemons(prefix=Path(prefix))

    elif hostname.startswith("compute"):
        # Setup the network
        setup_network()
        # Start Network Switch Service
        sssd_config()
        # Start  Munge
        start_munge()
        # Start the slurm daemons
        start_slurm_daemons(prefix=Path(prefix))

    else:
        raise ValueError(
            f"Unknown node type: {hostname}. Hostname must start with slurmctld or compute"
        )
