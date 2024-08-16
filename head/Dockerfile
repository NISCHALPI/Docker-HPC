# syntax=docker/dockerfile:1
ARG VERSION=24.10
FROM ubuntu:${VERSION}

ARG TIMEZONE="America/Chicago"
ARG USER="slurm"
ARG PASSWORD="slurm"

# Set time zone
RUN ln -sn /usr/share/zoneinfo/${TIMEZONE} /etc/localtime \
    && echo ${TIMEZONE} > /etc/timezone \
    && apt-get update \
    && apt -y install tzdata


# Switch the shell to bash
SHELL ["/usr/bin/bash", "-c"]

# Swith the workdir to optinal directory
WORKDIR /opt

# Install Esstential Deps
RUN <<EOF
DEBIAN_FRONTEND="noninteractive" apt-get install -y build-essential libssl-dev libbz2-dev liblua5.1-dev curl python3 sudo
apt-get clean && rm -rf /var/lib/apt/lists/*
EOF


ENTRYPOINT ["/usr/bin/bash"]
