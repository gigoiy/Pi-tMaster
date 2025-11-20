#!/bin/bash
# PitMaster Installation Script

set -e  # Exit on any error

echo "=========================================="
echo "    PitMaster Installation Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Error: Do not run as root. Use regular user account.${NC}"
    exit 1
fi

# Configuration
INSTALL_DIR="$HOME/PitMaster"
SERVICE_USER=$(whoami)

echo -e "${YELLOW}Installing PitMaster for user: $SERVICE_USER${NC}"

# Step 1: System updates and dependencies
echo -e "\n${YELLOW}[1/7] Installing system dependencies...${NC}"
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv python3-dev git

# Step 2: Enable SPI interface
echo -e "\n${YELLOW}[2/7] Enabling SPI interface...${NC}"
sudo raspi-config nonint do_spi 0

# Step 3: Create installation directory
echo -e "\n${YELLOW}[3/7] Creating installation directory...${NC}"
mkdir -p $INSTALL_DIR
mkdir -p $INSTALL_DIR/scripts

# Step 4: Setup CPU power helper script
echo -e "\n${YELLOW}[4/7] Setting up CPU power helper script...${NC}"

# Copy helper script to system location
sudo cp $INSTALL_DIR/scripts/cpu-power-helper.sh /usr/local/bin/
sudo chmod 755 /usr/local/bin/cpu-power-helper.sh

# Verify helper script syntax
echo -e "${YELLOW}Checking helper script syntax...${NC}"
if bash -n /usr/local/bin/cpu-power-helper.sh; then
    echo -e "${GREEN}Helper script syntax is valid${NC}"
else
    echo -e "${RED}Helper script has syntax errors${NC}"
    exit 1
fi

# Setup sudo permissions for the helper script
echo -e "${YELLOW}Setting up sudo permissions...${NC}"
echo "$SERVICE_USER ALL=(ALL) NOPASSWD: /usr/local/bin/cpu-power-helper.sh" | sudo tee /etc/sudoers.d/pitmaster
sudo chmod 440 /etc/sudoers.d/pitmaster

# Step 5: Setup Python virtual environment
echo -e "\n${YELLOW}[5/7] Setting up Python virtual environment...${NC}"
cd $INSTALL_DIR
python3 -m venv pitmaster
source pitmaster/bin/activate

# Install Python dependencies
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 6: Setup systemd services
echo -e "\n${YELLOW}[6/7] Setting up system services...${NC}"

# Update service files with actual username
sed -i "s/User=shmeggle/User=$SERVICE_USER/g" systemd/pitmaster.service
sed -i "s|/home/shmeggle|$HOME|g" systemd/pitmaster.service

# Copy service files
sudo cp systemd/pitmaster.service /etc/systemd/system/
sudo cp systemd/cpu-power.service /etc/systemd/system/

# Step 7: Enable and start services
echo -e "\n${YELLOW}[7/7] Starting services...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable cpu-power.service
sudo systemctl enable pitmaster.service
sudo systemctl start cpu-power.service
sudo systemctl start pitmaster.service

# Wait a moment for services to start
sleep 5

# Check service status
echo -e "\n${YELLOW}Service Status:${NC}"
if systemctl is-active --quiet pitmaster.service; then
    echo -e "pitmaster.service: ${GREEN}ACTIVE${NC}"
else
    echo -e "pitmaster.service: ${RED}INACTIVE${NC}"
    sudo systemctl status pitmaster.service --no-pager
fi

if systemctl is-active --quiet cpu-power.service; then
    echo -e "cpu-power.service: ${GREEN}ACTIVE${NC}"
else
    echo -e "cpu-power.service: ${RED}INACTIVE${NC}"
    sudo systemctl status cpu-power.service --no-pager
fi

# Test helper script thoroughly
echo -e "\n${YELLOW}Testing CPU power helper...${NC}"
echo -e "${YELLOW}Testing as current user...${NC}"
if /usr/local/bin/cpu-power-helper.sh get-status > /dev/null 2>&1; then
    echo -e "Direct helper script: ${GREEN}WORKING${NC}"
else
    echo -e "Direct helper script: ${RED}FAILED${NC}"
fi

echo -e "${YELLOW}Testing with sudo...${NC}"
if sudo /usr/local/bin/cpu-power-helper.sh get-status > /dev/null 2>&1; then
    echo -e "Sudo helper script: ${GREEN}WORKING${NC}"
    
    # Test actual output
    echo -e "${YELLOW}Testing actual output...${NC}"
    sudo /usr/local/bin/cpu-power-helper.sh get-status
else
    echo -e "Sudo helper script: ${RED}FAILED${NC}"
    echo -e "${YELLOW}Debug info:${NC}"
    ls -la /usr/local/bin/cpu-power-helper.sh
    sudo /usr/local/bin/cpu-power-helper.sh get-status
fi

# Get IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')

echo -e "\n${GREEN}==========================================${NC}"
echo -e "${GREEN}        INSTALLATION COMPLETE!${NC}"
echo -e "${GREEN}==========================================${NC}"
echo -e "PitMaster is now running and will start automatically on boot."
echo -e ""
echo -e "${YELLOW}Access your PitMaster at:${NC}"
echo -e "   http://$IP_ADDRESS:8080"
echo -e ""
echo -e "${YELLOW}If power management doesn't work:${NC}"
echo -e "1. Check helper script: sudo /usr/local/bin/cpu-power-helper.sh get-status"
echo -e "2. Check sudoers: sudo visudo -c"
echo -e "3. Check service logs: sudo journalctl -u pitmaster.service -f"
echo -e ""
echo -e "${GREEN}Enjoy your PitMaster! 🥩🔥${NC}"