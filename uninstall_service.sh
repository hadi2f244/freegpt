#!/bin/bash

# FreeGPT API Service Uninstallation Script

set -e

echo "=========================================="
echo "FreeGPT API Service Uninstallation"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root or with sudo"
    echo "Usage: sudo ./uninstall_service.sh"
    exit 1
fi

echo "Uninstalling FreeGPT API service..."
echo ""

# Stop the service
echo "1. Stopping the service..."
systemctl stop freegpt-api.service || true

# Disable service from starting on boot
echo "2. Disabling service from starting on boot..."
systemctl disable freegpt-api.service || true

# Remove service file
echo "3. Removing service file..."
rm -f /etc/systemd/system/freegpt-api.service

# Reload systemd daemon
echo "4. Reloading systemd daemon..."
systemctl daemon-reload

echo ""
echo "=========================================="
echo "✅ Uninstallation Complete!"
echo "=========================================="
echo ""
echo "The FreeGPT API service has been removed."
echo "Your code and data remain in: /home/h.azaddel@asax.local/code/asax/freegpt"
echo ""
