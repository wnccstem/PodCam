#!/usr/bin/env python3
"""
Filename: alert_system.py
Description: Modular alert system for sensor readings
Handles temperature, CO2, humidity, and moisture alerts
Easy to extend with new alert types
"""

from logging_config import setup_sensor_logger
from alerts_config import (
    TEMP_ALERT_HIGH,
    TEMP_ALERT_LOW,
    TEMP_ALERT_ENABLED,
    CO2_ALERT_HIGH,
    CO2_ALERT_ENABLED,
    HUMIDITY_ALERT_HIGH,
    HUMIDITY_ALERT_LOW,
    HUMIDITY_ALERT_ENABLED,
    MOISTURE_ALERT_LOW,
    MOISTURE_ALERT_ENABLED,
    ALERT_DEDUP,
)

logger = setup_sensor_logger()


class AlertSystem:
    """
    Modular alert system for monitoring sensor thresholds.
    Tracks alert state to prevent duplicate alerts within a period.
    Easy to extend with new alert types.
    """

    def __init__(self):
        """Initialize alert state tracking."""
        # Track active alerts by key to enable deduplication
        # Format: {alert_key: True} if currently violated
        self.active_alerts = {}

    def reset(self):
        """Reset all active alerts (call after sending alert emails)."""
        self.active_alerts.clear()

    def check_temperature(self, temp_f):
        """
        Check temperature against configured thresholds.

        Args:
            temp_f (float): Temperature in Fahrenheit

        Returns:
            tuple: (alert_triggered, alert_message)
                alert_triggered (bool): True if threshold violated
                alert_message (str): Human-readable alert message
        """
        if not TEMP_ALERT_ENABLED or temp_f is None:
            return False, None

        alerts = []

        # Check high temperature
        if temp_f > TEMP_ALERT_HIGH:
            alert_key = "temp_high"
            if not ALERT_DEDUP or not self.active_alerts.get(alert_key):
                alerts.append(f"🌡️ HIGH TEMPERATURE: {temp_f:.1f}°F (threshold: {TEMP_ALERT_HIGH}°F)")
                self.active_alerts[alert_key] = True
        else:
            self.active_alerts.pop("temp_high", None)

        # Check low temperature
        if temp_f < TEMP_ALERT_LOW:
            alert_key = "temp_low"
            if not ALERT_DEDUP or not self.active_alerts.get(alert_key):
                alerts.append(f"🌡️ LOW TEMPERATURE: {temp_f:.1f}°F (threshold: {TEMP_ALERT_LOW}°F)")
                self.active_alerts[alert_key] = True
        else:
            self.active_alerts.pop("temp_low", None)

        if alerts:
            return True, " | ".join(alerts)
        return False, None

    def check_co2(self, co2_ppm):
        """
        Check CO2 against configured thresholds.

        Args:
            co2_ppm (float): CO2 level in parts per million

        Returns:
            tuple: (alert_triggered, alert_message)
        """
        if not CO2_ALERT_ENABLED or co2_ppm is None:
            return False, None

        if co2_ppm > CO2_ALERT_HIGH:
            alert_key = "co2_high"
            if not ALERT_DEDUP or not self.active_alerts.get(alert_key):
                msg = f"⚠️ HIGH CO2: {co2_ppm:.0f} ppm (threshold: {CO2_ALERT_HIGH} ppm)"
                self.active_alerts[alert_key] = True
                return True, msg
        else:
            self.active_alerts.pop("co2_high", None)

        return False, None

    def check_humidity(self, humidity_pct):
        """
        Check humidity against configured thresholds.

        Args:
            humidity_pct (float): Humidity as percentage

        Returns:
            tuple: (alert_triggered, alert_message)
        """
        if not HUMIDITY_ALERT_ENABLED or humidity_pct is None:
            return False, None

        alerts = []

        # Check high humidity
        if humidity_pct > HUMIDITY_ALERT_HIGH:
            alert_key = "humidity_high"
            if not ALERT_DEDUP or not self.active_alerts.get(alert_key):
                alerts.append(f"💧 HIGH HUMIDITY: {humidity_pct:.1f}% (threshold: {HUMIDITY_ALERT_HIGH}%)")
                self.active_alerts[alert_key] = True
        else:
            self.active_alerts.pop("humidity_high", None)

        # Check low humidity
        if humidity_pct < HUMIDITY_ALERT_LOW:
            alert_key = "humidity_low"
            if not ALERT_DEDUP or not self.active_alerts.get(alert_key):
                alerts.append(f"💧 LOW HUMIDITY: {humidity_pct:.1f}% (threshold: {HUMIDITY_ALERT_LOW}%)")
                self.active_alerts[alert_key] = True
        else:
            self.active_alerts.pop("humidity_low", None)

        if alerts:
            return True, " | ".join(alerts)
        return False, None

    def check_moisture(self, moisture_pct):
        """
        Check soil moisture against configured thresholds.

        Args:
            moisture_pct (float): Soil moisture as percentage

        Returns:
            tuple: (alert_triggered, alert_message)
        """
        if not MOISTURE_ALERT_ENABLED or moisture_pct is None:
            return False, None

        if moisture_pct < MOISTURE_ALERT_LOW:
            alert_key = "moisture_low"
            if not ALERT_DEDUP or not self.active_alerts.get(alert_key):
                msg = f"🌱 LOW SOIL MOISTURE: {moisture_pct:.1f}% (threshold: {MOISTURE_ALERT_LOW}%)"
                self.active_alerts[alert_key] = True
                return True, msg
        else:
            self.active_alerts.pop("moisture_low", None)

        return False, None

    def check_all(self, co2_ppm=None, temp_f=None, humidity_pct=None, moisture_pct=None):
        """
        Check all enabled alerts and collect messages.

        Args:
            co2_ppm (float): CO2 level in ppm
            temp_f (float): Temperature in °F
            humidity_pct (float): Humidity percentage
            moisture_pct (float): Soil moisture percentage

        Returns:
            tuple: (any_alerts, messages_list)
                any_alerts (bool): True if any threshold violated
                messages_list (list): List of alert messages to send
        """
        messages = []

        # Check each sensor type
        temp_alert, temp_msg = self.check_temperature(temp_f)
        if temp_alert:
            messages.append(temp_msg)

        co2_alert, co2_msg = self.check_co2(co2_ppm)
        if co2_alert:
            messages.append(co2_msg)

        humidity_alert, humidity_msg = self.check_humidity(humidity_pct)
        if humidity_alert:
            messages.append(humidity_msg)

        moisture_alert, moisture_msg = self.check_moisture(moisture_pct)
        if moisture_alert:
            messages.append(moisture_msg)

        return len(messages) > 0, messages


def format_alert_body(alerts_list, co2=None, temp=None, humidity=None, moisture=None):
    """
    Format alert messages into an email body.

    Args:
        alerts_list (list): List of alert messages
        co2 (float): Current CO2 reading
        temp (float): Current temperature
        humidity (float): Current humidity
        moisture (float): Current moisture

    Returns:
        str: Formatted email body
    """
    body = "<h2>⚠️ Sensor Alert</h2>\n<p>"
    body += "<br>".join(alerts_list)
    body += "</p>\n<h3>Current Readings:</h3>\n<ul>\n"

    if co2 is not None:
        body += f"<li>CO2: {co2:.0f} ppm</li>\n"
    if temp is not None:
        body += f"<li>Temperature: {temp:.1f}°F</li>\n"
    if humidity is not None:
        body += f"<li>Humidity: {humidity:.1f}%</li>\n"
    if moisture is not None:
        body += f"<li>Soil Moisture: {moisture:.1f}%</li>\n"

    body += "</ul>\n<p>Check your PodsInSpace system immediately.</p>\n"

    return body
