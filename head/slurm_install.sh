#!/bin/bash

# Set URLs for source code download
SLURM_FETCH_URL="https://download.schedmd.com/slurm/slurm-24.05.2.tar.bz2"
MUNGE_FETCH_URL="https://github.com/dun/munge/releases/download/munge-0.5.16/munge-0.5.16.tar.xz"

# Define installation directories
INSTALL_DIR="/opt/apps"
SLURM_DIR="$INSTALL_DIR/slurm"
MUNGE_DIR="$INSTALL_DIR/munge"

# Check and create installation directory if it doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p "$INSTALL_DIR"
fi

# Change to the installation directory
cd "$INSTALL_DIR"

# Download the source files
curl -LO "$MUNGE_FETCH_URL"
curl -LO "$SLURM_FETCH_URL"

# Install dependencies
apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libbz2-dev \
    liblua5.1-dev \
    python3 \

# Extract the source codes
tar -xf munge-*.tar.*
tar -xf slurm-*.tar.*
rm -f *tar*

# Install and configure Munge
cd munge-* 
./configure --prefix="$MUNGE_DIR" 
make -j$(nproc)
make install
cd ..

# Install and configure Slurm
cd slurm-*
./configure --prefix="$SLURM_DIR" --with-munge="$MUNGE_DIR" --with-lua
make -j$(nproc)
make install
cd ..

# Cleanup installation files
rm -rf munge-* slurm-*