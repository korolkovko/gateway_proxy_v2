#!/bin/bash
# Gateway Proxy systemd service installer
# Run as: sudo ./install_service.sh

set -e  # Exit on error

echo "🚀 Installing Gateway Proxy as systemd service..."

# Get current directory (where the script is located)
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="gateway-proxy.service"
SYSTEMD_DIR="/etc/systemd/system"

echo "📂 Installation directory: $INSTALL_DIR"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo ./install_service.sh"
    exit 1
fi

# Check if service file exists
if [ ! -f "$INSTALL_DIR/$SERVICE_FILE" ]; then
    echo "❌ Service file not found: $SERVICE_FILE"
    exit 1
fi

# Check if .env exists
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo "⚠️  Warning: .env file not found. Make sure to create it before starting the service."
fi

# Copy service file to systemd directory
echo "📋 Copying service file to $SYSTEMD_DIR..."
cp "$INSTALL_DIR/$SERVICE_FILE" "$SYSTEMD_DIR/"

# Replace placeholder paths with actual installation directory
echo "🔧 Updating paths in service file..."
sed -i.bak "s|/opt/gateway_proxy_v2|$INSTALL_DIR|g" "$SYSTEMD_DIR/$SERVICE_FILE"

# Get current user (the one who ran sudo)
ACTUAL_USER="${SUDO_USER:-$USER}"
echo "👤 Setting service user to: $ACTUAL_USER"
sed -i.bak "s|User=kiosk|User=$ACTUAL_USER|g" "$SYSTEMD_DIR/$SERVICE_FILE"
sed -i.bak "s|Group=kiosk|Group=$ACTUAL_USER|g" "$SYSTEMD_DIR/$SERVICE_FILE"

# Remove backup file
rm -f "$SYSTEMD_DIR/$SERVICE_FILE.bak"

# Reload systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# Enable service (autostart on boot)
echo "✅ Enabling service for autostart..."
systemctl enable gateway-proxy

echo ""
echo "✅ Installation complete!"
echo ""
echo "📚 Available commands:"
echo "  sudo systemctl start gateway-proxy      # Start the service"
echo "  sudo systemctl stop gateway-proxy       # Stop the service"
echo "  sudo systemctl restart gateway-proxy    # Restart the service"
echo "  sudo systemctl status gateway-proxy     # Check status"
echo "  sudo journalctl -u gateway-proxy -f     # View logs (real-time)"
echo ""
echo "🎯 To start now, run:"
echo "  sudo systemctl start gateway-proxy"
echo ""
