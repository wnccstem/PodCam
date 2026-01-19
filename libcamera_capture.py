#!/usr/bin/env python3
"""
Libcamera Capture Module for CSI Cameras on Raspberry Pi

This module provides a wrapper around libcamera-vid for capturing frames
from CSI-connected cameras. It creates a compatible interface with OpenCV
VideoCapture for seamless integration.

Hardware Support:
- Raspberry Pi Camera Module v1, v2, v3
- Raspberry Pi HQ Camera
- Any CSI-connected camera supported by libcamera

Requirements:
- libcamera stack present (provided by Raspberry Pi OS / Debian)
- picamera2 library (usually via apt: python3-picamera2)
- rpicam-apps or libcamera-tools optional for CLI diagnostics

sudo apt install libcamera-dev
"""

import subprocess
import time
# import numpy as np
# from typing import Optional, Tuple
from threading import Lock
import logging
import shutil

logger = logging.getLogger(__name__)

try:
    from picamera2 import Picamera2
    from libcamera import controls
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    logger.warning("picamera2 not available - CSI camera support disabled")


class LibcameraCapture:
    """
    Wrapper class for libcamera that mimics OpenCV VideoCapture interface.
    This allows CSI cameras to work with existing OpenCV-based code.
    """

    def __init__(self, camera_index=0):
        """
        Initialize libcamera capture.
        
        Args:
            camera_index: Camera index (0 for first CSI camera)
        """
        if not PICAMERA2_AVAILABLE:
            raise RuntimeError("picamera2 library not installed. Install with: pip install picamera2")
        
        self.camera_index = camera_index
        self.camera = None
        self.width = 640
        self.height = 480
        self.fps = 10.0
        self.is_opened = False
        self.lock = Lock()
        self.current_frame = None
        
        # Try to initialize the camera
        try:
            self.camera = Picamera2(camera_index)
            logger.info(f"Libcamera: Detected camera {camera_index}")
            self.is_opened = True
        except Exception as e:
            logger.error(f"Failed to initialize libcamera camera {camera_index}: {e}")
            self.is_opened = False

    def isOpened(self):
        """Check if camera is successfully opened."""
        return self.is_opened

    def set(self, prop_id, value):
        """
        Set camera property (mimics cv2.VideoCapture.set).
        
        Args:
            prop_id: Property ID (use cv2.CAP_PROP_* constants)
            value: Value to set
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_opened:
            return False

        import cv2
        
        try:
            if prop_id == cv2.CAP_PROP_FRAME_WIDTH:
                self.width = int(value)
                return True
            elif prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
                self.height = int(value)
                return True
            elif prop_id == cv2.CAP_PROP_FPS:
                self.fps = float(value)
                return True
            else:
                logger.debug(f"Libcamera: Property {prop_id} not supported")
                return False
        except Exception as e:
            logger.error(f"Failed to set property {prop_id}: {e}")
            return False

    def get(self, prop_id):
        """
        Get camera property (mimics cv2.VideoCapture.get).
        
        Args:
            prop_id: Property ID (use cv2.CAP_PROP_* constants)
        
        Returns:
            Property value, or 0 if not available
        """
        if not self.is_opened:
            return 0

        import cv2
        
        try:
            if prop_id == cv2.CAP_PROP_FRAME_WIDTH:
                return float(self.width)
            elif prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
                return float(self.height)
            elif prop_id == cv2.CAP_PROP_FPS:
                return self.fps
            else:
                return 0
        except Exception as e:
            logger.error(f"Failed to get property {prop_id}: {e}")
            return 0

    def start(self):
        """Start the camera capture."""
        if not self.is_opened or self.camera is None:
            return False
        try:
            # Configure camera with requested resolution and FPS
            config = self.camera.create_video_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"},
                controls={"FrameRate": self.fps}
            )
            self.camera.configure(config)

            # Enable AE/AWB by default; mode can be adjusted later
            try:
                self.camera.set_controls({
                    "AeEnable": True,
                    "AwbEnable": True,
                })
            except Exception:
                pass

            self.camera.start()
            logger.info(f"Libcamera: Started capture at {self.width}x{self.height} @ {self.fps} FPS")

            # Brief warm-up to stabilize exposure/awb
            time.sleep(0.2)
            return True
        except Exception as e:
            logger.error(f"Failed to start libcamera: {e}")
            return False
        
    def set_day_mode(self):
        """Apply typical daylight settings (AWB auto)."""
        if not self.is_opened or self.camera is None:
            return False
        try:
            # Prefer explicit AWB mode if available
            try:
                self.camera.set_controls({
                    'AwbEnable': True,
                    'AwbMode': controls.AwbModeEnum.Auto,
                })
            except Exception:
                # Fallback: just enable AWB
                self.camera.set_controls({'AwbEnable': True})
            return True
        except Exception as e:
            logger.warning(f"Failed to set day mode: {e}")
            return False

    def set_night_mode(self):
        """Apply typical night/IR settings (AWB greyworld to avoid color cast)."""
        if not self.is_opened or self.camera is None:
            return False
        try:
            try:
                self.camera.set_controls({
                    'AwbEnable': True,
                    'AwbMode': controls.AwbModeEnum.Greyworld,
                })
            except Exception:
                # If Greyworld not available, disable AWB to reduce color pumping
                self.camera.set_controls({'AwbEnable': False})
            return True
        except Exception as e:
            logger.warning(f"Failed to set night mode: {e}")
            return False

    def read(self):
        """
        Read a frame from the camera (mimics cv2.VideoCapture.read).
        
        Returns:
            Tuple of (success, frame) where frame is a numpy array in BGR format
        """
        if not self.is_opened or self.camera is None:
            return False, None

        try:
            with self.lock:
                # Capture array returns RGB, need to convert to BGR for OpenCV compatibility
                frame_rgb = self.camera.capture_array()
                
                if frame_rgb is None:
                    return False, None
                
                # Convert RGB to BGR (OpenCV format)
                import cv2
                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                
                return True, frame_bgr
        except Exception as e:
            logger.error(f"Failed to read frame: {e}")
            return False, None

    def release(self):
        """Release the camera (mimics cv2.VideoCapture.release)."""
        if self.camera is not None:
            try:
                self.camera.stop()
                self.camera.close()
                logger.info("Libcamera: Camera released")
            except Exception as e:
                logger.error(f"Error releasing camera: {e}")
            finally:
                self.camera = None
                self.is_opened = False


def detect_csi_cameras():
    """
    Detect available CSI cameras (excludes USB cameras).
    
    Returns:
        List of detected camera indices
    """
    # Don't use Picamera2.global_camera_info() as it can list USB cameras too.
    # Instead, use CLI tools which correctly distinguish CSI from USB.

    # 2) Try rpicam-apps (Debian 13 / Raspberry Pi repo)
    if shutil.which('rpicam-hello'):
        try:
            result = subprocess.run(
                ['rpicam-hello', '--list-cameras'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                cameras = []
                # The USB camera path appears in stderr, not stdout
                # Check entire output (stdout + stderr) for USB indicators
                full_output = result.stdout + '\n' + result.stderr
                full_output_lower = full_output.lower()
                
                # If the ONLY camera listed has USB indicators in the full output, skip it
                if 'usb@' in full_output_lower or 'uvcvideo' in full_output_lower:
                    logger.info("rpicam-hello detected USB camera only - skipping CSI detection")
                    return []
                
                # Otherwise parse camera indices from stdout
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if '[' in line and ']' in line:
                        try:
                            idx_str = line.split('[')[1].split(']')[0]
                            cameras.append(int(idx_str))
                        except Exception:
                            pass
                if cameras:
                    return cameras
        except Exception as e:
            logger.warning(f"rpicam-hello camera listing failed: {e}")

    # 3) Try generic libcamera tools ('cam --list')
    if shutil.which('cam'):
        try:
            result = subprocess.run(
                ['cam', '--list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                cameras = []
                for line in result.stdout.split('\n'):
                    s = line.strip()
                    s_lower = s.lower()
                    # Skip USB cameras
                    if 'usb@' in s_lower or 'uvcvideo' in s_lower or '/usb/' in s_lower:
                        logger.debug(f"Filtered out USB camera: {s}")
                        continue
                    # Parse lines like "0: imx219 ..." or "[0] ..."
                    if s.startswith('[') and ']' in s:
                        try:
                            idx = int(s[1:s.index(']')])
                            cameras.append(idx)
                        except Exception:
                            pass
                    else:
                        parts = s.split(':', 1)
                        if parts and parts[0].isdigit():
                            try:
                                cameras.append(int(parts[0]))
                            except Exception:
                                pass
                if cameras:
                    return sorted(set(cameras))
        except Exception as e:
            logger.warning(f"cam --list failed: {e}")

    # 4) Legacy fallback: libcamera-hello (older Raspberry Pi OS)
    if shutil.which('libcamera-hello'):
        try:
            result = subprocess.run(
                ['libcamera-hello', '--list-cameras'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                cameras = []
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    line_lower = line.lower()
                    if '[' in line and ']' in line:
                        # Filter USB cameras
                        if 'usb@' in line_lower or 'uvcvideo' in line_lower or '/usb/' in line_lower:
                            logger.debug(f"Filtered out USB camera: {line}")
                            continue
                        try:
                            idx_str = line.split('[')[1].split(']')[0]
                            cameras.append(int(idx_str))
                        except Exception:
                            pass
                if cameras:
                    return cameras
        except Exception as e:
            logger.warning(f"libcamera-hello listing failed: {e}")

    # No cameras detected by any method
    return []


def is_libcamera_available():
    """Check if the libcamera stack is available on the system."""
    # If Picamera2 imported successfully, libcamera is present/usable
    if PICAMERA2_AVAILABLE:
        return True
    # Otherwise, look for known CLI tools
    for tool in ('rpicam-hello', 'cam', 'libcamera-hello'):
        if shutil.which(tool):
            return True
    return False
