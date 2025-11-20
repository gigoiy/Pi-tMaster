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
cp -r src/* $INSTALL_DIR/

# Step 4: Setup CPU power helper script
echo -e "\n${YELLOW}[4/7] Setting up CPU power helper script...${NC}"

# Copy helper script to system location
sudo cp $INSTALL_DIR/scripts/cpu-power-helper.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/cpu-power-helper.sh

# Setup sudo permissions for the helper script
echo "$SERVICE_USER ALL=(ALL) NOPASSWD: /sbin/shutdown, /sbin/reboot, /usr/local/bin/cpu-power-helper.sh" | sudo tee /etc/sudoers.d/pitmaster
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
sleep 3

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

# Test helper script
echo -e "\n${YELLOW}Testing CPU power helper...${NC}"
if sudo /usr/local/bin/cpu-power-helper.sh get-status > /dev/null 2>&1; then
    echo -e "CPU power helper: ${GREEN}WORKING${NC}"
else
    echo -e "CPU power helper: ${RED}NOT WORKING${NC}"
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
echo -e "   http://pitmaster.local:8080"
echo -e ""
echo -e "${YELLOW}Installation directory:${NC} $INSTALL_DIR"
echo -e "${YELLOW}Virtual environment:${NC} $INSTALL_DIR/pitmaster"
echo -e ""
echo -e "${YELLOW}Useful commands:${NC}"
echo -e "   sudo systemctl stop pitmaster.service    # Stop service"
echo -e "   sudo systemctl start pitmaster.service   # Start service"
echo -e "   sudo systemctl restart pitmaster.service # Restart service"
echo -e "   sudo journalctl -u pitmaster.service -f  # View logs"
echo -e ""
echo -e "${YELLOW}Power Management:${NC}"
echo -e "   The web interface now supports dynamic power mode switching!"
echo -e "   - Low Power: 300-600 MHz (powersave governor)"
echo -e "   - Full Power: 600-1500 MHz (ondemand governor)"
echo -e ""
echo -e "${YELLOW}Sensor Wiring Guide:${NC}"
echo -e "   All MAX6675 chips share:"
echo -e "   - SO  → GPIO9  (pin 21) - MISO"
echo -e "   - SCLK → GPIO11 (pin 23) - SCLK"
echo -e "   - VCC  → 5V"
echo -e "   - GND  → GND"
echo -e ""
echo -e "   Individual CS lines:"
echo -e "   - Left probe  CS → GPIO8  (pin 24)"
echo -e "   - Right probe CS → GPIO7  (pin 26)"
echo -e "   - Meat probe  CS → GPIO16 (pin 36)"
echo -e ""

echo -e "${GREEN}Enjoy your PitMaster! 🥩🔥${NC}"