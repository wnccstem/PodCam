# ============================================================================
# File: web_stream.py (OPTIMIZED VERSION)
# Author: William Loring
#
# Description:
#   This program creates a web server that captures video from a USB camera
#   and streams it live to web browsers. Students can view the camera feed
#   by opening a web browser and going to the server's address.
#
#   OPTIMIZATIONS FOR SPEED AND BANDWIDTH:
#   - Reduced default resolution to 640x480 (from 1280x720) for less bandwidth
#   - Added JPEG quality control (85% quality) to balance size vs quality
#   - Frame rate limiting to max 15 FPS to reduce bandwidth usage
#   - Camera warm-up sequence to reduce initial lag
#   - Optional known camera index to skip detection (faster startup)
#   - Responsive web page design with CSS styling
#   - Overlay label feature: displays "WNCC STEM Club" for 60 seconds every 15 minutes
#
#   This file is heavily commented for beginning Python programmers in a
#   community college setting. It explains programming concepts, real-world
#   hardware issues, and how web streaming works.
#
# Educational Topics Covered:
#   - Object-Oriented Programming (classes and methods)
#   - Threading (running multiple tasks at the same time)
#   - HTTP servers and web protocols
#   - Camera/video capture with OpenCV
#   - Error handling with try/except blocks
#   - Network programming basics
#   - Real-world troubleshooting and hardware limitations
#   - Performance optimization techniques
#   - Real-time image overlay and text rendering
# ============================================================================


# --------------------------- IMPORTS (Libraries) -------------------------- #
# These are modules (libraries) that add extra features to Python

import os  # For file system operations and path handling
import sys  # For interpreter path visibility in logs
import logging  # For dynamic level tweaks when debugging
import socketserver  # For creating network servers that handle multiple clients
import time  # For adding delays and timing operations
import numpy as np  # For numerical operations and color correction
from http import server  # For creating HTTP web servers
from threading import (
    Condition,  # For synchronizing threads (like a traffic signal)
    Thread,  # For running background tasks
)  # For running multiple tasks simultaneously
from typing import Optional  # For type hints

from logging_config import get_logger
from web_stream_page import PAGE
from config import (
    ENABLE_LABEL_OVERLAY,
    LABEL_TEXT,
    LABEL_CYCLE_MINUTES,
    LABEL_DURATION_SECONDS,
    LABEL_FONT_SCALE,
    LABEL_TRANSPARENCY,
    TEXT_TRANSPARENCY,
    TEXT_COLOR,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_FRAME_RATE,
    CAMERA_AUTO_EXPOSURE,
    CAMERA_EXPOSURE_VALUE,
    CAMERA_DAY_EXPOSURE_VALUE,
    CAMERA_NIGHT_EXPOSURE_VALUE,
    JPEG_QUALITY,
    KNOWN_CAMERA_INDEX,
    # Day/Night config (software only)
    ENABLE_DAY_NIGHT,
    NIGHT_LUMA_THRESHOLD,
    DAY_LUMA_THRESHOLD,
    LUMA_SAMPLE_EVERY_SEC,
    # RGB LED color correction
    ENABLE_RGB_LED_CORRECTION,
    RGB_CORRECTION_RED,
    RGB_CORRECTION_GREEN,
    RGB_CORRECTION_BLUE,
    RGB_LED_GAMMA,
    # Software white balance
    WB_MODE,
    WB_ALPHA,
    WB_UPDATE_EVERY_SEC,
    WB_GAIN_MIN,
    WB_GAIN_MAX,
    WB_EXCLUDE_DARK,
    WB_EXCLUDE_BRIGHT,
    WB_CALIBRATION_FILE,
    # Night-only brightness boost
    NIGHT_BRIGHTNESS_ENABLE,
    NIGHT_BRIGHTNESS_ALPHA,
    NIGHT_BRIGHTNESS_BETA,
    NIGHT_EXTRA_GAMMA,
)

# Import OpenCV library for camera control
# pip install opencv-python
import cv2

# Import libcamera support for CSI cameras
try:
    from libcamera_capture import LibcameraCapture, detect_csi_cameras, is_libcamera_available
    LIBCAMERA_AVAILABLE = True
except ImportError:
    LIBCAMERA_AVAILABLE = False
    LibcameraCapture = None

# No GPIO IR control (removed by user request)

# --------------------------- LOGGING SETUP -------------------------------- #
# Logging is like a diary for your program. It records what happens and any errors.
# This helps you debug problems and see what your code is doing.
#
# We use the centralized logging_config module for consistent logging setup.

# Setup logging for web_stream module
logger = get_logger("web_stream", enable_console=True)
# Emit handler info immediately to verify logger wiring
try:
    handler_kinds = [type(h).__name__ for h in logger.handlers]
    logger.info(f"Logger initialized with handlers: {handler_kinds}")
except Exception:
    pass


# -------------------- RGB LED COLOR CORRECTION ---------------------------- #
def apply_rgb_led_correction(frame, red_mult=1.0, green_mult=1.0, blue_mult=1.0, gamma=1.0):
    """
    Apply color correction for RGB LED lighting.
    
    Args:
        frame: BGR numpy array from camera
        red_mult: Red channel multiplier (1.0 = no change)
        green_mult: Green channel multiplier (1.0 = no change)
        blue_mult: Blue channel multiplier (1.0 = no change)
        gamma: Gamma correction (1.0 = no change, <1 darker, >1 brighter)
    
    Returns:
        Corrected BGR frame
    """
    if frame is None:
        return frame
    
    # Split BGR channels
    b, g, r = cv2.split(frame)
    
    # Apply multipliers with clipping to valid range [0, 255]
    if blue_mult != 1.0:
        b = np.clip(b.astype(np.float32) * blue_mult, 0, 255).astype(np.uint8)
    if green_mult != 1.0:
        g = np.clip(g.astype(np.float32) * green_mult, 0, 255).astype(np.uint8)
    if red_mult != 1.0:
        r = np.clip(r.astype(np.float32) * red_mult, 0, 255).astype(np.uint8)
    
    # Merge channels back
    corrected = cv2.merge([b, g, r])
    
    # Apply gamma correction if needed
    if gamma != 1.0:
        # Build lookup table for gamma correction
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255
                          for i in np.arange(0, 256)]).astype(np.uint8)
        corrected = cv2.LUT(corrected, table)
    
    return corrected


def apply_brightness_contrast_gamma(frame, alpha=1.0, beta=0.0, gamma=1.0):
    """
    Apply contrast (alpha), brightness (beta), and gamma adjustment to a frame.
    - alpha: contrast multiplier (1.0 no change)
    - beta: brightness offset (0 no change)
    - gamma: gamma correction (>1.0 brightens midtones)
    """
    if frame is None:
        return frame
    out = frame
    try:
        if alpha != 1.0 or beta != 0.0:
            # ConvertScaleAbs: dst = saturate(|alpha*src + beta|)
            out = cv2.convertScaleAbs(out, alpha=float(alpha), beta=float(beta))
        if gamma != 1.0:
            inv_gamma = 1.0 / float(gamma)
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype(np.uint8)
            out = cv2.LUT(out, table)
        return out
    except Exception:
        return frame


# --------------------- MEDIA RELAY (FRAME BROADCASTER) -------------------- #
class MediaRelay:
    """
    MediaRelay pattern for sharing a single webcam source across multiple connections.
    This class captures frames from the camera in a background thread and allows
    multiple clients to subscribe and receive the latest frame.

    Key Concepts:
    - Only one thread talks to the camera (saves resources)
    - All clients (web browsers) get the latest frame from the relay
    - Uses threading.Condition to let clients wait for new frames
    """

    def __init__(
        self,
        enable_overlay=True,
        rotation_angle=0,
        width=1280,
        height=720,
        frame_rate=10.0,
    ):
        # This will store the most recent camera frame as JPEG bytes
        self.frame = None

        # Condition is like a traffic light for threads: it lets them wait for new frames
        self.condition = Condition()

        # Control variables for the camera and background thread
        self.running = False
        self.cap = None
        self.capture_thread = None

        # Store camera-specific settings
        self.enable_overlay = enable_overlay and ENABLE_LABEL_OVERLAY
        self.rotation_angle = rotation_angle
        self.width = width
        self.height = height
        self.frame_rate = frame_rate

        # Label timing control (only initialize if label overlay is enabled for this camera)
        if self.enable_overlay:
            self.label_start_time = (
                time.time()
            )  # When we started the current cycle
            self.label_shown = False  # Track if label is currently being shown

        # Day/Night state
        self.enable_day_night = ENABLE_DAY_NIGHT
        self.current_mode = "day"  # default
        self._last_exposure_mode = None  # Track last exposure mode
        self._last_luma_check = 0.0
        self._mode_switch_count = 0  # Require multiple samples before switching
        self._smoothed_luma = None  # Exponential moving average of brightness

        # Software white balance state
        self.wb_mode = WB_MODE
        self._wb_last_update = 0.0
        # Order: (R, G, B)
        self._wb_gains = [1.0, 1.0, 1.0]
        # Keep last uncorrected frame for calibration
        self._last_uncorrected = None

        # Remember how the camera was opened for potential reconnects
        self.camera_index = 0
        self.use_libcamera = False

    # ------------------------ START CAPTURE ------------------------------- #
    def start_capture(self, camera_index=0, use_libcamera=False):
        # Start capturing video from camera (USB or CSI)
        # camera_index: 0 = first camera, 1 = second, etc.
        # use_libcamera: True for CSI cameras, False for USB cameras
        
        # Store for reconnection logic
        self.camera_index = int(camera_index)
        self.use_libcamera = bool(use_libcamera)

        if use_libcamera:
            if not LIBCAMERA_AVAILABLE:
                raise RuntimeError("Libcamera support not available. Install picamera2: pip install picamera2")
            
            logger.info(
                f"[MediaRelay] Opening CSI camera {camera_index} with libcamera..."
            )
            self.cap = LibcameraCapture(camera_index)
            if not self.cap.isOpened():
                raise RuntimeError(
                    f"Could not open CSI camera {camera_index} with libcamera"
                )
            logger.info(
                f"[MediaRelay] ✓ CSI camera {camera_index} opened successfully with libcamera"
            )
        else:
            logger.info(
                f"[MediaRelay] Opening USB camera {camera_index} with V4L2 backend..."
            )
            # Open camera using OpenCV and the V4L2 backend (best for USB cameras)
            self.cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
            if not self.cap.isOpened():
                # If camera failed to open, raise an error and stop the program
                raise RuntimeError(
                    f"Could not open USB camera {camera_index} with V4L2 backend"
                )
            logger.info(
                f"[MediaRelay] ✓ USB camera {camera_index} opened successfully with V4L2"
            )

        # Enhanced camera configuration with multiple attempts
        self._configure_camera_settings(camera_index)
        
        # For libcamera, start the capture
        if use_libcamera and hasattr(self.cap, 'start'):
            self.cap.start()

        # Check final settings
        actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        logger.info(
            f"[MediaRelay] Final camera settings: {int(actual_width)}x{int(actual_height)} @ {actual_fps} FPS"
        )

        # Check if we got the desired settings
        if int(actual_width) != self.width or int(actual_height) != self.height:
            logger.warning(
                f"[MediaRelay] Camera {camera_index} resolution mismatch: requested {self.width}x{self.height}, got {int(actual_width)}x{int(actual_height)}"
            )
        if actual_fps != self.frame_rate:
            logger.warning(
                f"[MediaRelay] Camera {camera_index} FPS mismatch: requested {self.frame_rate}, got {actual_fps}"
            )

        # Warm up the camera by capturing and discarding a few frames
        # This helps reduce initial lag and ensures stable image quality
        logger.info("[MediaRelay] Warming up camera...")
        for i in range(5):
            ret, _ = self.cap.read()
            if not ret:
                logger.warning(
                    f"[MediaRelay] Frame {i+1} failed during warm-up"
                )
            time.sleep(0.1)  # Small delay between warm-up frames
        logger.info("[MediaRelay] Camera warm-up complete")

        # Try loading persisted WB calibration (if any)
        try:
            self._load_wb_calibration()
        except Exception:
            pass

        # Start the background thread to capture frames
        self.running = True
        self.capture_thread = Thread(target=self._capture_frames)
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def _reopen_camera(self) -> bool:
        """Attempt to reopen the camera using stored settings.
        Returns True on success, False otherwise.
        """
        try:
            # Release existing handle if any
            try:
                if self.cap:
                    self.cap.release()
            except Exception:
                pass

            if self.use_libcamera:
                logger.warning(f"[MediaRelay] Attempting to reconnect CSI camera {self.camera_index}...")
                if not LIBCAMERA_AVAILABLE:
                    logger.error("[MediaRelay] Libcamera not available during reconnect")
                    return False
                self.cap = LibcameraCapture(self.camera_index)
                if not self.cap.isOpened():
                    logger.error(f"[MediaRelay] Reconnect failed: could not open CSI camera {self.camera_index}")
                    return False
                # Configure and start
                self._configure_camera_settings(self.camera_index)
                if hasattr(self.cap, 'start'):
                    self.cap.start()
                logger.info("[MediaRelay] ✓ CSI camera reconnected")
            else:
                logger.warning(f"[MediaRelay] Attempting to reconnect USB camera {self.camera_index} (V4L2)...")
                self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
                if not self.cap.isOpened():
                    logger.error(f"[MediaRelay] Reconnect failed: could not open USB camera {self.camera_index}")
                    return False
                # Configure
                self._configure_camera_settings(self.camera_index)
                logger.info("[MediaRelay] ✓ USB camera reconnected")

            # Warm a couple frames
            for i in range(3):
                ret, _ = self.cap.read()
                if not ret:
                    time.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"[MediaRelay] Camera reconnect error: {e}")
            return False

    def _configure_camera_settings(self, camera_index):
        """Enhanced camera configuration with multiple attempts to force settings."""
        logger.info(
            f"[MediaRelay] Configuring camera {camera_index} settings: {self.width}x{self.height} @ {self.frame_rate} FPS"
        )

        # Method 1: Standard approach
        success = self._try_camera_config("Standard configuration")
        if success:
            return

        # Method 2: Set FPS first, then resolution
        logger.info(f"[MediaRelay] Trying FPS-first configuration...")
        self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)
        time.sleep(0.1)  # Small delay
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        time.sleep(0.1)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        success = self._check_settings("FPS-first configuration")
        if success:
            return

        # Method 3: Multiple attempts with delays
        for attempt in range(3):
            logger.info(
                f"[MediaRelay] Configuration attempt {attempt + 1}/3..."
            )
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            time.sleep(0.2)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            time.sleep(0.2)
            self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)
            time.sleep(0.2)

            if self._check_settings(f"Attempt {attempt + 1}"):
                return

        logger.warning(
            f"[MediaRelay] Camera {camera_index} did not accept requested settings after multiple attempts"
        )

    def _try_camera_config(self, method_name):
        """Try standard camera configuration."""
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)
        
        # Apply exposure settings from config
        try:
            if CAMERA_AUTO_EXPOSURE:
                # Enable auto-exposure (3 = auto mode)
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)
                logger.info(f"[MediaRelay] Auto-exposure enabled")
            else:
                # Manual exposure mode (1 = manual)
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
                self.cap.set(cv2.CAP_PROP_EXPOSURE, CAMERA_EXPOSURE_VALUE)
                actual_exp = self.cap.get(cv2.CAP_PROP_EXPOSURE)
                logger.info(f"[MediaRelay] Manual exposure set to {actual_exp}")
            
            # Set anti-banding/power line frequency to 60Hz (2 = 60Hz, 1 = 50Hz, 0 = disabled)
            if hasattr(cv2, 'CAP_PROP_POWERLINE_FREQUENCY'):
                self.cap.set(cv2.CAP_PROP_POWERLINE_FREQUENCY, 2)
                logger.info("[MediaRelay] Power line frequency set to 60Hz (anti-banding)")
        
        except Exception as e:
            logger.warning(f"[MediaRelay] Could not set exposure or anti-banding: {e}")
        # (IR LED control removed - camera-specific; handled outside this script)
        return self._check_settings(method_name)

    def _check_settings(self, method_name):
        """Check if camera accepted the requested settings."""
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)

        if actual_width == self.width and actual_height == self.height:
            logger.info(
                f"[MediaRelay] ✓ {method_name} successful: {actual_width}x{actual_height} @ {actual_fps} FPS"
            )
            return True
        else:
            logger.info(
                f"[MediaRelay] ✗ {method_name} failed: got {actual_width}x{actual_height} @ {actual_fps} FPS"
            )
            return False

    # -------------------- SOFTWARE WHITE BALANCE ------------------------ #
    def _compute_grayworld_gains(self, frame):
        """Estimate per-channel gains using grayworld assumption on a downscaled, masked frame.
        Returns gains in (R, G, B) order.
        """
        try:
            if frame is None or frame.size == 0:
                return (1.0, 1.0, 1.0)

            # Downscale to speed up
            h, w = frame.shape[:2]
            scale = 320.0 / max(w, 1)
            if scale < 1.0:
                small = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            else:
                small = frame

            # Mask out very dark/bright pixels
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            mask = (gray >= WB_EXCLUDE_DARK) & (gray <= WB_EXCLUDE_BRIGHT)
            if not np.any(mask):
                return (1.0, 1.0, 1.0)

            b, g, r = cv2.split(small)
            # Use masked means
            r_mean = float(r[mask].mean()) if np.any(mask) else 1.0
            g_mean = float(g[mask].mean()) if np.any(mask) else 1.0
            b_mean = float(b[mask].mean()) if np.any(mask) else 1.0

            # Target is the average of the three channels
            target = (r_mean + g_mean + b_mean) / 3.0
            # Raw gains to bring each channel to target
            r_gain = target / max(r_mean, 1e-6)
            g_gain = target / max(g_mean, 1e-6)
            b_gain = target / max(b_mean, 1e-6)

            # Normalize to preserve overall brightness (fix G to 1.0 reference)
            if g_gain > 0:
                r_gain /= g_gain
                b_gain /= g_gain
                g_gain = 1.0

            # Clamp to safe range
            r_gain = float(np.clip(r_gain, WB_GAIN_MIN, WB_GAIN_MAX))
            g_gain = float(np.clip(g_gain, WB_GAIN_MIN, WB_GAIN_MAX))
            b_gain = float(np.clip(b_gain, WB_GAIN_MIN, WB_GAIN_MAX))

            return (r_gain, g_gain, b_gain)
        except Exception as e:
            logger.debug(f"[MediaRelay] Grayworld gains computation failed: {e}")
            return (1.0, 1.0, 1.0)

    def _update_auto_wb(self, frame, now_ts):
        """Update internal WB gains periodically with EMA smoothing."""
        if self.wb_mode != "auto_grayworld":
            return
        if (now_ts - self._wb_last_update) < WB_UPDATE_EVERY_SEC:
            return
        self._wb_last_update = now_ts

        r_gain, g_gain, b_gain = self._compute_grayworld_gains(frame)
        # EMA smoothing
        self._wb_gains[0] = (1 - WB_ALPHA) * self._wb_gains[0] + WB_ALPHA * r_gain
        self._wb_gains[1] = (1 - WB_ALPHA) * self._wb_gains[1] + WB_ALPHA * g_gain
        self._wb_gains[2] = (1 - WB_ALPHA) * self._wb_gains[2] + WB_ALPHA * b_gain
        logger.debug(
            f"[MediaRelay] WB gains updated (R,G,B) -> ({self._wb_gains[0]:.3f}, {self._wb_gains[1]:.3f}, {self._wb_gains[2]:.3f})"
        )

    def _extract_roi(self, frame, roi_mode: str = "", size_fraction: float = 0.45):
        """Return ROI of frame based on mode; supports 'center' square ROI.
        Falls back to full frame on errors.
        """
        try:
            if frame is None or not roi_mode:
                return frame
            mode = (roi_mode or "").lower()
            if mode == "center":
                h, w = frame.shape[:2]
                s = int(max(1, min(h, w) * float(size_fraction)))
                cx, cy = w // 2, h // 2
                x1 = max(0, cx - s // 2)
                y1 = max(0, cy - s // 2)
                x2 = min(w, x1 + s)
                y2 = min(h, y1 + s)
                return frame[y1:y2, x1:x2]
            return frame
        except Exception:
            return frame

    def _save_wb_calibration(self):
        try:
            data = {
                "mode": "locked",
                "gains": {
                    "r": float(self._wb_gains[0]),
                    "g": float(self._wb_gains[1]),
                    "b": float(self._wb_gains[2]),
                },
                "timestamp": time.time(),
            }
            # Save next to this script
            base_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base_dir, WB_CALIBRATION_FILE)
            import json
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"[MediaRelay] WB calibration saved to {path}")
        except Exception as e:
            logger.warning(f"[MediaRelay] Failed to save WB calibration: {e}")

    def _load_wb_calibration(self):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base_dir, WB_CALIBRATION_FILE)
            if not os.path.exists(path):
                return False
            import json
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            gains = data.get("gains", {})
            r = float(gains.get("r", 1.0))
            g = float(gains.get("g", 1.0))
            b = float(gains.get("b", 1.0))
            # Clamp
            r = float(np.clip(r, WB_GAIN_MIN, WB_GAIN_MAX))
            g = float(np.clip(g, WB_GAIN_MIN, WB_GAIN_MAX))
            b = float(np.clip(b, WB_GAIN_MIN, WB_GAIN_MAX))
            self._wb_gains = [r, g, b]
            self.wb_mode = "locked"
            logger.info(
                f"[MediaRelay] WB calibration loaded. Locked gains (R,G,B)=({r:.3f}, {g:.3f}, {b:.3f})"
            )
            return True
        except Exception as e:
            logger.warning(f"[MediaRelay] Failed to load WB calibration: {e}")
            return False

    def calibrate_from_last_frame(self, roi_mode: str = "", size_fraction: float = 0.45):
        """Compute grayworld gains from the last uncorrected frame and lock WB.
        Optional ROI selection via roi_mode and size_fraction.
        """
        src = self._last_uncorrected
        if src is None:
            raise RuntimeError("No recent frame available for calibration")
        src_roi = self._extract_roi(src, roi_mode=roi_mode, size_fraction=size_fraction)
        r_gain, g_gain, b_gain = self._compute_grayworld_gains(src_roi)
        self._wb_gains = [r_gain, g_gain, b_gain]
        self.wb_mode = "locked"
        self._save_wb_calibration()
        return tuple(self._wb_gains)

    def preview_calibration(self, roi_mode: str = "", size_fraction: float = 0.45):
        """Compute proposed grayworld gains from the last uncorrected frame without applying."""
        src = self._last_uncorrected
        if src is None:
            raise RuntimeError("No recent frame available for preview")
        src_roi = self._extract_roi(src, roi_mode=roi_mode, size_fraction=size_fraction)
        return self._compute_grayworld_gains(src_roi)

    # ------------------------ CAPTURE FRAMES ------------------------------- #
    def _capture_frames(self):
        """This method runs in a background thread and keeps grabbing frames from the camera
        It stores the latest frame and notifies all waiting clients"""
        frame_time = (
            1.0 / self.frame_rate
        )  # Calculate time between frames for rate limiting
        last_frame_time = 0

        fail_count = 0
        last_heartbeat = time.time()

        while self.running:
            if self.cap is not None:
                current_time = time.time()

                # Rate limiting: only process frames at the specified max FPS
                if current_time - last_frame_time < frame_time:
                    time.sleep(0.001)  # Small sleep to prevent busy waiting
                    continue

                # Try to read one frame from the camera
                ret, frame = self.cap.read()
                if ret:
                    # IR LED control removed; no per-frame forcing
                    
                    # Save an uncorrected copy for WB calibration before any processing
                    try:
                        self._last_uncorrected = frame.copy()
                    except Exception:
                        self._last_uncorrected = None
                    # Apply RGB LED color correction (OPTIMAL LOCATION: early in pipeline)
                    if ENABLE_RGB_LED_CORRECTION and frame is not None:
                        try:
                            # Update auto WB gains periodically (if enabled)
                            self._update_auto_wb(frame, current_time)
                            wb_r, wb_g, wb_b = self._wb_gains
                            # Combine base multipliers with auto gains
                            frame = apply_rgb_led_correction(
                                frame,
                                red_mult=RGB_CORRECTION_RED * wb_r,
                                green_mult=RGB_CORRECTION_GREEN * wb_g,
                                blue_mult=RGB_CORRECTION_BLUE * wb_b,
                                gamma=RGB_LED_GAMMA
                            )
                        except Exception as e:
                            logger.debug(f"[MediaRelay] RGB LED correction failed: {e}")
                    
                    # Optional: day/night switching using luminance from frame
                    # (now uses corrected frame for accurate luminance)
                    if self.enable_day_night and frame is not None:
                        now = current_time
                        if now - self._last_luma_check >= LUMA_SAMPLE_EVERY_SEC:
                            self._last_luma_check = now
                            # Compute normalized luma from the UNCORRECTED frame to avoid bias
                            src_for_luma = self._last_uncorrected if self._last_uncorrected is not None else frame
                            gray = cv2.cvtColor(src_for_luma, cv2.COLOR_BGR2GRAY)
                            raw_luma = float(gray.mean()) / 255.0
                            
                            # Apply exponential moving average to smooth out auto-exposure variations
                            # Alpha = 0.3 means 30% new value, 70% old value (heavy smoothing)
                            if self._smoothed_luma is None:
                                self._smoothed_luma = raw_luma
                            else:
                                self._smoothed_luma = 0.3 * raw_luma + 0.7 * self._smoothed_luma
                            
                            mean_luma = self._smoothed_luma
                            
                            # Determine if we should switch modes (with damping)
                            should_switch_to_night = self.current_mode == "day" and mean_luma < NIGHT_LUMA_THRESHOLD
                            should_switch_to_day = self.current_mode == "night" and mean_luma > DAY_LUMA_THRESHOLD
                            
                            if should_switch_to_night or should_switch_to_day:
                                self._mode_switch_count += 1
                                # Require 2 consecutive samples in target range before switching
                                if self._mode_switch_count >= 2:
                                    new_mode = "night" if should_switch_to_night else "day"
                                    self.current_mode = new_mode
                                    self._mode_switch_count = 0
                                    try:
                                        # Set camera exposure automatically for day/night
                                        if not CAMERA_AUTO_EXPOSURE and self.cap is not None:
                                            if new_mode == "night":
                                                self.cap.set(cv2.CAP_PROP_EXPOSURE, CAMERA_NIGHT_EXPOSURE_VALUE)
                                                logger.info(f"[MediaRelay] Exposure set to NIGHT value: {CAMERA_NIGHT_EXPOSURE_VALUE}")
                                            else:
                                                self.cap.set(cv2.CAP_PROP_EXPOSURE, CAMERA_DAY_EXPOSURE_VALUE)
                                                logger.info(f"[MediaRelay] Exposure set to DAY value: {CAMERA_DAY_EXPOSURE_VALUE}")
                                        if hasattr(self.cap, "set_day_mode") and hasattr(self.cap, "set_night_mode"):
                                            if new_mode == "night":
                                                self.cap.set_night_mode()
                                            else:
                                                self.cap.set_day_mode()
                                        logger.info(f"[MediaRelay] Day/Night switched to {new_mode} (smoothed luma={mean_luma:.3f}, raw={raw_luma:.3f})")
                                    except Exception as e:
                                        logger.warning(f"[MediaRelay] Exposure switch error: {e}")
                            else:
                                # Reset counter if brightness is stable in current mode
                                self._mode_switch_count = 0
                    # Night-only brightness boost (software), after day/night decision
                    if self.enable_day_night and frame is not None and self.current_mode == "night":
                        if NIGHT_BRIGHTNESS_ENABLE:
                            try:
                                frame = apply_brightness_contrast_gamma(
                                    frame,
                                    alpha=NIGHT_BRIGHTNESS_ALPHA,
                                    beta=NIGHT_BRIGHTNESS_BETA,
                                    gamma=NIGHT_EXTRA_GAMMA,
                                )
                            except Exception:
                                pass
                    # Add WNCC STEM Club label timing logic (only if enabled for this camera)
                    if self.enable_overlay:
                        current_cycle_time = (
                            current_time - self.label_start_time
                        )

                        # Show label for configured duration every configured interval
                        cycle_duration = (
                            LABEL_CYCLE_MINUTES * 60
                        )  # Convert minutes to seconds
                        if current_cycle_time >= cycle_duration:  # Reset cycle
                            self.label_start_time = current_time
                            current_cycle_time = 0
                            self.label_shown = False

                        # Show label for first X seconds of each cycle
                        show_label = current_cycle_time < LABEL_DURATION_SECONDS

                        # Add overlay text if it's time to show it
                        if show_label:
                            # Add semi-transparent background for better text visibility
                            overlay = frame.copy()

                            # Calculate text size and position
                            font = cv2.FONT_HERSHEY_SIMPLEX
                            thickness = 2

                            # Get text size to position it properly
                            (text_width, text_height), baseline = (
                                cv2.getTextSize(
                                    LABEL_TEXT,
                                    font,
                                    LABEL_FONT_SCALE,
                                    thickness,
                                )
                            )

                            # Position in bottom-left corner with some padding
                            x = 20  # 20 pixels from left edge
                            # 20 pixels from bottom edge
                            y = frame.shape[0] - 20

                            # Draw semi-transparent background rectangle
                            cv2.rectangle(
                                overlay,
                                (x - 10, y - text_height - 10),
                                (x + text_width + 10, y + 10),
                                (0, 0, 0),
                                -1,
                            )  # Black background

                            # Blend the overlay with the original frame for transparency
                            cv2.addWeighted(
                                overlay,
                                LABEL_TRANSPARENCY,
                                frame,
                                1 - LABEL_TRANSPARENCY,
                                0,
                                frame,
                            )

                            # Add label text using the configured text color and transparency
                            if TEXT_TRANSPARENCY < 1.0:
                                text_overlay = frame.copy()
                                cv2.putText(
                                    text_overlay,
                                    LABEL_TEXT,
                                    (x, y),
                                    font,
                                    LABEL_FONT_SCALE,
                                    TEXT_COLOR,
                                    thickness,
                                )
                                cv2.addWeighted(
                                    text_overlay,
                                    TEXT_TRANSPARENCY,
                                    frame,
                                    1 - TEXT_TRANSPARENCY,
                                    0,
                                    frame,
                                )
                            else:
                                cv2.putText(
                                    frame,
                                    LABEL_TEXT,
                                    (x, y),
                                    font,
                                    LABEL_FONT_SCALE,
                                    TEXT_COLOR,
                                    thickness,
                                )

                            # Log when label appears (only once per state change)
                            if not self.label_shown:
                                logger.info(
                                    f"[MediaRelay] Label '{LABEL_TEXT}' displayed for {LABEL_DURATION_SECONDS}s"
                                )
                                self.label_shown = True
                        else:
                            # Log when label disappears (only once per state change)
                            if self.label_shown:
                                logger.info(
                                    f"[MediaRelay] Label '{LABEL_TEXT}' hidden - next display in {LABEL_CYCLE_MINUTES} minutes"
                                )
                                self.label_shown = False

                    # Apply rotation if specified for this camera
                    # Debug logging to help diagnose unexpected rotation behavior
                    logger.debug(
                        f"[MediaRelay] rotation_angle={self.rotation_angle}"
                    )
                    if self.rotation_angle == 90:
                        # Rotate 90 degrees counterclockwise
                        logger.debug(
                            "[MediaRelay] Applying rotation: 90° CCW (ROTATE_90_COUNTERCLOCKWISE)"
                        )
                        frame = cv2.rotate(
                            frame, cv2.ROTATE_90_COUNTERCLOCKWISE
                        )
                    elif self.rotation_angle == 180:
                        # Rotate 180 degrees
                        logger.debug(
                            "[MediaRelay] Applying rotation: 180° (ROTATE_180)"
                        )
                        frame = cv2.rotate(frame, cv2.ROTATE_180)
                    elif self.rotation_angle == 270:
                        # Rotate 270 degrees counterclockwise (or 90 degrees clockwise)
                        logger.debug(
                            "[MediaRelay] Applying rotation: 270° CCW / 90° CW (ROTATE_90_CLOCKWISE)"
                        )
                        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

                    # Convert the frame to JPEG format with controlled quality for web streaming
                    # ---------------- Day/Night corner label -----------------
                    if self.enable_day_night and frame is not None:
                        mode_text = "DAY" if self.current_mode == "day" else "NIGHT"
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        dn_scale = 0.6
                        dn_thickness = 2
                        try:
                            (mtw, mth), _ = cv2.getTextSize(mode_text, font, dn_scale, dn_thickness)
                            pad = 6
                            # Guard against unexpected empty dimensions
                            if mtw > 0 and mth > 0:
                                x2 = max(0, frame.shape[1] - mtw - pad - 8)
                                y2 = pad + mth + 2
                                bg_color = (0, 120, 0) if self.current_mode == "day" else (0, 0, 160)
                                txt_color = (255, 255, 255)
                                cv2.rectangle(
                                    frame,
                                    (x2 - pad, y2 - mth - pad),
                                    (x2 + mtw + pad, y2 + pad // 2),
                                    bg_color,
                                    -1,
                                )
                                cv2.putText(
                                    frame,
                                    mode_text,
                                    (x2, y2),
                                    font,
                                    dn_scale,
                                    txt_color,
                                    dn_thickness,
                                    cv2.LINE_AA,
                                )
                        except Exception as e:
                            logger.debug(f"[MediaRelay] Day/Night label draw failed: {e}")
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
                    _, buffer = cv2.imencode(".jpg", frame, encode_params)
                    frame_bytes = buffer.tobytes()

                    # Notify all clients that a new frame is ready
                    with self.condition:
                        self.frame = frame_bytes
                        self.condition.notify_all()

                    last_frame_time = current_time
                else:
                    # Frame capture failed; track and optionally reconnect
                    fail_count += 1
                    if fail_count % int(max(1, self.frame_rate)) == 0:
                        logger.warning(f"[MediaRelay] Consecutive frame read failures: {fail_count}")
                    # After ~3 seconds of failures, try to reconnect
                    if fail_count >= int(self.frame_rate) * 3:
                        logger.error("[MediaRelay] Persistent frame read failures. Attempting camera reconnect...")
                        success = self._reopen_camera()
                        if success:
                            logger.info("[MediaRelay] Reconnect succeeded. Resuming capture.")
                            fail_count = 0
                            last_frame_time = time.time()
                        else:
                            logger.error("[MediaRelay] Reconnect failed. Stopping capture loop.")
                            break
                    else:
                        time.sleep(0.02)
            else:
                # If camera connection is lost, exit the loop
                break

            # Heartbeat every 60s to confirm capture is active
            if time.time() - last_heartbeat >= 60:
                logger.info("[MediaRelay] Capture heartbeat: running OK")
                last_heartbeat = time.time()

    # ------------------------- GET FRAME ---------------------------------- #
    def get_frame(self):
        """
        Wait for and return the latest frame (for use by each client).
        Each client (browser) calls this to get the newest frame.
        """
        with self.condition:
            self.condition.wait()  # Wait until a new frame is available
            return self.frame

    def stop(self):
        # Cleanly stop the background thread and release the camera
        self.running = False
        if self.capture_thread:
            self.capture_thread.join()
        if self.cap:
            self.cap.release()


# -------------------- STREAMING HANDLER (Web Requests) -------------------- #
class StreamingHandler(server.BaseHTTPRequestHandler):
    """
    This class handles HTTP requests from web browsers.

    When someone opens a web browser and goes to our server's address,
    their browser sends an HTTP request. This class processes those requests
    and sends back the appropriate response (web page or video stream).

    Key Concepts:
    - Inheritance (this class extends BaseHTTPRequestHandler)
    - HTTP protocol basics (GET requests, response codes, headers)
    - Method overriding (we override do_GET from the parent class)
    - String manipulation and encoding
    - Binary data handling
    """

    # Class variable to track the number of active streaming connections
    active_stream_connections = 0

    # -------------------------- DO GET ------------------------------------ #
    def do_GET(self):
        # This method handles GET requests from browsers (like when you type a URL)
        # It decides what to send back based on the requested path
        # Strip query parameters (e.g., ?t=timestamp) for path matching
        full_path = self.path
        path = full_path.split('?')[0]
        # Parse query params for endpoints that use them
        try:
            from urllib.parse import parse_qs
            qs = full_path.split('?', 1)[1] if '?' in full_path else ''
            qparams = parse_qs(qs)
        except Exception:
            qparams = {}
        
        if path == "/":
            # Redirect root path to the main page
            self.send_response(301)
            self.send_header("Location", "/index.html")
            self.end_headers()
        elif path == "/index.html":
            # Send the main HTML page
            content = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif path == "/stream0.mjpg":
            # Handle Pod camera stream (camera 0)
            self._handle_stream_request(relay0, "Pod")
        elif path == "/wb/status":
            # Return white balance status and gains
            try:
                gains = getattr(relay0, "_wb_gains", [1.0, 1.0, 1.0]) if relay0 else [1.0, 1.0, 1.0]
                mode = getattr(relay0, "wb_mode", "off") if relay0 else "off"
                import json
                payload = json.dumps({
                    "mode": mode,
                    "gains": {"r": gains[0], "g": gains[1], "b": gains[2]}
                }).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as e:
                self.send_error(500, f"WB status error: {e}")
        elif path == "/wb/calibrate":
            # One-click neutral-card calibration: compute & lock gains from last frame
            try:
                if not relay0:
                    raise RuntimeError("Camera not available")
                # ROI options: roi=center&size=0.4 (fraction of min dimension)
                roi_mode = (qparams.get('roi', [''])[0] or '').lower()
                size_f = float(qparams.get('size', [0.45])[0])
                size_f = max(0.05, min(0.95, size_f))
                r, g, b = relay0.calibrate_from_last_frame(roi_mode=roi_mode, size_fraction=size_f)
                msg = f"Calibrated and locked WB (R,G,B)=({r:.3f},{g:.3f},{b:.3f})"
                body = msg.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_error(500, f"Calibration failed: {e}")
        elif path == "/wb/preview":
            # Compute proposed gains without applying them (for UI/testing)
            try:
                if not relay0:
                    raise RuntimeError("Camera not available")
                roi_mode = (qparams.get('roi', [''])[0] or '').lower()
                size_f = float(qparams.get('size', [0.45])[0])
                size_f = max(0.05, min(0.95, size_f))
                gains = relay0.preview_calibration(roi_mode=roi_mode, size_fraction=size_f)
                import json
                payload = json.dumps({
                    "proposed_gains": {"r": gains[0], "g": gains[1], "b": gains[2]},
                    "mode": relay0.wb_mode,
                    "roi": roi_mode or "full",
                    "size_fraction": size_f
                }).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as e:
                self.send_error(500, f"WB preview failed: {e}")
        elif path == "/wb/locked":
            try:
                if not relay0:
                    raise RuntimeError("Camera not available")
                relay0.wb_mode = "locked"
                msg = "WB mode set to locked"
                body = msg.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_error(500, f"WB lock failed: {e}")
        elif path == "/wb/auto":
            try:
                if not relay0:
                    raise RuntimeError("Camera not available")
                relay0.wb_mode = "auto_grayworld"
                msg = "WB mode set to auto_grayworld"
                body = msg.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_error(500, f"WB auto set failed: {e}")
        elif path == "/wb/off":
            try:
                if not relay0:
                    raise RuntimeError("Camera not available")
                relay0.wb_mode = "off"
                relay0._wb_gains = [1.0, 1.0, 1.0]
                msg = "WB mode set to off"
                body = msg.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_error(500, f"WB off failed: {e}")
        elif path == "/wb/clear":
            try:
                # Delete calibration file; set auto mode
                base_dir = os.path.dirname(os.path.abspath(__file__))
                pathf = os.path.join(base_dir, WB_CALIBRATION_FILE)
                if os.path.exists(pathf):
                    os.remove(pathf)
                if relay0:
                    relay0.wb_mode = "auto_grayworld"
                msg = "WB calibration cleared; mode set to auto"
                body = msg.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_error(500, f"WB clear failed: {e}")
        elif path == "/favicon.ico":
            # Handle favicon requests to prevent 404 errors
            self.send_response(204)  # No Content
            self.end_headers()
        else:
            # Any other path: send a 404 Not Found error
            self.send_error(404)
            self.end_headers()

    def _handle_stream_request(self, camera_relay, camera_description):
        """Handle MJPEG stream requests for a specific camera relay."""
        # Check if the requested camera relay is available
        if camera_relay is None:
            logger.error(
                f"{camera_description} camera not available for {self.path}"
            )
            self.send_error(503, f"{camera_description} camera not available")
            return

        # Increment the connection counter and log new connection
        StreamingHandler.active_stream_connections += 1
        logger.info(
            f"New {camera_description} streaming client connected from {self.client_address[0]} requesting {self.path}. "
            f"Active connections: {StreamingHandler.active_stream_connections}"
        )

        self.send_response(200)
        self.send_header("Age", "0")
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header(
            "Content-Type", "multipart/x-mixed-replace; boundary=FRAME"
        )
        self.end_headers()
        try:
            while True:
                # Get the latest frame from the specific MediaRelay
                frame = camera_relay.get_frame()
                if frame is not None:
                    # Send the frame boundary marker
                    self.wfile.write(b"--FRAME\r\n")
                    # Send headers for this JPEG image
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", str(len(frame)))
                    self.end_headers()
                    # Send the actual image data
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
        except Exception as e:
            # If the browser disconnects or there's a network error, log it
            logger.warning(
                "Removed streaming client %s (%s): %s",
                self.client_address,
                camera_description,
                str(e),
            )
        finally:
            # Decrement the connection counter when client disconnects
            StreamingHandler.active_stream_connections -= 1
            logger.info(
                f"{camera_description} streaming client {self.client_address[0]} disconnected from {self.path}. "
                f"Active connections: {StreamingHandler.active_stream_connections}"
            )


# -------------------- STREAMING SERVER (Multi-Client) --------------------- #
class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    """
    This class creates the web server that handles multiple clients simultaneously.

    Key Concepts:
    - Multiple inheritance (inherits from both ThreadingMixIn and HTTPServer)
    - Mixin classes (ThreadingMixIn adds threading capability)
    - Class attributes (variables that belong to the class, not instances)
    - Server architecture and design patterns

    ThreadingMixIn allows the server to handle multiple browser connections at once.
    Each client gets its own thread and can independently receive the MJPEG stream.
    The MediaRelay object is shared, but frame access is synchronized for thread safety.
    """

    # Class attributes - these apply to all instances of this class

    # Allow reusing the network address immediately after shutdown
    # Without this, you might get "Address already in use" errors
    allow_reuse_address = True

    # Use daemon threads for client connections
    # This means all client threads will close when the main program exits
    daemon_threads = True


# ======================= GLOBAL VARIABLES ================================= #
# Global MediaRelay object that will be initialized in main()
# relay0 for Pod camera (camera 0)
relay0: Optional["MediaRelay"] = None  # Pod camera

# ====================== MAIN PROGRAM STARTS HERE ========================== #
# This is where the actual program execution begins.
# Everything above this point was just defining classes and functions.
# Now we use those classes to create and run our camera streaming server.


def find_working_camera():
    """
    Find a working camera efficiently (USB or CSI).
    Returns tuple of (camera_index, use_libcamera) if found, (None, False) otherwise.
    """
    # First, check for CSI cameras if libcamera is available
    if LIBCAMERA_AVAILABLE and is_libcamera_available():
        logger.info("Checking for CSI cameras with libcamera...")
        csi_cameras = detect_csi_cameras()
        if csi_cameras:
            logger.info(f"Found CSI cameras: {csi_cameras}")
            # Try first CSI camera
            try:
                test_cap = LibcameraCapture(0)
                if test_cap.isOpened():
                    logger.info(f"✓ CSI camera 0 is working")
                    test_cap.release()
                    return (0, True)
                test_cap.release()
            except Exception as e:
                logger.warning(f"CSI camera test failed: {e}")
    
    # If user specified a known camera index, try that first (fastest startup)
    if KNOWN_CAMERA_INDEX is not None:
        logger.info(f"Trying known USB camera index {KNOWN_CAMERA_INDEX}...")
        test_cap = cv2.VideoCapture(KNOWN_CAMERA_INDEX, cv2.CAP_V4L2)
        if test_cap.isOpened():
            ret, frame = test_cap.read()
            if ret and frame is not None:
                logger.info(f"✓ Known USB camera {KNOWN_CAMERA_INDEX} is working")
                test_cap.release()
                return (KNOWN_CAMERA_INDEX, False)
            else:
                logger.warning(
                    f"Known USB camera {KNOWN_CAMERA_INDEX} opens but cannot capture frames"
                )
        else:
            logger.warning(f"Known USB camera {KNOWN_CAMERA_INDEX} not available")
        test_cap.release()

    # If known camera failed or not specified, search for USB cameras
    logger.info("Detecting available USB cameras...")
    for cam_idx in range(4):
        logger.info(f"Testing USB camera {cam_idx} with V4L2...")
        test_cap = cv2.VideoCapture(cam_idx, cv2.CAP_V4L2)
        if test_cap.isOpened():
            ret, frame = test_cap.read()
            if ret and frame is not None:
                logger.info(f"✓ Found working USB camera at index {cam_idx}")
                test_cap.release()
                return (cam_idx, False)
            else:
                logger.warning(
                    f"USB camera {cam_idx} opens but cannot capture frames"
                )
        else:
            logger.info(f"USB camera {cam_idx} not available")
        test_cap.release()

    return (None, False)


def main():
    global relay0  # Declare relay as global so it can be accessed by StreamingHandler

    # Print status messages to help users understand what's happening
    logger.info("Starting Pod camera streaming server...")
    try:
        logger.info(
            f"Startup context: cwd={os.getcwd()} file={__file__} python={sys.executable}"
        )
    except Exception:
        pass
    logger.info("Camera 0: Pod Camera")

    # Optional: elevate logging to DEBUG via env toggle
    if os.getenv("WEB_STREAM_DEBUG") == "1":
        logger.setLevel(logging.DEBUG)
        logger.info("WEB_STREAM_DEBUG=1 detected, log level set to DEBUG")
    
    # Detect if libcamera is available
    if LIBCAMERA_AVAILABLE:
        logger.info("Libcamera support available for CSI cameras")
    
    # Force USB mode if KNOWN_CAMERA_INDEX is set (user knows their camera)
    use_libcamera_0 = False
    if KNOWN_CAMERA_INDEX is not None:
        logger.info("KNOWN_CAMERA_INDEX is set - using USB/V4L2 mode for camera 0")
        use_libcamera_0 = False
    elif LIBCAMERA_AVAILABLE and is_libcamera_available():
        # Only auto-detect CSI if camera index is not explicitly known
        csi_cameras = detect_csi_cameras()
        if 0 in csi_cameras:
            use_libcamera_0 = True
            logger.info("Camera 0 detected as CSI camera")

    # Initialize camera relay for Pod (camera 0) with overlay enabled
    relay0 = MediaRelay(
        enable_overlay=True,
        rotation_angle=0,
        width=CAMERA_WIDTH,
        height=CAMERA_HEIGHT,
        frame_rate=CAMERA_FRAME_RATE,
    )
    try:
        relay0.start_capture(camera_index=0, use_libcamera=use_libcamera_0)
        cam_type_0 = "CSI" if use_libcamera_0 else "USB"
        logger.info(
            f"✓ Pod camera ({cam_type_0} camera 0) initialized successfully with overlay at {CAMERA_WIDTH}x{CAMERA_HEIGHT} @ {CAMERA_FRAME_RATE} FPS"
        )
    except Exception as e:
        logger.error(
            f"✗ Pod camera (camera 0) failed to initialize: {e}"
        )
        relay0 = None

    # Check if camera is working
    if relay0 is None:
        logger.error("Pod camera could not be initialized!")
        logger.error("Please check:")
        logger.error("  - Camera is connected properly (USB or CSI)")
        logger.error("  - Camera is not being used by another application")
        logger.error("  - Camera permissions: sudo usermod -a -G video $USER")
        logger.error("  - For CSI: check ribbon cable and enable camera interface")
        logger.error("  - For USB: ls -la /dev/video*")
        logger.error("  - V4L2 info: v4l2-ctl --list-devices")
        exit(1)

    # Log camera availability
    logger.info("Pod camera available at: /stream0.mjpg")

    # Now start the web server
    try:
        # Create the network address for our server
        # ("", 8000) means:
        # - "" = listen on all available network interfaces (localhost, WiFi, Ethernet)
        # - 8000 = port number (like a channel number for network communication)
        address = ("", 8000)

        # Create the HTTP server object
        # This combines our StreamingHandler (processes requests) with
        # the StreamingServer (manages network connections)
        server = StreamingServer(address, StreamingHandler)

        # Get network information to display to the user
        import socket  # Import here since we only need it once

        hostname = socket.gethostname()  # Get the computer's name
        try:
            # Try to get the computer's IP address on the local network
            local_ip = socket.gethostbyname(hostname)

            # Print connection information for users
            logger.info(f"Pod camera streaming server started successfully!")
            logger.info(f"Pod camera view: http://localhost:8000/")
            logger.info(f"Network access: http://{local_ip}:8000/")
            logger.info(f"Raspberry Pi access: http://{hostname}.local:8000/")
            logger.info(
                f"Pod camera stream: http://{local_ip}:8000/stream0.mjpg"
            )
        except:
            # If we can't get the IP address, just show localhost
            logger.info(
                "Pod camera streaming server started on http://localhost:8000/"
            )

        logger.info("Press Ctrl+C to stop the server")
        logger.info("-" * 50)

        # Start the server and keep it running
        # serve_forever() is a blocking call - the program waits here
        # and processes incoming requests until we stop it
        server.serve_forever()

    except KeyboardInterrupt:
        # This exception occurs when user presses Ctrl+C
        logger.info("Streaming stopped by user")

    finally:
        # This block always runs, even if an error occurred
        # It ensures we clean up resources properly

        # Stop camera capture thread and close camera connection
        if relay0:
            relay0.stop()
            logger.info("Pod camera stopped")

        logger.info("Cleanup completed. Goodbye!")


# If this script is run directly (not imported), call the main function
if __name__ == "__main__":
    # Start the main program
    main()
else:
    # If this script is imported as a module, we don't run the main function
    # This allows other scripts to use the MediaRelay and StreamingServer classes
    logger.info(
        "web_stream.py module imported. Use main() to start the server."
    )
