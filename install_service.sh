#!/bin/bash

# FreeGPT API Service Installation Script
# This script installs the FreeGPT API as a systemd service

set -e

echo "=========================================="
echo "FreeGPT API Service Installation"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root or with sudo"
    echo "Usage: sudo ./install_service.sh"
    exit 1
fi

# Get the actual user (not root) and their primary group
ACTUAL_USER="${SUDO_USER:-$USER}"
ACTUAL_GROUP=$(id -gn "$ACTUAL_USER")
SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing FreeGPT API service..."
echo "Service directory: $SERVICE_DIR"
echo "User: $ACTUAL_USER"
echo "Group: $ACTUAL_GROUP"
echo ""

# Create service file with actual user/group/path
echo "1. Creating service file with your configuration..."
cat > /tmp/freegpt-api.service << EOF
[Unit]
Description=FreeGPT OpenAI-Compatible API Server
After=network.target

[Service]
Type=simple
User=$ACTUAL_USER
Group=$ACTUAL_GROUP
WorkingDirectory=$SERVICE_DIR
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"

# Load environment variables from .env file
EnvironmentFile=-$SERVICE_DIR/.env

# Start the API server
ExecStart=/usr/bin/python3 -m uvicorn api:app --host 0.0.0.0 --port 8000

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=freegpt-api

[Install]
WantedBy=multi-user.target
EOF

# Copy to systemd
cp /tmp/freegpt-api.service /etc/systemd/system/
chmod 644 /etc/systemd/system/freegpt-api.service
rm /tmp/freegpt-api.service

# Reload systemd daemon
echo "2. Reloading systemd daemon..."
systemctl daemon-reload

# Enable service to start on boot
echo "3. Enabling service to start on boot..."
systemctl enable freegpt-api.service

# Start the service now
echo "4. Starting the service..."
systemctl start freegpt-api.service

# Wait a moment for service to start
sleep 2

# Check status
echo ""
echo "=========================================="
echo "Service Status:"
echo "=========================================="
systemctl status freegpt-api.service --no-pager || true

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Service commands:"
echo "  sudo systemctl start freegpt-api     - Start the service"
echo "  sudo systemctl stop freegpt-api      - Stop the service"
echo "  sudo systemctl restart freegpt-api   - Restart the service"
echo "  sudo systemctl status freegpt-api    - Check service status"
echo "  sudo journalctl -u freegpt-api -f    - View live logs"
echo ""
echo "The API server is now running at: http://localhost:8000"
echo "API will automatically start on system reboot."
echo ""
