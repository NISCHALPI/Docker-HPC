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

# Network topology setup
echo "Setting up network topology..."
# Remove default route
run_with_sudo "ip route del default" || {
    echo "Error: Failed to remove default route."
    exit 1
}
# Add the controller as gateway
run_with_sudo "ip route add default via 172.16.100.2" || {
    echo "Error: Failed to add default route via 172.16.100.2."
    exit 1
}
echo "Network topology setup completed successfully."

# Set up the munge service
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

# Prepare the SLURM worker daemon directory
prepre_slurm_controller() {
    # Define SLURM-related directories
    SLURM_VAR_SPOOL_DIR="/var/spool/slurmd"
    SLURM_RUN_DIR="/run/slurmd"
    SLURM_LOG_DIR="/var/log/slurmd"

    # Create necessary directories
    temp_dirs=("$SLURM_VAR_SPOOL_DIR" "$SLURM_RUN_DIR" "$SLURM_LOG_DIR")
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

    echo "SLURM worker dirs setup completed successfully on Hostname: $HOSTNAME"
}
# Set up the SLURM controller
run_with_sudo "$(declare -f prepre_slurm_controller); prepre_slurm_controller"


## Wait until the controller daemon is up and ready and then start the worker daemon (Check on slurmctdl:6817 for TCP connection)
SLURMCTDLHOST="slurmctld"
SLURMCTDLPORT="6817"
echo "Waiting for the controller daemon to be up and ready on $SLURMCTDLHOST:$SLURMCTDLPORT..."
while ! nc -z $SLURMCTDLHOST $SLURMCTDLPORT; do
    sleep 1
    echo "Retrying..."
done

# Start the SLURM worker daemon
echo "Starting the SLURM worker daemon..."
run_with_sudo "/opt/apps/sbin/slurmd -cDvvv --conf-server slurmctld:6817" || {
    echo "Failed to start the SLURM worker daemon"
    exit 1
}
