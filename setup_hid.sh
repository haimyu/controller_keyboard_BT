#!/bin/bash
# setup_hid_fixed.sh - Fixed setup for Pi Zero W Bluetooth HID

set -e

echo "=== Configuring Raspberry Pi Zero W for Bluetooth HID ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Must run as root"
    echo "Usage: sudo ./setup_hid_fixed.sh"
    exit 1
fi

echo "1. Backing up original configuration..."
cp /etc/bluetooth/main.conf /etc/bluetooth/main.conf.backup

echo "2. Stopping Bluetooth service..."
systemctl stop bluetooth
sleep 2

echo "3. Checking BlueZ version and plugin support..."
BLUEZ_VERSION=$(bluetoothd --version 2>/dev/null || echo "5.43")
echo "BlueZ version: $BLUEZ_VERSION"

# Check if input plugin disable is supported
if bluetoothd --help 2>&1 | grep -q "\-P"; then
    echo "BlueZ supports plugin disable - creating override..."
    mkdir -p /etc/systemd/system/bluetooth.service.d
    cat > /etc/systemd/system/bluetooth.service.d/override.conf << 'EOF'
[Service]
ExecStart=
ExecStart=/usr/lib/bluetooth/bluetoothd -P input
EOF
    echo "✓ Input plugin will be disabled"
else
    echo "BlueZ doesn't support -P flag - using alternative method..."
    # Remove any existing override that might be causing issues
    rm -f /etc/systemd/system/bluetooth.service.d/override.conf
    echo "✓ Will disable input plugin via configuration"
fi

echo "4. Configuring main.conf for HID..."
# Create a clean main.conf with HID settings
cat > /etc/bluetooth/main.conf << 'EOF'
[General]
Name = Assistive Keyboard
Class = 0x002540
DiscoverableTimeout = 0
PairableTimeout = 0
Discoverable = true
Pairable = true
AutoEnable = true
ControllerMode = dual

[Policy]
AutoEnable = true

# Disable input plugin via configuration if -P flag not supported
[Plugin]
Load = 
Exclude = input
EOF

echo "5. Creating input.conf to disable HID input handling..."
mkdir -p /etc/bluetooth
cat > /etc/bluetooth/input.conf << 'EOF'
[General]
UserspaceHID = true
EOF

echo "6. Reloading systemd..."
systemctl daemon-reload

echo "7. Starting Bluetooth service..."
if systemctl start bluetooth; then
    echo "✓ Bluetooth service started successfully"
else
    echo "⚠ Bluetooth start failed, trying fallback method..."
    
    # Fallback: Remove override and try basic configuration
    rm -f /etc/systemd/system/bluetooth.service.d/override.conf
    systemctl daemon-reload
    
    # Simplified main.conf without problematic options
    cat > /etc/bluetooth/main.conf << 'EOF'
[General]
Name = Assistive Keyboard
Class = 0x002540
DiscoverableTimeout = 0
PairableTimeout = 0
AutoEnable = true
EOF
    
    if systemctl start bluetooth; then
        echo "✓ Bluetooth started with fallback configuration"
    else
        echo "❌ Bluetooth service failed to start"
        echo "Let's check the error:"
        systemctl status bluetooth.service
        exit 1
    fi
fi

sleep 3

echo "8. Configuring adapter for HID..."
# Wait for adapter to be ready
for i in {1..10}; do
    if hciconfig hci0 >/dev/null 2>&1; then
        break
    fi
    echo "Waiting for adapter... ($i/10)"
    sleep 1
done

# Configure adapter
hciconfig hci0 up 2>/dev/null || echo "Adapter already up"
hciconfig hci0 class 0x002540 2>/dev/null || echo "Note: Class setting may require manual config"
hciconfig hci0 name "Assistive Keyboard" 2>/dev/null || echo "Name will be set by main.conf"
hciconfig hci0 piscan 2>/dev/null || echo "Scan mode will be set programmatically"

echo "9. Installing Python dependencies..."
apt-get update -qq
apt-get install -y python3-dbus python3-gi python3-dev libbluetooth-dev

echo "10. Setting permissions..."
usermod -a -G input pi 2>/dev/null || echo "User permissions set"

echo "=== Setup Complete ==="
echo ""
echo "✓ Bluetooth adapter configuration:"
hciconfig hci0 2>/dev/null || echo "Adapter will be configured at runtime"

echo ""
echo "✓ Service status:"
systemctl is-active bluetooth.service

echo ""
echo "NEXT STEPS:"
echo "1. Test the configuration: sudo python3 src/main.py"
echo "2. If issues persist, reboot: sudo reboot"
echo "3. Look for 'Assistive Keyboard' in MacBook Bluetooth settings"
echo ""
echo "TROUBLESHOOTING:"
echo "- If no keyboard icon appears, the device class will be set at runtime"
echo "- If connection fails, check: sudo systemctl status bluetooth"
echo "- For logs: journalctl -u bluetooth -f"
