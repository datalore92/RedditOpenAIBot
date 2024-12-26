#!/bin/bash
set -x

echo "[$(date)] Starting up..."
mkdir -p /app/logs
sudo chown -R vpnuser:vpnuser /app/logs  # Fix permissions

# Setup DNS 
echo "[$(date)] Setting up DNS..."
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
echo "nameserver 8.8.4.4" | sudo tee -a /etc/resolv.conf

# Test DNS
echo "[$(date)] Testing DNS..."
if ! ping -c 1 google.com >/dev/null 2>&1; then
    echo "ERROR: DNS not working"
    exit 1
fi

echo "[$(date)] Starting VPN..."
# Get original IP before VPN
echo "[$(date)] Original IP: $(curl -s https://ipinfo.io/ip)"

# Create VPN status log
VPN_STATUS_FILE="/app/logs/vpn_status.log"
echo "VPN Status Log - $(date)" > $VPN_STATUS_FILE
echo "----------------------------------------" >> $VPN_STATUS_FILE
echo "Original IP: $(curl -s https://ipinfo.io/ip)" >> $VPN_STATUS_FILE
echo "Original Location: $(curl -s https://ipinfo.io/city), $(curl -s https://ipinfo.io/country)" >> $VPN_STATUS_FILE
echo "Original ISP: $(curl -s https://ipinfo.io/org)" >> $VPN_STATUS_FILE
echo "----------------------------------------" >> $VPN_STATUS_FILE

# Create OpenVPN credentials from environment variables
echo -e "${OPENVPN_USERNAME}\n${OPENVPN_PASSWORD}" > /etc/openvpn/credentials
chmod 600 /etc/openvpn/credentials
chown vpnuser:vpnuser /etc/openvpn/credentials

# Start OpenVPN with better logging
echo "[$(date)] Starting OpenVPN..."
sudo openvpn \
    --config /etc/openvpn/windscribe.conf \
    --auth-user-pass /etc/openvpn/credentials \
    --log /var/log/openvpn/openvpn.log \
    --log-append /var/log/openvpn/openvpn.log \
    --status /app/logs/status.log 1 \
    --verb 4 \
    --suppress-timestamps \
    --daemon

# Add immediate log check
sleep 2
if [ -f /var/log/openvpn/openvpn.log ]; then
    echo "Initial OpenVPN log contents:"
    cat /var/log/openvpn/openvpn.log
fi

# Wait for VPN connection with better debugging
echo "[$(date)] Waiting for VPN connection..."
connection_timeout=60  # Increase timeout to 60 seconds
for i in $(seq 1 $connection_timeout); do
    # Check both tun0 existence and "Initialization Sequence Completed" message
    if ip addr show tun0 >/dev/null 2>&1 && grep -q "Initialization Sequence Completed" /var/log/openvpn/openvpn.log; then
        echo "[$(date)] VPN interface detected and initialized"
        sleep 5  # Give routing time to stabilize
        
        # Test VPN connection
        echo "[$(date)] Testing VPN connection..."
        if ! curl -s https://ipinfo.io/ip >/dev/null; then
            echo "ERROR: Cannot reach internet through VPN"
            exit 1
        fi
        
        # Get VPN connection details with error checking
        NEW_IP=$(curl -s https://ipinfo.io/ip)
        if [ -z "$NEW_IP" ]; then
            echo "ERROR: Could not get new IP address"
            exit 1
        fi
        
        NEW_CITY=$(curl -s https://ipinfo.io/city)
        NEW_REGION=$(curl -s https://ipinfo.io/region)
        NEW_COUNTRY=$(curl -s https://ipinfo.io/country)
        NEW_ISP=$(curl -s https://ipinfo.io/org)
        
        # Debug output
        echo "[$(date)] VPN Connection Info:"
        echo "New IP: $NEW_IP"
        echo "Location: $NEW_CITY, $NEW_REGION, $NEW_COUNTRY"
        echo "ISP: $NEW_ISP"
        
        # Check if IP actually changed
        if [ "$NEW_IP" = "$(grep 'Original IP:' $VPN_STATUS_FILE | cut -d' ' -f3)" ]; then
            echo "ERROR: VPN connected but IP did not change!"
            exit 1
        fi
        
        # Log successful connection
        {
            echo "VPN Connection Established - $(date)"
            echo "----------------------------------------"
            echo "New IP: $NEW_IP"
            echo "VPN Location: $NEW_CITY, $NEW_REGION, $NEW_COUNTRY"
            echo "VPN ISP: $NEW_ISP"
            echo "Connection Time: $(date)"
            echo "Interface: tun0"
            echo "----------------------------------------"
        } >> $VPN_STATUS_FILE
        
        break
    fi
    echo "[$(date)] Waiting for VPN... ($i/$connection_timeout)"
    # Check OpenVPN logs for errors
    if [ -f "/var/log/openvpn/openvpn.log" ]; then
        tail -n 5 /var/log/openvpn/openvpn.log
    fi
    sleep 1
done

# Check if we actually connected - improved check
if ! (ip addr show tun0 >/dev/null 2>&1 && grep -q "Initialization Sequence Completed" /var/log/openvpn/openvpn.log); then
    echo "ERROR: Failed to establish VPN connection after $connection_timeout seconds"
    echo "Last few lines of OpenVPN log:"
    tail -n 20 /var/log/openvpn/openvpn.log
    exit 1
fi

# Start periodic status updates in background
(while true; do
    sleep 300  # Update every 5 minutes
    CURRENT_IP=$(curl -s https://ipinfo.io/ip)
    echo "[$(date)] VPN Status Check" >> $VPN_STATUS_FILE
    echo "Current IP: $CURRENT_IP" >> $VPN_STATUS_FILE
    echo "----------------------------------------" >> $VPN_STATUS_FILE
done) &

# Show network info
echo "[$(date)] Network info:"
ip route
ip addr

# Verify internet connectivity through VPN
echo "[$(date)] Testing internet connectivity through VPN..."
if ! ping -c 1 8.8.8.8; then
    echo "ERROR: No internet connectivity through VPN"
    exit 1
fi

if ! curl -s https://ipinfo.io/ip >/dev/null; then
    echo "ERROR: Cannot access internet through VPN"
    exit 1
fi

echo "[$(date)] Starting bot..."
if ! /venv/bin/python3 -m src.bot; then
    echo "ERROR: Bot failed to start"
    exit 1
fi

# Keep container running - only if bot exits normally
tail -f /dev/null
