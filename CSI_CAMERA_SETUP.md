# CSI Camera Setup for Raspberry Pi

## Overview
This project now supports both USB cameras (via V4L2) and CSI cameras (via libcamera) for Raspberry Pi Camera Modules.

## Hardware Requirements
- Raspberry Pi (any model with CSI camera connector)
- Raspberry Pi Camera Module (v1, v2, v3, or HQ Camera)
- Properly connected camera ribbon cable (blue strip faces USB ports)

## Installation on Raspberry Pi

### 1. Enable Camera Interface
```bash
sudo raspi-config
```
Navigate to: **Interface Options → Camera → Enable**

Then reboot:
```bash
sudo reboot
```

### 2. Install Required Packages
Run the automated setup script:
```bash
cd /path/to/PodCam
chmod +x setup_csi_camera.sh
./setup_csi_camera.sh
```

Or install manually:
```bash
# Update system
sudo apt update

# Install libcamera apps
sudo apt install -y libcamera-apps

# Install picamera2 Python library
sudo apt install -y python3-picamera2 python3-libcamera

# If using virtual environment
source .venv/bin/activate
pip install picamera2
```

### 3. Test Camera Connection
```bash
# Test with libcamera (5 second preview)
libcamera-hello -t 5000

# List available cameras
libcamera-hello --list-cameras

# Capture a test image
libcamera-still -o test.jpg
```

## Usage

### Automatic Detection
The web stream server will automatically detect CSI cameras and use them:
```bash
python3 web_stream.py
```

The program will:
1. Check for CSI cameras first (using libcamera)
2. Fall back to USB cameras if no CSI cameras found
3. Log which type of camera is being used

### Camera Configuration
Edit `config.py` to adjust camera settings:
- Resolution (width/height)
- Frame rate
- JPEG quality
- Overlay settings

## Troubleshooting

### Camera Not Detected
```bash
# Check if camera is recognized
libcamera-hello --list-cameras

# Check for errors
dmesg | grep -i camera

# Verify camera interface is enabled
vcgencmd get_camera
# Should show: supported=1 detected=1
```

### "Camera is not enabled" Error
1. Run `sudo raspi-config`
2. Enable camera interface
3. Reboot the Pi
4. Test again with `libcamera-hello -t 5000`

### Cable Connection Issues
- Blue strip on ribbon cable faces **toward** USB ports on Pi
- Cable firmly seated in both camera and Pi connectors
- Black tabs on connectors pulled up before inserting cable
- No visible damage to ribbon cable

### Permission Issues
```bash
# Add user to video group
sudo usermod -a -G video $USER

# Logout and login again for group changes to take effect
```

### Dependency Issues
```bash
# Reinstall picamera2
pip uninstall picamera2
sudo apt install --reinstall python3-picamera2

# Check Python can import it
python3 -c "import picamera2; print('picamera2 OK')"
```

## Camera Module Specifications

### Raspberry Pi Camera Module v2
- Resolution: 8MP (3280 x 2464)
- Video: 1080p30, 720p60
- Sensor: Sony IMX219

### Raspberry Pi Camera Module v3
- Resolution: 12MP (4608 x 2592)
- Video: 1080p50, 720p100
- Sensor: Sony IMX708
- Improved low-light performance

### Raspberry Pi HQ Camera
- Resolution: 12.3MP (4056 x 3040)
- C/CS-mount for interchangeable lenses
- Sensor: Sony IMX477

## Features

### Automatic Camera Type Detection
- CSI cameras detected via libcamera
- USB cameras detected via V4L2
- Seamless fallback between types

### Unified Interface
- Same code works for both camera types
- OpenCV-compatible API
- Consistent configuration

### Performance Optimizations
- Native libcamera integration for CSI cameras
- Hardware-accelerated encoding
- Adjustable resolution and frame rates

## Differences Between USB and CSI

| Feature | USB Camera (V4L2) | CSI Camera (libcamera) |
|---------|-------------------|------------------------|
| Connection | USB port | CSI ribbon cable |
| Bandwidth | USB 2.0/3.0 limit | Dedicated CSI interface |
| Latency | Higher | Lower |
| CPU Usage | Moderate | Lower (hardware encoding) |
| Resolution | Varies by model | Up to 12MP |
| Installation | Plug-and-play | Requires cable setup |

## Code Integration

The `libcamera_capture.py` module provides:
- `LibcameraCapture` class - OpenCV-compatible camera interface
- `detect_csi_cameras()` - Auto-detect available CSI cameras
- `is_libcamera_available()` - Check if libcamera is installed

Example usage:
```python
from libcamera_capture import LibcameraCapture

# Create CSI camera capture
cap = LibcameraCapture(0)

# Configure resolution and frame rate
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 30)

# Start capture
cap.start()

# Read frames (OpenCV compatible)
ret, frame = cap.read()

# Release when done
cap.release()
```

## References
- [Raspberry Pi Camera Documentation](https://www.raspberrypi.com/documentation/accessories/camera.html)
- [libcamera Documentation](https://libcamera.org/)
- [picamera2 Library](https://github.com/raspberrypi/picamera2)
