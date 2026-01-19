#!/usr/bin/env python3
"""
Check available camera controls for IR LED management
"""
import cv2

def check_camera_controls(camera_index=0):
    """Check all available V4L2 controls for the camera"""
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"Failed to open camera {camera_index}")
        return
    
    print(f"Camera {camera_index} controls:")
    print("-" * 60)
    
    # Common V4L2 properties that might control IR LEDs
    properties = {
        'BRIGHTNESS': cv2.CAP_PROP_BRIGHTNESS,
        'CONTRAST': cv2.CAP_PROP_CONTRAST,
        'SATURATION': cv2.CAP_PROP_SATURATION,
        'HUE': cv2.CAP_PROP_HUE,
        'GAIN': cv2.CAP_PROP_GAIN,
        'EXPOSURE': cv2.CAP_PROP_EXPOSURE,
        'AUTO_EXPOSURE': cv2.CAP_PROP_AUTO_EXPOSURE,
        'AUTO_WB': cv2.CAP_PROP_AUTO_WB,
        'WB_TEMPERATURE': cv2.CAP_PROP_WB_TEMPERATURE,
        'GAMMA': cv2.CAP_PROP_GAMMA,
        'SHARPNESS': cv2.CAP_PROP_SHARPNESS,
        'BACKLIGHT': cv2.CAP_PROP_BACKLIGHT,
    }
    
    # Try to get extended properties (some cameras use these for IR control)
    extended_props = {
        'IRIS': cv2.CAP_PROP_IRIS,
        'ZOOM': cv2.CAP_PROP_ZOOM,
        'FOCUS': cv2.CAP_PROP_FOCUS,
        'AUTOFOCUS': cv2.CAP_PROP_AUTOFOCUS,
    }
    
    properties.update(extended_props)
    
    for name, prop in properties.items():
        try:
            value = cap.get(prop)
            if value != -1:  # -1 usually means not supported
                print(f"{name:20s} = {value}")
        except Exception as e:
            pass
    
    print("\nTrying to disable IR LEDs...")
    print("(Arducam cameras may use BACKLIGHT, GAMMA, or custom properties)")
    
    # Try different approaches to disable IR
    attempts = [
        ("Set BACKLIGHT to 0", cv2.CAP_PROP_BACKLIGHT, 0),
        ("Set BACKLIGHT to 1", cv2.CAP_PROP_BACKLIGHT, 1),
        ("Set IRIS to 0", cv2.CAP_PROP_IRIS, 0),
    ]
    
    for desc, prop, value in attempts:
        try:
            cap.set(prop, value)
            actual = cap.get(prop)
            print(f"{desc}: set={value}, actual={actual}")
        except Exception as e:
            print(f"{desc}: Failed - {e}")
    
    cap.release()
    print("\nNote: Some Arducam cameras require v4l2-ctl commands:")
    print("  v4l2-ctl -d /dev/video0 --list-ctrls")
    print("  v4l2-ctl -d /dev/video0 --set-ctrl=led_mode=0")

if __name__ == "__main__":
    check_camera_controls(0)
