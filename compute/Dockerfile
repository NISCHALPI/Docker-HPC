# syntax=docker/dockerfile:1
ARG VERSION=24.10
FROM ubuntu:${VERSION}

# Set time zone
ARG TIMEZONE="America/Chicago"
RUN ln -sn /usr/share/zoneinfo/${TIMEZONE} /etc/localtime \
    && echo ${TIMEZONE} > /etc/timezone \
    && apt-get update \
    && apt -y install tzdata

# Switch the shell to bash
SHELL ["/usr/bin/bash", "-c"]


# Install Slurm Runtime Deps
RUN <<EOF
apt-get update
slurm_runtime_deps=(
    libssl-dev
    libbz2-dev
    libnuma-dev
    libmysqlclient-dev
    libjson-c-dev
    libjwt-dev
    libhttp-parser-dev
    libyaml-dev
    libcurl4-openssl-dev
    libreadline-dev
    libdbus-1-dev
    dbus
    libfreeipmi-dev
    liblua5.3-dev
    libgtk2.0-dev
    munge
    libmunge2
    libmunge-dev
    libpam0g-dev
    liblz4-dev
    libnvidia-ml-dev
    libpmix-dev
    python3
    python3-pip
    net-tools
    iproute2
    iptables
    iputils-ping
    netcat-openbsd
)
for package in "${slurm_runtime_deps[@]}"
do
    DEBIAN_FRONTEND=noninteractive apt-get install -y $package
done
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF

# Slurm User Account
ARG USERNAME=${SLURM_USER_NAME:-"slurm"}
ARG PASSWORD=${SLURM_USER_PASSWORD:-"slurm"}
ARG UID=1001
ARG GID=1001

# Create the admin user account (slurm)
RUN <<EOF
groupadd --gid ${GID} ${USERNAME}
useradd --uid ${UID} --gid ${GID} -m ${USERNAME}
echo "${USERNAME}:${PASSWORD}" | chpasswd
apt-get update
apt-get install -y sudo
echo "${USERNAME} ALL=(ALL) ALL" > /etc/sudoers.d/${USERNAME} 
chmod 0440 /etc/sudoers.d/${USERNAME}
EOF

USER ${USERNAME}
# Swith the workdir to default directory
WORKDIR /home/${USERNAME}

ENTRYPOINT ["/usr/bin/bash"]
