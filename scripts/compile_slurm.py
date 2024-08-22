#!/usr/bin/env python3
from pathlib import Path
import subprocess
from logger import get_logger
from deb_utils import (
    non_interactive_install,
    clear_apt_caches,
    set_uid_root,
    get_env_var,
)

logger = get_logger(__name__)

RUNTIME_DEPS = [
    "build-essential",
    "libssl-dev",
    "libbz2-dev",
    "libnuma-dev",
    "libmysqlclient-dev",
    "libjson-c-dev",
    "libjwt-dev",
    "libhttp-parser-dev",
    "libyaml-dev",
    "libcurl4-openssl-dev",
    "libreadline-dev",
    "libdbus-1-dev",
    "libfreeipmi-dev",
    "liblua5.3-dev",
    "libgtk2.0-dev",
    "munge",
    "libmunge2",
    "libmunge-dev",
    "libpam0g-dev",
    "liblz4-dev",
    "libnvidia-ml-dev",
    "man2html",
    "libpmix-dev",
    "curl",
]


def compile_slurm(
    prefix: Path = Path("/opt/apps/"),
    parallel: int = 8,
) -> None:
    """Compiles and installs SLURM

    Args:
        prefix (str, optional): The prefix to install SLURM. Defaults to "/opt/slurm/".
        parallel (int, optional): The number of parallel jobs to use when compiling. Defaults to 8.
    """
    # Define contants
    SITE = prefix
    SRCDIR = Path("/tmp/slurm")
    SLURM_SBIN_DIR = SITE / "sbin"
    SLURM_BIN = SITE / "bin"
    SLURM_DOWNLOAD_URL = "https://download.schedmd.com/slurm/slurm-24.05.2.tar.bz2"

    # Check if slurm is already installed
    logger.info("Checking if SLURM is already installed")
    slurm_binaries = [
        SLURM_SBIN_DIR / "slurmctld",
        SLURM_SBIN_DIR / "slurmd",
        SLURM_BIN / "sinfo",
        SLURM_BIN / "srun",
    ]
    if not any([path.exists() for path in slurm_binaries]):
        logger.info("\n#############  INSTALLING DEPS #############")
        for dep in RUNTIME_DEPS:
            non_interactive_install(dep)
        logger.info("\n#############  INSTALLING DEPS COMPLETE #############")

        logger.info(f"Compiling SLURM to {SITE}")

        logger.info("SLURM is not installed. Proceeding with installation!")
        # Make sure the site directory exists
        subprocess.run(["mkdir", "-p", str(SITE)])

        # Download and extract the SLURM source code
        logger.info(f"Downloading SLURM source code from {SLURM_DOWNLOAD_URL}")
        subprocess.run(
            ["curl", "-L", "-R", "-o", "/tmp/slurm.tar.bz2", SLURM_DOWNLOAD_URL]
        )
        logger.info("Extracting SLURM source code")
        # Make the SRCDIR
        subprocess.run(["mkdir", "-p", str(SRCDIR)])
        subprocess.run(
            [
                "tar",
                "xaf",
                "/tmp/slurm.tar.bz2",
                "-C",
                "/tmp/slurm",
                "--strip-components=1",
            ]
        )

        # Check if the source code was extracted
        if len(list(SRCDIR.glob("*"))) == 0:
            logger.error(f"Failed to extract SLURM source code to {SRCDIR}")
            raise FileNotFoundError(f"Failed to extract SLURM source code to {SRCDIR}")

        logger.info("Compiling SLURM")
        subprocess.run(
            f"./configure --prefix={SITE} --with-lua --enable-pam --enable-pkgconfig --with-lua",
            cwd=str(SRCDIR),
            shell=True,
        )
        subprocess.run(f"make -j{parallel}", cwd=str(SRCDIR), shell=True)
        subprocess.run("make install", cwd=str(SRCDIR), shell=True)
        logger.info("SLURM compiled and installed successfully to {SITE}")

        # Cleanup
        logger.info("Cleaning up temporary files")
        clear_apt_caches()
        logger.info("SLURM installation complete!")

        logger.info("############# SLURM Installation Complete! #############")
        logger.info(f"SLURM binaries installed to {SLURM_BIN}")
        logger.info(f"SLURM shared binaries installed to {SLURM_SBIN_DIR}")
        logger.info(f"SLURM libraries installed to {SITE / 'lib'}")
        logger.info("############# SLURM Installation Complete! #############")

        # Copy the slurm configuration file to SITE/etc/slurm.conf
        logger.info("Copying slurm configuration file to /etc/slurm.conf")
        # Make the /etc/slurm directory
        subprocess.run(["mkdir", "-p", SITE / "etc"])
        subprocess.run(["cp", get_env_var("SLURM_CONF"), SITE / "etc"])
        # Copy cgroup.conf to /etc/slurm/cgroup.conf
        subprocess.run(["cp", get_env_var("CGROUP_CONF"), SITE / "etc"])

    else:
        logger.info("SLURM is already installed. Skipping installation!")


if __name__ == "__main__":
    set_uid_root()
    compile_slurm()
