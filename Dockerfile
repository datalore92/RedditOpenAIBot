FROM archlinux:base-devel

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV container=docker
ENV LC_ALL=C

# Initialize pacman keyring and update system without prompts
RUN pacman-key --init && \
    pacman-key --populate && \
    pacman -Syu --noconfirm && \
    useradd -m -G wheel docker && \
    echo "docker ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    echo "root ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    mkdir -p /etc/systemd/system/console-getty.service.d/ && \
    mkdir -p /run/systemd/system

# Install only needed dependencies
RUN pacman -S --needed --noconfirm \
    python \
    python-pip \
    gcc \
    iptables \
    openvpn \
    curl \
    net-tools \
    sudo \
    base-devel \
    && pacman -Scc --noconfirm && \
    ovpn_ver=$(openvpn --version | head -n1 | awk '{print $2}') && \
    if dpkg --compare-versions "$ovpn_ver" lt "2.4.6"; then \
        echo "ERROR: OpenVPN >= 2.4.6 required (found $ovpn_ver)" && exit 1; \
    fi

# Install dos2unix
RUN pacman -S --noconfirm dos2unix

# Install debug tools
RUN pacman -S --needed --noconfirm \
    tcpdump \
    net-tools \
    traceroute \
    whois

# Add environment variables
ENV TERM=xterm
ENV PYTHONUNBUFFERED=1

# Create VPN user and setup OpenVPN
RUN useradd -m -G wheel vpnuser && \
    echo "vpnuser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    mkdir -p /etc/openvpn && \
    chown -R vpnuser:vpnuser /etc/openvpn

# Create configs directory and add OpenVPN config
COPY configs/ /etc/openvpn/
RUN if [ ! -f /etc/openvpn/windscribe.ovpn ]; then \
        echo "ERROR: Missing OpenVPN config file. Please download from Windscribe and place in configs/windscribe.ovpn" && \
        exit 1; \
    fi && \
    mv /etc/openvpn/windscribe.ovpn /etc/openvpn/windscribe.conf && \
    dos2unix /etc/openvpn/windscribe.conf && \
    chown vpnuser:vpnuser /etc/openvpn/windscribe.conf && \
    chmod 644 /etc/openvpn/windscribe.conf

# Fix log permissions and create required directories
RUN mkdir -p /var/log/openvpn && \
    mkdir -p /dev/net && \
    touch /var/log/openvpn/openvpn.log && \
    chown -R vpnuser:vpnuser /var/log/openvpn && \
    chmod -R 755 /var/log/openvpn && \
    mknod /dev/net/tun c 10 200 || true

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Create and setup logs directory
RUN mkdir -p /app/logs && \
    chown -R vpnuser:vpnuser /app/logs && \
    chmod 755 /app/logs

# Create and activate virtual environment, then install dependencies
RUN python3 -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Fix line endings and make executable
RUN dos2unix /app/startup.sh && \
    chmod +x /app/startup.sh && \
    chown root:root /app/startup.sh

# Fix permissions for application
RUN chown -R vpnuser:vpnuser /app /venv

# Set shell to bash
SHELL ["/bin/bash", "-c"]

# Switch to vpnuser
USER vpnuser

# Initialize services and start script
ENTRYPOINT ["/bin/bash", "-c", "/app/startup.sh"]