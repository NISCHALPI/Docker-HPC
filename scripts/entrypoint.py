#!/usr/bin/env python3
from compile_slurm import compile_slurm
from network_topology import setup_network
from start_munge import start_munge
from start_slurm_daemons import start_slurm_daemons
from utils import get_hostname, get_env_var
from logger import get_logger
from pathlib import Path


logger = get_logger(__name__)

if __name__ == "__main__":
    hostname = get_hostname()
    logger.info(f"Starting the HPC cluster setup on {hostname}")
    prefix = get_env_var("SLURM_INSTALL_PREFIX")
    if hostname.startswith("slurmctld"):
        compile_slurm(prefix=Path(prefix))
        setup_network()
        start_munge()
        start_slurm_daemons(prefix=Path(prefix))

    elif hostname.startswith("compute"):
        setup_network()
        start_munge()
        start_slurm_daemons(prefix=Path(prefix))

    else:
        raise ValueError(
            f"Unknown node type: {hostname}. Hostname must start with slurmctld or compute"
        )
    
