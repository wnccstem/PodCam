# Quick Start: CSI Camera Setup

## On Raspberry Pi

1. **Enable camera interface:**
   ```bash
   sudo raspi-config
   # Interface Options → Camera → Enable
   sudo reboot
   ```

2. **Run setup script:**
   ```bash
   chmod +x setup_csi_camera.sh
   ./setup_csi_camera.sh
   ```

3. **Test camera:**
   ```bash
   libcamera-hello -t 5000
   ```

4. **Start web stream:**
   ```bash
   python3 web_stream.py
   ```

## Camera Detection Priority

The program automatically detects cameras in this order:
1. CSI cameras (via libcamera) - if available
2. USB cameras at known index (if configured)
3. USB cameras by scanning indices 0-3

## Files Added

- `libcamera_capture.py` - CSI camera support module
- `setup_csi_camera.sh` - Automated setup script
- `CSI_CAMERA_SETUP.md` - Detailed documentation

## Configuration

Edit `config.py` for camera settings:
- `KNOWN_CAMERA_INDEX` - Skip detection for faster startup
- Resolution and FPS for each camera
- Overlay and rotation settings

## Troubleshooting

**Camera not detected:**
```bash
libcamera-hello --list-cameras
vcgencmd get_camera  # Should show: supported=1 detected=1
```

**Cable connection:**
- Blue strip faces USB ports
- Cable firmly seated
- No visible damage

**Permissions:**
```bash
sudo usermod -a -G video $USER
# Logout and login again
```

## Testing on Windows

This code is developed on Windows but runs on Raspberry Pi. The import errors for `picamera2` and `libcamera` on Windows are normal and expected.

Deploy to Raspberry Pi to test CSI camera functionality.
