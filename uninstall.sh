#!/bin/bash
# PitMaster Uninstall Script

echo "=========================================="
echo "    PitMaster Uninstall Script"
echo "=========================================="

INSTALL_DIR="$HOME/PitMaster"

# Stop and disable services
echo "Stopping services..."
sudo systemctl stop pitmaster.service
sudo systemctl stop cpu-power.service
sudo systemctl disable pitmaster.service
sudo systemctl disable cpu-power.service

# Remove service files
echo "Removing service files..."
sudo rm -f /etc/systemd/system/pitmaster.service
sudo rm -f /etc/systemd/system/cpu-power.service

# Remove CPU power helper script
echo "Removing CPU power helper script..."
sudo rm -f /usr/local/bin/cpu-power-helper.sh

# Remove sudoers configuration
echo "Removing sudoers configuration..."
sudo rm -f /etc/sudoers.d/pitmaster

# Reload systemd and sudoers
sudo systemctl daemon-reload

# Remove installation directory
echo "Removing installation directory..."
rm -rf $INSTALL_DIR

echo "=========================================="
echo "    Uninstall Complete!"
echo "=========================================="