#!/usr/bin/env python3
from pathlib import Path
from utils import run
from logger import get_logger

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


def install_slurm_runtime_deps() -> None:
    """Installs the runtime dependencies for SLURM"""
    for dep in RUNTIME_DEPS:
        print(f"Installing SLURM runtime dependency: {dep}")
        run(f"DEBIAN_FRONTEND=noninteractive apt-get install -y {dep}")


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

    logger.info(f"Compiling SLURM to {SITE}")

    # Check if slurm is already installed
    logger.info("Checking if SLURM is already installed")
    slurm_binaries = [
        SLURM_SBIN_DIR / "slurmctld",
        SLURM_SBIN_DIR / "slurmd",
        SLURM_BIN / "sinfo",
        SLURM_BIN / "srun",
    ]
    if not any([path.exists() for path in slurm_binaries]):
        logger.info("SLURM is not installed. Proceeding with installation!")
        # Install the runtime dependencies
        install_slurm_runtime_deps()

        # Make sure the site directory exists
        run(f"mkdir -p {SITE}")

        # Download and extract the SLURM source code
        logger.info(f"Downloading SLURM source code from {SLURM_DOWNLOAD_URL}")
        run(f"curl -L -R -o /tmp/slurm.tar.bz2 {SLURM_DOWNLOAD_URL}")
        logger.info("Extracting SLURM source code")
        # Make the SRCDIR
        run(f"mkdir -p {SRCDIR}")
        run("tar xaf /tmp/slurm.tar.bz2 -C /tmp/slurm --strip-components=1")

        # Check if the source code was extracted
        if len(list(SRCDIR.glob("*"))) == 0:
            logger.error(f"Failed to extract SLURM source code to {SRCDIR}")
            raise FileNotFoundError(f"Failed to extract SLURM source code to {SRCDIR}")

        logger.info("Compiling SLURM")
        # Compile SLURM
        run(
            f"cd {SRCDIR} && ./configure --prefix={SITE} --with-lua --enable-pam --enable-pkgconfig --with-lua"
        )
        run(f"cd {SRCDIR} && make -j{parallel}")
        run(f"cd {SRCDIR} && make install")
        logger.info("SLURM compiled and installed successfully to {SITE}")

        # Cleanup
        logger.info("Cleaning up temporary files")
        run(f"rm -rf {SRCDIR}")
        run("apt-get clean")
        run("apt-get autoremove")
        run("rm -rf /var/lib/apt/lists/*")
        logger.info("SLURM installation complete!")

        logger.info("############# SLURM Installation Complete! #############")
        logger.info(f"SLURM binaries installed to {SLURM_BIN}")
        logger.info(f"SLURM shared binaries installed to {SLURM_SBIN_DIR}")
        logger.info(f"SLURM libraries installed to {SITE / 'lib'}")
        logger.info("############# SLURM Installation Complete! #############")

    else:
        logger.info("SLURM is already installed. Skipping installation!")


if __name__ == "__main__":
    compile_slurm()
