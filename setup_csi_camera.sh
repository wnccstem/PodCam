#!/bin/bash
# Setup script for CSI camera support on Raspberry Pi

echo "Setting up CSI Camera Support for PodCam"
echo "========================================"
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This does not appear to be a Raspberry Pi"
    echo "CSI camera support requires Raspberry Pi hardware"
    echo ""
fi

# Check if libcamera is installed
echo "Checking for libcamera installation..."
if command -v libcamera-hello &> /dev/null; then
    echo "✓ libcamera-apps is installed"
    libcamera-hello --version
else
    echo "✗ libcamera-apps not found"
    echo "Installing libcamera-apps..."
    sudo apt update
    sudo apt install -y libcamera-apps
fi

echo ""
echo "Checking Python environment..."

# Check if picamera2 is installed
if python3 -c "import picamera2" 2>/dev/null; then
    echo "✓ picamera2 is installed"
else
    echo "✗ picamera2 not found"
    echo "Installing picamera2..."
    
    # Install dependencies
    sudo apt install -y python3-picamera2 python3-libcamera
    
    # If virtual environment exists, install there too
    if [ -d ".venv" ]; then
        echo "Installing picamera2 in virtual environment..."
        source .venv/bin/activate
        pip install picamera2
    fi
fi

echo ""
echo "Detecting cameras..."
echo ""

# List available cameras
echo "=== Libcamera Devices ==="
libcamera-hello --list-cameras

echo ""
echo "=== V4L2 Devices (USB Cameras) ==="
if command -v v4l2-ctl &> /dev/null; then
    v4l2-ctl --list-devices
else
    ls -l /dev/video* 2>/dev/null || echo "No /dev/video* devices found"
fi

echo ""
echo "========================================"
echo "Setup complete!"
echo ""
echo "To test your CSI camera, run:"
echo "  libcamera-hello -t 5000"
echo ""
echo "To start the web stream with CSI support:"
echo "  python3 web_stream.py"
echo ""
echo "Troubleshooting tips:"
echo "1. Check camera cable connection (blue strip toward USB ports)"
echo "2. Enable camera in raspi-config: sudo raspi-config → Interface Options → Camera"
echo "3. Reboot after enabling: sudo reboot"
echo "4. Test with: libcamera-still -o test.jpg"
echo ""
