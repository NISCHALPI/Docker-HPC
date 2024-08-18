#!/bin/bash

# Check if SLURM_USER_PASSWORD environment variable is set
if [ -z "$SLURM_USER_PASSWORD" ]; then
    echo "Error: Environment variable SLURM_USER_PASSWORD is not set."
    exit 1
fi

run_with_sudo() {
    local cmd="$1"
    echo "Running command: $cmd"
    echo "$SLURM_USER_PASSWORD" | sudo -S bash -c "$cmd" || {
        echo "Error: Command '$cmd' failed."
        exit 1
    }
}

# Define the SLURM installation function
install_slurm() {
    # Define installation directories
    local SITE="/opt/apps"
    local SRC="/opt/src"
    local SLURM_SBIN="$SITE/sbin"
    local SLURM_BIN="$SITE/bin"
    local SLURM_URL="https://download.schedmd.com/slurm/slurm-24.05.2.tar.bz2"
    
    # Check and create installation and source directories
    [ ! -d "$SITE" ] && mkdir -p "$SITE"
    [ ! -d "$SRC" ] && mkdir -p "$SRC"

    # Check if SLURM is already installed
    if [ -x "$SLURM_SBIN/slurmd" ] && [ -x "$SLURM_SBIN/slurmctld" ] && [ -x "$SLURM_BIN/srun" ]; then
        echo "SLURM is already installed at $SITE."
        echo "To recompile, use docker compose down --rmi all -v to remove mounted volume."
        exit 0
    fi

    # Install dependencies
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        build-essential \
        libssl-dev \
        libbz2-dev \
        libnuma-dev \
        libmysqlclient-dev \
        libjson-c-dev \
        libjwt-dev \
        libhttp-parser-dev \
        libyaml-dev \
        libcurl4-openssl-dev \
        libreadline-dev \
        libdbus-1-dev \
        libfreeipmi-dev \
        liblua5.3-dev \
        libgtk2.0-dev \
        libmunge-dev \
        libpam0g-dev \
        liblz4-dev \
        libnvidia-ml-dev \
        man2html \
        libpmix-dev \
        curl \
        python3 \
        python3-pip || {
            echo "Error: Failed to install dependencies."
            exit 1
        }

    # Download, extract, compile and install SLURM
    cd "$SRC" || {
        echo "Error: Failed to change directory to $SRC."
        exit 1
    }

    echo "Downloading SLURM from $SLURM_URL..."
    curl -L -O -R "$SLURM_URL" || {
        echo "Error: Failed to download SLURM source."
        exit 1
    }

    echo "Extracting SLURM tarball..."
    tar xaf slurm-*.tar.* || {
        echo "Error: Failed to extract SLURM tarball."
        exit 1
    }
    rm slurm-*.tar.bz2

    # Change to the SLURM source directory and configure
    local SLURM_SRC_DIR=$(ls -d slurm-* 2>/dev/null)
    if [ -z "$SLURM_SRC_DIR" ]; then
        echo "Error: SLURM source directory not found."
        exit 1
    fi

    cd "$SLURM_SRC_DIR" || {
        echo "Error: Failed to change directory to $SLURM_SRC_DIR."
        exit 1
    }

    echo "Configuring SLURM..."
    ./configure --prefix="$SITE" --with-lua --enable-pam --enable-pkgconfig --with-lua || {
        echo "Error: Configuration failed."
        exit 1
    }

    echo "Compiling SLURM..."
    make -j$(nproc) || {
        echo "Error: Compilation failed."
        exit 1
    }

    echo "Installing SLURM..."
    make install || {
        echo "Error: Installation failed."
        exit 1
    }
    
    # Cleanup installation files
    rm -rf "$SRC"
    apt-get autoclean
    rm -rf /var/lib/apt/lists/*
}

# Slurm installation
# Run the SLURM installation function with sudo
run_with_sudo "$(declare -f install_slurm); install_slurm"
cd ~

# Network topology
# Set up the NAT and forwarding rules to direct traffic from worker network to management network
run_with_sudo "sysctl -w net.ipv4.ip_forward=1" || {
    echo "Error: Failed to enable IP forwarding."
    exit 1
}
run_with_sudo "iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE" || {
    echo "Error: Failed to enable IP masquerading on outbound traffic."
    exit 1
}
run_with_sudo "iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT" || {
    echo "Error: Failed to forward traffic from eth1 to eth0."
    exit 1
}
run_with_sudo "iptables -A FORWARD -i eth0 -o eth1 -j ACCEPT" || {
    echo "Error: Failed to forward traffic from eth0 to eth1."
    exit 1
}
echo "SLURM installation and network setup completed successfully."


# Setup munge auth service
setup_munge() {
    # List of directories to check and create
    local dirs=("/etc/munge" "/var/log/munge" "/var/lib/munge" "/run/munge")

    # Check and create necessary directories if they don't exist
    for dir in "${dirs[@]}"; do
        [ ! -d "$dir" ] && mkdir -p "$dir" || true
    done

    # Change ownership for directories
    chown -R munge: /etc/munge /var/log/munge /var/lib/munge /run/munge || {
        echo "Failed to change ownership for munge directories"
        exit 1
    }

    # Set permissions for directories
    chmod 0700 /etc/munge /var/log/munge /var/lib/munge || {
        echo "Failed to set permissions on /etc/munge, /var/log/munge, or /var/lib/munge"
        exit 1
    }
    chmod 0755 /run/munge || {
        echo "Failed to set permissions on /run/munge"
        exit 1
    }

    # Set permissions and ownership for munge.key
    chmod 0700 /etc/munge/munge.key || {
        echo "Failed to set permissions on /etc/munge/munge.key"
        exit 1
    }
    chown munge: /etc/munge/munge.key || {
        echo "Failed to change ownership for /etc/munge/munge.key"
        exit 1
    }
    
    # Start the munged service as munge user
    sudo -u munge /usr/sbin/munged || {
        echo "Failed to start munged service"
        exit 1
    }

    echo "Munge setup completed successfully on Hostname: $HOSTNAME"
}
# Run the munge setup function with sudo
run_with_sudo "$(declare -f setup_munge); setup_munge"



# Setup the controller daemon for SLURM
prepre_slurm_controller() {
    # Define SLURM-related directories
    SLURM_VAR_SPOOL_DIR="/var/spool/slurmd"
    SLURM_RUN_DIR="/run/slurmd"
    SLURM_LOG_DIR="/var/log/slurmd"
    SLURM_STATE_SAVE_LOCATION="/var/spool/slurmctld"

    # Create necessary directories
    temp_dirs=("$SLURM_VAR_SPOOL_DIR" "$SLURM_RUN_DIR" "$SLURM_LOG_DIR" "$SLURM_STATE_SAVE_LOCATION")
    for dir in "${temp_dirs[@]}"; do
        # If not exist, create the directory
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir" || {
                echo "Failed to create $dir directory"
                exit 1
            }
        fi

        # Change ownership of the directory to SLURM user
        UNAME=${SLURM_USERNAME:-"slurm"}
        chown -R $UNAME:$UNAME "$dir" || {
            echo "Failed to change ownership for $dir directory"
            exit 1
        }

        # Change permissions of the directory
        chmod 0700 "$dir" || {
            echo "Failed to set permissions for $dir directory"
            exit 1
        }
    done

    echo "SLURM controller dirs setup completed successfully on Hostname: $HOSTNAME"
}

# Set up the SLURM controller
run_with_sudo "$(declare -f prepre_slurm_controller); prepre_slurm_controller"


# Run the SLURM controller daemon
/opt/apps/sbin/slurmctld -D -vvv -c || {
    echo "Failed to start SLURM controller daemon"
    exit 1
}
