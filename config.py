"""
Configuration file for the PodsInSpace Monitoring System
Centralizes all configurable parameters for easy maintenance
"""

# Sensor Reading Configuration
SENSOR_READ_INTERVAL = 30  # seconds between sensor readings
THINGSPEAK_INTERVAL = 600  # seconds between ThingSpeak updates (10 minutes)

# Calculated values based on intervals
READINGS_PER_CYCLE = THINGSPEAK_INTERVAL // SENSOR_READ_INTERVAL  # 20 readings

# Email Configuration
ENABLE_SCHEDULED_EMAILS = True
DAILY_EMAIL_TIME = "06:00,18:00"  # HH:MM format for daily status email
SEND_EMAIL_ON_STARTUP = True  # Send one status email at service startup

# Email SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587  # TLS port for Gmail
EMAIL_TIMEOUT = 30  # Connection timeout in seconds

# Default email settings (can be overridden)
DEFAULT_SENDER_EMAIL = "wnccrobotics@gmail.com"
DEFAULT_SENDER_PASSWORD = (
    "loyqlzkxisojeqsr"  # Use App Password, not regular password
)

# Multiple recipients - add more email addresses here
DEFAULT_RECIPIENT_EMAILS = [
    "williamloring@hotmail.com",
    "loringw@wncc.edu",
    "trooks1@wncc.edu",
]

# Email template constants
SUBJECT_PREFIX = "PodsInSpace "
DEFAULT_SUBJECT = f"{SUBJECT_PREFIX} System Notification"

# Data Processing Configuration
TRIM_PERCENT = 0.1  # Percentage to trim from each end for outlier removal (10%)

HUMIDITY_MIN = 40.0  # Percentage
HUMIDITY_MAX = 80.0  # Percentage

# System Configuration
LOG_BACKUP_COUNT = 7  # Number of log files to keep
LOG_ROTATION = "midnight"  # When to rotate logs

# Network Configuration
THINGSPEAK_TIMEOUT = 30  # seconds
RETRY_DELAY = 5  # seconds to wait before retrying failed operations
RESTART_DELAY = (
    600  # seconds to wait before system restart after critical error
)

# Camera Overlay Configuration
ENABLE_LABEL_OVERLAY = True  # Set to False to completely disable label feature
LABEL_TEXT = (
    "WNCC STEM Club Meeting Thursday at 4 PM in C1"  # Text to display on video
)
LABEL_CYCLE_MINUTES = 10  # Show label every X minutes
LABEL_DURATION_SECONDS = 30  # Show label for X seconds each cycle
LABEL_FONT_SCALE = 0.8  # Size of the label text
LABEL_TRANSPARENCY = (
    0.7  # Background transparency (0.0 = transparent, 1.0 = opaque)
)
TEXT_TRANSPARENCY = 0.9  # Text transparency for overlays (0.0 = fully transparent, 1.0 = fully opaque)
TEXT_COLOR = (0, 85, 204)  # Text color for overlays (BGR format - burnt orange)

# ------------------------- CAMERA EXPOSURE CONTROL ------------------------ #
# Control camera exposure and IR LED behavior
# True = auto exposure, False = manual (set to False to stop flicker)
CAMERA_AUTO_EXPOSURE = False

# Exposure values for manual mode
# Use lower value for day, higher for night (IR)
# Example: 16 for bright daylight
CAMERA_DAY_EXPOSURE_VALUE = 40
# Example: 33 for IR night (increase if too dark: 100-300)
CAMERA_NIGHT_EXPOSURE_VALUE = 30

# For backward compatibility, you may keep this (used if not switching dynamically)
CAMERA_EXPOSURE_VALUE = CAMERA_NIGHT_EXPOSURE_VALUE

# ------------------------ WEBSTREAM CONFIGURATION ------------------------- #
# These constants (values that don't change) control how the camera behaves.
# You can change these to adjust the video quality and frame rate.

# Pod (Camera 0) Frame Rate Settings
# How many pictures per second we want the camera to take
CAMERA_FRAME_RATE = 5.0

# Note: Some cameras may ignore frame rate settings and use their own preferred rate.
# This is normal hardware behavior - the camera will tell us what it's actually using.
# Pod (Camera 0) Resolution
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1080

# JPEG compression quality (0-100, higher = better quality but more bandwidth)
# Good balance between quality and bandwidth
JPEG_QUALITY = 85

# Skip camera detection if you know your camera index (faster startup)
# Set to 0, 1, 2, etc. if you know your camera index, or None to auto-detect
KNOWN_CAMERA_INDEX = 0

# ---------------------- DAY/NIGHT CONFIG (software only) ----------------- #
# Enable automatic day/night switching based on frame brightness
# Set True to enable day/night label display
ENABLE_DAY_NIGHT = True
# Hysteresis thresholds on normalized luma (0.0-1.0). Use NIGHT < DAY.
# Lower values = darker threshold. Tune based on your lighting:
#   - If showing NIGHT during daylight → lower DAY_LUMA_THRESHOLD (try 0.30-0.40)
#   - If showing DAY at night → raise NIGHT_LUMA_THRESHOLD (try 0.25-0.35)
#   - Keep ~0.10-0.15 gap between thresholds to prevent rapid switching
#   - If flickering → increase sample interval to 300+ seconds
# NOTE: Luma is measured from UNCORRECTED frame (before RGB correction/WB)
# Switch to night mode when brightness drops below this (raised for IR illumination)
NIGHT_LUMA_THRESHOLD = 0.25
# Switch to day mode when brightness rises above this (lowered for IR illumination)
DAY_LUMA_THRESHOLD = 0.18
# How often in (seconds) to sample brightness to consider switching
# Check more often for maximum stability
LUMA_SAMPLE_EVERY_SEC = 15.0

# ---------------------- RGB LED COLOR CORRECTION -------------------------- #
# Adjust colors to compensate for RGB LED lighting
ENABLE_RGB_LED_CORRECTION = True  # Apply correction to live stream

# RGB multipliers for white balance adjustment (1.0 = no change)
# Magenta cast = too little green vs red+blue. Boost green and slightly
# reduce red/blue until soil looks natural.
RGB_CORRECTION_RED = 1.0  # Slightly reduce red
RGB_CORRECTION_GREEN = 1.0  # Boost green to counter magenta
RGB_CORRECTION_BLUE = 1.0  # Slightly reduce blue

# Optional: Gamma correction for brightness curve adjustment
# Increase above 1.0 to brighten midtones (e.g., 1.2–1.4)
RGB_LED_GAMMA = 1.5

# Software White Balance (in addition to the base multipliers above)
# Modes: "off" (no auto WB), "auto_grayworld" (estimate per-frame gains)
# NOTE: Auto WB disabled due to flickering
# Use manual RGB multipliers or calibrate with /wb/calibrate
WB_MODE = "on"

# How quickly to adapt to new lighting (0.0-1.0). Lower = smoother.
WB_ALPHA = 0.12

# How often (in seconds) to recompute gains
WB_UPDATE_EVERY_SEC = 3.0

# Clamp range for auto gains to avoid extremes
WB_GAIN_MIN = 0.5
WB_GAIN_MAX = 2.0

# Ignore very dark/bright pixels when computing gains to reduce bias
WB_EXCLUDE_DARK = 25  # grayscale below this (0-255) is ignored
WB_EXCLUDE_BRIGHT = 235  # grayscale above this is ignored

# Persisted calibration file for "neutral-card" lock
WB_CALIBRATION_FILE = "wb_calibration.json"

# ---------------------- NIGHT BRIGHTNESS BOOST ---------------------------- #
# Apply additional brightness/contrast/gamma only when in night mode
# This helps visibility under IR illumination or very low light.
NIGHT_BRIGHTNESS_ENABLE = True
# Contrast multiplier (1.0 = no change). Try 1.05–1.25.
NIGHT_BRIGHTNESS_ALPHA = 1.0
# Brightness offset in 0–255 (0 = no change). Try 8–20.
NIGHT_BRIGHTNESS_BETA = 7
# Extra gamma to brighten midtones at night (1.0 = no change). Try 1.1–1.4.
NIGHT_EXTRA_GAMMA = 1.0
