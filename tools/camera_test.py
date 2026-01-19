#!/usr/bin/env python3
"""
Filename: camera_test.py
Description: Test and report the FPS and resolution of USB (V4L2) or CSI (libcamera) cameras.
Detects available cameras, opens the first working one, and prints its actual settings.

Supports:
- USB cameras via OpenCV and V4L2
- CSI cameras via libcamera (Raspberry Pi Camera Module)
"""
# Create and activate virtual environment
# python -m venv .venv
# source .venv/bine/activate
# pip install opencv-python
# sudo apt install libcap-dev
# pip install picamera2

import cv2
import logging
import os
import sys
import json
import platform
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import libcamera support
LIBCAMERA_AVAILABLE = False
LibcameraCapture = None
PICAMERA2_AVAILABLE = False
PICAMERA2_IMPORT_ERROR = None

# Helper: attempt to import picamera2 (works both for apt and pip installs)
def _try_import_picamera2():
    global PICAMERA2_AVAILABLE, PICAMERA2_IMPORT_ERROR
    try:
        from picamera2 import Picamera2 as _Picamera2  # noqa: F401
        PICAMERA2_AVAILABLE = True
        return True
    except Exception as e:
        PICAMERA2_AVAILABLE = False
        PICAMERA2_IMPORT_ERROR = e
        return False

# First try normal import
if not _try_import_picamera2():
    # If running inside a venv, ensure its site-packages is on sys.path
    ve = os.environ.get("VIRTUAL_ENV")
    if ve:
        candidate = os.path.join(
            ve,
            "lib",
            f"python{sys.version_info.major}.{sys.version_info.minor}",
            "site-packages",
        )
        if os.path.isdir(candidate) and candidate not in sys.path:
            sys.path.insert(0, candidate)
            _try_import_picamera2()

# Then try to import our libcamera_capture module (depends on picamera2)
try:
    from libcamera_capture import (
        LibcameraCapture,
        detect_csi_cameras,
        is_libcamera_available,
    )
    LIBCAMERA_AVAILABLE = True
except Exception:
    LIBCAMERA_AVAILABLE = False
    LibcameraCapture = None

# Setup logging to console only
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def get_camera_backend():
    """Return appropriate camera backend for the current platform."""
    system = platform.system().lower()
    if system == "linux":
        return cv2.CAP_V4L2
    elif system == "windows":
        return cv2.CAP_DSHOW  # DirectShow for Windows
    else:
        return 0  # Default backend for macOS and others


def list_working_cameras(max_index=10, test_frames=3):
    """Return a list of all working cameras (USB and CSI) with their types."""
    working = []
    
    # First check for CSI cameras if libcamera (Picamera2) is available.
    # Do not require legacy demo tools (libcamera-hello); Debian 13 uses rpicam-apps/cam.
    # CSI detection now filters out USB cameras automatically.
    if LIBCAMERA_AVAILABLE:
        logging.info("Checking for CSI cameras with libcamera...")
        try:
            csi_cameras = detect_csi_cameras()
            if csi_cameras:
                logging.info(f"Found {len(csi_cameras)} CSI camera(s): {csi_cameras}")
            else:
                logging.info("No CSI cameras detected (USB cameras filtered out)")
        except Exception as e:
            logging.warning(f"CSI camera detection failed: {e}")
            csi_cameras = []
        for cam_idx in csi_cameras:
            logging.info(f"Testing CSI camera {cam_idx}...")
            try:
                cap = LibcameraCapture(cam_idx)
                if cap.isOpened():
                    cap.start()
                    good = False
                    for _ in range(test_frames):
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            good = True
                            break
                    if good:
                        logging.info(f"✓ Working CSI camera index {cam_idx}")
                        working.append((cam_idx, 'CSI'))
                    else:
                        logging.warning(f"CSI camera {cam_idx} opened but produced no frames")
                    cap.release()
            except Exception as e:
                logging.warning(f"CSI camera {cam_idx} test failed: {e}")
    
    # Then check for USB cameras
    backend = get_camera_backend()
    backend_name = (
        "V4L2"
        if backend == cv2.CAP_V4L2
        else "DirectShow" if backend == cv2.CAP_DSHOW else "Default"
    )
    
    logging.info(f"Checking for USB cameras with {backend_name}...")
    for cam_idx in range(max_index + 1):
        logging.info(f"Testing USB camera {cam_idx} with {backend_name}...")
        cap = cv2.VideoCapture(cam_idx, backend)
        if not cap.isOpened():
            logging.debug(f"USB camera {cam_idx} could not be opened.")
            cap.release()
            continue
        good = False
        for _ in range(test_frames):
            ret, frame = cap.read()
            if ret and frame is not None:
                good = True
                break
        if good:
            logging.info(f"✓ Working USB camera index {cam_idx}")
            working.append((cam_idx, 'USB'))
        else:
            logging.warning(f"USB camera {cam_idx} opened but produced no frames")
        cap.release()
    
    return working


def print_camera_info(camera_index, camera_type='USB'):
    """Open camera and print its actual FPS and resolution."""
    if camera_type == 'CSI':
        if not LIBCAMERA_AVAILABLE:
            print(f"CSI camera support not available")
            return
        
        cap = LibcameraCapture(camera_index)
        if not cap.isOpened():
            print(f"Could not open CSI camera {camera_index}.")
            return
        
        # Try to set some typical values
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
        try:
            cap.set(cv2.CAP_PROP_FPS, 20)
        except Exception as e:
            logging.warning(f"Could not set FPS: {e}")
        cap.start()
        
        # Get actual settings
        actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        actual_fps = cap.get(cv2.CAP_PROP_FPS)
        print(f"CSI Camera {camera_index} actual settings:")
        print(f"  Resolution: {int(actual_width)}x{int(actual_height)}")
        print(f"  FPS: {actual_fps}")
        cap.release()
    else:  # USB camera
        backend = get_camera_backend()
        cap = cv2.VideoCapture(camera_index, backend)
        if not cap.isOpened():
            print(f"Could not open USB camera {camera_index}.")
            return
        # Try to set some typical values (these may be ignored by hardware)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
        cap.set(cv2.CAP_PROP_FPS, 20)
        # Get actual settings
        actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        actual_fps = cap.get(cv2.CAP_PROP_FPS)
        print(f"USB Camera {camera_index} actual settings:")
        print(f"  Resolution: {int(actual_width)}x{int(actual_height)}")
        print(f"  FPS: {actual_fps}")
        cap.release()


def scan_supported_resolutions_and_fps(camera_index, camera_type='USB'):
    """
    Try a list of common resolutions and FPS values.
    Print only the ones that are accepted by the camera.
    """
    common_resolutions = [
        (320, 240),
        (640, 480),
        (800, 600),
        (1024, 768),
        (1280, 720),
        (1280, 1024),
        (1600, 1200),
        (1920, 1080),
        (2592, 1944),  # Pi Camera v1/v2 max
        (4056, 3040),  # Pi HQ Camera max
    ]
    common_fps = [5, 10, 15, 20, 24, 25, 30, 60]
    
    if camera_type == 'CSI':
        if not LIBCAMERA_AVAILABLE:
            print(f"CSI camera support not available")
            return
        
        cap = LibcameraCapture(camera_index)
        if not cap.isOpened():
            print(f"Could not open CSI camera {camera_index}.")
            return
    else:
        cap = cv2.VideoCapture(camera_index, get_camera_backend())
        if not cap.isOpened():
            print(f"Could not open USB camera {camera_index}.")
            return

    print(f"\nSupported configurations for {camera_type} camera {camera_index}:")
    print(f"{'Resolution':>12} | {'FPS':>6}")
    print("-" * 25)

    working_configs = []
    
    # Start camera if CSI
    if camera_type == 'CSI':
        cap.start()

    for width, height in common_resolutions:
        # Set resolution and try 20 FPS (to match JSON output)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, 20)
        
        # For CSI cameras, need to restart with new config
        if camera_type == 'CSI':
            try:
                cap.release()
                cap = LibcameraCapture(camera_index)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                cap.set(cv2.CAP_PROP_FPS, 20)
                cap.start()
            except:
                continue
        
        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = cap.get(cv2.CAP_PROP_FPS)

        # Only show configurations that work (resolution matches what we requested)
        if actual_width == width and actual_height == height:
            config = f"{width}x{height}"
            if config not in [wc[0] for wc in working_configs]:
                working_configs.append((config, actual_fps))
                print(f"{width}x{height: <5} | {actual_fps: <6.1f}")

    if not working_configs:
        print(
            "No configurations matched exactly. Camera may only support specific resolutions."
        )
        print("\nActual camera behavior (showing what camera reports):")
        print(f"{'Requested':>12} | {'Camera Reports':>15}")
        print("-" * 32)
        # Show a few examples of what the camera actually does
        for width, height in common_resolutions[
            :4
        ]:  # Just test first 4 resolutions
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"{width}x{height: <5} | {actual_width}x{actual_height: <6}")

    cap.release()


def probe_camera_resolutions(camera_index, camera_type='USB', resolutions=None):
    """Return a dict of supported resolutions for a camera index.

    We consider a resolution "supported" if after setting width/height the
    camera reports exactly those values. FPS reported is whatever the device
    returns after setting 20 FPS (to match console output).
    """
    if resolutions is None:
        resolutions = [
            (320, 240),
            (640, 480),
            (800, 600),
            (1024, 768),
            (1280, 720),
            (1280, 1024),
            (1600, 1200),
            (1920, 1080),
            (2592, 1944),  # Pi Camera v1/v2
            (4056, 3040),  # Pi HQ Camera
        ]

    if camera_type == 'CSI':
        if not LIBCAMERA_AVAILABLE:
            return {"index": camera_index, "type": "CSI", "error": "libcamera_not_available"}
        
        cap = LibcameraCapture(camera_index)
        if not cap.isOpened():
            return {"index": camera_index, "type": "CSI", "error": "cannot_open"}
    else:
        cap = cv2.VideoCapture(camera_index, get_camera_backend())
        if not cap.isOpened():
            return {"index": camera_index, "type": "USB", "error": "cannot_open"}

    # Start camera if CSI
    if camera_type == 'CSI':
        cap.start()
    
    # First get default info with same settings as print_camera_info
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
    cap.set(cv2.CAP_PROP_FPS, 20)
    default_info = {
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
    }

    supported = []
    for w, h in resolutions:
        if camera_type == 'CSI':
            # CSI cameras need to be reconfigured for each resolution test
            try:
                cap.release()
                cap = LibcameraCapture(camera_index)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
                cap.set(cv2.CAP_PROP_FPS, 20)
                cap.start()
            except:
                continue
        else:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
            cap.set(cv2.CAP_PROP_FPS, 20)  # Try to set 20 FPS like console mode
        
        actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if actual_w == w and actual_h == h:
            fps = cap.get(cv2.CAP_PROP_FPS)
            supported.append({"width": w, "height": h, "fps": fps})

    cap.release()
    return {
        "index": camera_index,
        "type": camera_type,
        "default": default_info,
        "supported_resolutions": supported,
    }


def probe_all_cameras(max_index=10):
    """Probe all camera indexes (USB and CSI) and return JSON-serializable data."""
    results = []
    working = list_working_cameras(max_index=max_index)
    for idx, cam_type in working:
        results.append(probe_camera_resolutions(idx, camera_type=cam_type))
    return {"cameras": results, "count": len(results)}


if __name__ == "__main__":
    try:
        max_idx = int(os.environ.get("CAM_MAX_INDEX", "8"))
    except ValueError:
        max_idx = 8

    print("Camera Test Utility (USB and CSI cameras)")
    print("==========================================")
    
    # Detect available camera CLI tools (names differ across distros)
    has_libcamera_hello = shutil.which("libcamera-hello") is not None
    has_rpicam_hello = shutil.which("rpicam-hello") is not None
    has_cam_tool = shutil.which("cam") is not None

    # Check for picamera2 and libcamera availability
    if PICAMERA2_AVAILABLE:
        print("✓ picamera2 is installed")
        if LIBCAMERA_AVAILABLE:
            print("✓ libcamera_capture module loaded successfully")
            if is_libcamera_available():
                print("✓ libcamera tools detected")
            else:
                print("⚠ libcamera demo tools not detected")
                # Provide distro-aware hints
                if has_rpicam_hello:
                    print("  Try: rpicam-hello --list-cameras")
                elif has_cam_tool:
                    print("  Try: cam --list")
                elif has_libcamera_hello:
                    print("  Try: libcamera-hello --list-cameras")
                else:
                    print("  On Raspberry Pi OS/Debian with RPi repo: sudo apt install rpicam-apps")
                    print("  On generic Debian/Ubuntu: sudo apt install libcamera-tools")
        else:
            print("⚠ libcamera_capture module failed to load")
            print("  Check that libcamera_capture.py exists in parent directory")
    else:
        print("⚠ picamera2 not available to this Python interpreter")
        print(f"  Python: {sys.executable}")
        ve = os.environ.get("VIRTUAL_ENV")
        if ve:
            print(f"  VIRTUAL_ENV: {ve}")
        if PICAMERA2_IMPORT_ERROR is not None:
            print(f"  Import error: {PICAMERA2_IMPORT_ERROR}")
        print("  Try: sudo apt install python3-picamera2  (system)")
        print("   or: ./.venv/bin/pip install picamera2   (venv)")
        print("   and run with the same interpreter shown above")
    print()

    # Always probe cameras and save to JSON
    data = probe_all_cameras(max_index=max_idx)
    json_output = json.dumps(data, indent=2)

    # Save to camera_info.json
    try:
        with open("camera_info.json", "w") as f:
            f.write(json_output)
        print("Camera information saved to: camera_info.json")
    except IOError as e:
        print(f"Error saving to camera_info.json: {e}")

    working = list_working_cameras(max_index=max_idx)
    if not working:
        print("No working cameras detected!")
        print("Please check:")
        print("  - USB camera connections and permissions")
        print("  - CSI camera cable and raspi-config settings")
        if has_rpicam_hello:
            print("  - Run: rpicam-hello --list-cameras (for CSI)")
        elif has_cam_tool:
            print("  - Run: cam --list (for CSI)")
        else:
            print("  - Run: libcamera-hello --list-cameras (for CSI)")
    else:
        print("Working cameras found:")
        for idx, cam_type in working:
            print(f"  [{cam_type}] Camera {idx}")
        print()

        # Show info for ALL working cameras, not just the first
        for i, (cam_idx, cam_type) in enumerate(working):
            if i > 0:
                print("\n" + "=" * 50)
            print(f"{cam_type} Camera {cam_idx} Details:")
            print_camera_info(cam_idx, cam_type)
            scan_supported_resolutions_and_fps(cam_idx, cam_type)
