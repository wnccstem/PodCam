#!/usr/bin/env python3
"""
Filename: sensors_ts.py
Description: Display co2, temperature, and humidity
from SCD41 sensor with integrated email notifications
!Connect to I2C bus
Press Ctrl+C to exit
"""
import api_key_ts
from datetime import datetime
from time import sleep

import requests

from co2_sensor_ts import CO2Sensor
from moisture_sensor_ts import MoistureSensor
from logging_config import setup_sensor_logger

# Create sensor objects
co2_sensor = CO2Sensor()
moisture_sensor = MoistureSensor()

# Import email notification system
from email_notification import EmailNotifier

# Import configuration constants
from config import (
    SENSOR_READ_INTERVAL,
    THINGSPEAK_INTERVAL,
    READINGS_PER_CYCLE,
    ENABLE_SCHEDULED_EMAILS,
    DAILY_EMAIL_TIME,
    SEND_EMAIL_ON_STARTUP,
)

# Import alert system
from alert_system import AlertSystem, format_alert_body
from alerts_config import ALERT_REALTIME

# Setup logging for sensors module
logger = setup_sensor_logger()

# Initialize email notification system
email_notifier = EmailNotifier()

# Initialize alert system
alert_system = AlertSystem()

# Substitute your api key in this file for updating your ThingSpeak channel
TS_KEY = api_key_ts.THINGSPEAK_API_KEY

# Global variables for email scheduling and water level tracking
# Track last sent date per scheduled time (keyed by 'HH:MM')
last_daily_email_dates = {}
# Track what 'next scheduled' message we've already logged to avoid spam
last_announced_next_email = None
previous_water_level = None

# Create ThingSpeak data dictionary
ts_data = {}

logger.info("PodsInSpace sensors send to ThingSpeak with email notifications")
logger.info(f"Reading sensors every {SENSOR_READ_INTERVAL} seconds")
logger.info(
    f"Averaging {READINGS_PER_CYCLE} readings over {THINGSPEAK_INTERVAL/60:.0f} minutes"
)
if ENABLE_SCHEDULED_EMAILS:
    # Display configured daily times (support string or list)
    try:
        if isinstance(DAILY_EMAIL_TIME, list):
            times_descr = ", ".join(DAILY_EMAIL_TIME)
        elif isinstance(DAILY_EMAIL_TIME, str) and "," in DAILY_EMAIL_TIME:
            times_descr = ", ".join(
                [t.strip() for t in DAILY_EMAIL_TIME.split(",")]
            )
        else:
            times_descr = str(DAILY_EMAIL_TIME)
    except Exception:
        times_descr = str(DAILY_EMAIL_TIME)

    logger.info(f"Daily summary emails at {times_descr}")
    logger.info("Water level change alerts enabled")
logger.info("Ctrl+C to exit!")


# ------------------------ CALCULATE TRIMMED MEAN -------------------------- #
def calculate_trimmed_mean(readings, trim_percent=0.1):
    """
    Calculate trimmed mean by removing outliers from the dataset.
    Removes trim_percent from both ends of the sorted data.
    Default removes 10% from each end (20% total).
    """
    if not readings:
        return 0.0

    if len(readings) == 1:
        return readings[0]

    # Sort the readings
    sorted_readings = sorted(readings)

    # Calculate number of values to trim from each end
    trim_count = max(1, int(len(sorted_readings) * trim_percent))

    # Ensure we don't trim all values
    if trim_count * 2 >= len(sorted_readings):
        trim_count = 0

    # Remove outliers from both ends
    if trim_count > 0:
        trimmed_readings = sorted_readings[trim_count:-trim_count]
    else:
        trimmed_readings = sorted_readings

    # Calculate and return the mean
    return sum(trimmed_readings) / len(trimmed_readings)


# ---------------- GET CURRENT SENSOR DATA FOR EMAIL ----------------------- #
def get_current_sensor_data_for_email(
    co2, temp_f, humidity, moisture_pct=None, moisture_status=None, temp_c=None
):
    """
    Format current sensor readings for email reports.

    Args:
        cco2: CO2 concentration in ppm
        temp_f: Air temperature in Fahrenheit
        humidity: Humidity percentage

    Returns:
        dict: Formatted sensor data
        str: System status
    """
    try:

        # Format sensor data
        # Show temperature in Fahrenheit
        if temp_f is not None:
            air_temp_str = f"{temp_f:.1f} °F"
        else:
            air_temp_str = "No data"

        sensor_data = {
            "CO2": (f"{co2} ppm" if co2 is not None else "No data"),
            "Air Temperature": air_temp_str,
            "Humidity": (
                f"{humidity:.1f}%" if humidity is not None else "No data"
            ),
        }

        if moisture_pct is not None:
            sensor_data["Soil Moisture"] = f"{moisture_pct:.1f}%"
        else:
            sensor_data["Soil Moisture"] = "No data"
        if moisture_status is not None:
            sensor_data["Soil Moisture Status"] = moisture_status

        # Determine system status
        system_status = "Normal"
        return sensor_data, system_status

    except Exception as e:
        logger.error(f"Error formatting sensor data for email: {e}")
        return {
            "Soil Moisture": "Error",
            "Soil Moisture Status": "Error",
            "CO2": "Error",
            "Air Temperature": "Error",
            "Humidity": "Error",
        }, "Critical"


def should_send_daily_email():
    """Determine if it's time to send the daily summary email.

    Behavior:
    - Do NOT catch up on missed earlier times the same day.
    - Only send for the next upcoming configured time for today.
    - Trigger within a small grace window around the target time to tolerate loop delays.

    Returns a list with at most one time string when it's due now.
    """

    global last_daily_email_dates

    if not ENABLE_SCHEDULED_EMAILS:
        return []

    now = datetime.now()
    current_date = now.date()

    # Parse configured times
    if isinstance(DAILY_EMAIL_TIME, list):
        times_list = [t.strip() for t in DAILY_EMAIL_TIME]
    elif isinstance(DAILY_EMAIL_TIME, str):
        if "," in DAILY_EMAIL_TIME:
            times_list = [
                t.strip() for t in DAILY_EMAIL_TIME.split(",") if t.strip()
            ]
        else:
            times_list = [DAILY_EMAIL_TIME.strip()]
    else:
        times_list = [str(DAILY_EMAIL_TIME)]

    # Build today datetimes for each configured time
    candidates = []
    for t in times_list:
        try:
            h, m = map(int, t.split(":"))
            dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
            candidates.append((t, dt))
        except Exception:
            continue

    if not candidates:
        return []

    # Choose the next upcoming scheduled time today (>= now), or none if all past
    upcoming_today = [(t, dt) for (t, dt) in candidates if dt >= now]
    if not upcoming_today:
        # All today's times are past; do not catch up
        return []

    next_t, next_dt = min(upcoming_today, key=lambda x: x[1])

    # Only send once per day per scheduled time
    if last_daily_email_dates.get(next_t) == current_date:
        return []

    # Grace window to allow the main loop to catch the moment (e.g., +/- 2 minutes)
    grace_seconds = max(
        60, int(SENSOR_READ_INTERVAL) * 4
    )  # at least 1 min, typically 2 min

    delta_sec = (now - next_dt).total_seconds()
    # Detailed visibility into scheduler decision
    try:
        logger.debug(
            f"Scheduler check: now={now.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"next={next_dt.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"delta_sec={delta_sec:.1f}, window=±{grace_seconds}s"
        )
    except Exception:
        pass

    if -grace_seconds <= delta_sec <= grace_seconds:
        logger.debug(f"Scheduler: within window for {next_t} → SEND")
        return [next_t]

    if delta_sec < -grace_seconds:
        logger.debug("Scheduler: not yet in window → WAIT")
    else:
        logger.debug("Scheduler: missed window; will not catch up → SKIP")

    return []


# ------------------------ GET NEXT DAILY EMAIL TIME ----------------------- #
def get_next_daily_email_time():
    """Compute the next scheduled time and whether it's today or tomorrow.

    Returns:
        tuple: (time_str 'HH:MM', 'today'|'tomorrow'), or None if misconfigured
    """
    try:
        now = datetime.now()

        # Normalize configured times
        if isinstance(DAILY_EMAIL_TIME, list):
            scheduled_times = [t.strip() for t in DAILY_EMAIL_TIME]
        elif isinstance(DAILY_EMAIL_TIME, str):
            if "," in DAILY_EMAIL_TIME:
                scheduled_times = [
                    t.strip() for t in DAILY_EMAIL_TIME.split(",") if t.strip()
                ]
            else:
                scheduled_times = [DAILY_EMAIL_TIME.strip()]
        else:
            scheduled_times = [str(DAILY_EMAIL_TIME)]

        # Build today datetimes
        parsed = []
        for t in scheduled_times:
            try:
                h, m = map(int, t.split(":"))
                parsed.append(
                    (t, now.replace(hour=h, minute=m, second=0, microsecond=0))
                )
            except Exception:
                continue

        if not parsed:
            return None

        # Next upcoming today
        upcoming_today = [(t, dt) for (t, dt) in parsed if dt >= now]
        if upcoming_today:
            next_t, next_dt = min(upcoming_today, key=lambda x: x[1])
            try:
                logger.debug(
                    f"Next email time (today): {next_t} at {next_dt.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            except Exception:
                pass
            return next_t, "today"

        # Otherwise earliest tomorrow
        next_t, earliest_dt = min(parsed, key=lambda x: x[1])
        try:
            logger.debug(
                f"Next email time (tomorrow): {next_t} (today's time has passed)"
            )
        except Exception:
            pass
        return next_t, "tomorrow"

    except Exception:
        return None


# ---------------------- SEND DAILY SUMMARY EMAIL -------------------------- #
def send_daily_summary_email(
    moisture_pct,
    moisture_status,
    co2,
    temp_f,
    humidity,
    scheduled_time=None,
):
    """Send daily summary email."""

    try:
        logger.info("📧 Sending daily summary email")

        # Calculate temp_f if temp_c is provided
        sensor_data, system_status = get_current_sensor_data_for_email(
            co2,
            temp_f,
            humidity,
            moisture_pct=moisture_pct,
            moisture_status=moisture_status,
        )

        success = email_notifier.send_status_report(
            recipient_email=None,  # Uses DEFAULT_RECIPIENT_EMAILS for multiple recipients
            sensor_data=sensor_data,
            system_status=system_status,
        )

        if success:
            # Record last sent date for this scheduled_time (or default key)
            key = scheduled_time if scheduled_time else "default"
            last_daily_email_dates[key] = datetime.now().date()
            logger.info("✅ Daily summary email sent successfully")
        else:
            logger.error("❌ Failed to send daily summary email")

    except Exception as e:
        logger.error(f"Error sending daily summary email: {e}")


def main():
    # Initialize lists to store readings for averaging
    moisture_readings = []
    co2_readings = []
    temp_readings = []
    humidity_readings = []

    # Moisture sensor tracking
    moisture_pct = None
    moisture_status_last = None
    moisture_sensor = MoistureSensor()

    # Send initial reading on startup
    initial_reading_sent = False
    # Optional: send an initial status email at startup
    startup_email_sent = False

    try:
        # On startup, log next scheduled daily email time once
        if ENABLE_SCHEDULED_EMAILS:
            try:
                nxt = get_next_daily_email_time()
                if nxt:
                    t_str, when = nxt
                    logger.info(
                        f"Next daily email scheduled for {t_str} ({when})"
                    )
            except Exception:
                pass

        while True:
            # Read SCD41 sensor data using the abstracted module (read once per loop)
            co2, temp_f, humidity = co2_sensor.read_sensors()

            # Read moisture sensor data
            moisture_data = moisture_sensor.read_sensor()
            if moisture_data is not None:
                moisture_pct = moisture_data.get("moisture_percent")
                moisture_status_last = moisture_data.get("status")
            else:
                moisture_pct = None
                moisture_status_last = None

            # Check if SCD41 sensor data was retrieved successfully
            if co2 is not None and temp_f is not None and humidity is not None:

                # Log reading with moisture status
                if moisture_pct is not None:
                    logger.info(
                        f"Reading {len(temp_readings)+1}/{READINGS_PER_CYCLE}: {co2:.0f} ppm | {temp_f:.1f} °F | {humidity:.1f}% | Moisture: {moisture_pct:.1f}% ({moisture_status_last})"
                    )
                else:
                    logger.info(
                        f"Reading {len(temp_readings)+1}/{READINGS_PER_CYCLE}: {co2:.0f} ppm | {temp_f:.1f} °F | {humidity:.1f}% | Moisture: No data"
                    )

                # Add readings to lists for averaging
                co2_readings.append(co2)
                temp_readings.append(temp_f)
                humidity_readings.append(humidity)
                if moisture_pct is not None:
                    moisture_readings.append(moisture_pct)

                # Optional: real-time alerting based on individual readings
                if ALERT_REALTIME:
                    try:
                        rt_alerts, rt_messages = alert_system.check_all(
                            co2_ppm=co2,
                            temp_f=temp_f,
                            humidity_pct=humidity,
                            moisture_pct=moisture_pct,
                        )
                        if rt_alerts:
                            logger.warning(
                                f"REALTIME ALERT: {' | '.join(rt_messages)}"
                            )

                            # Build alert body using current readings
                            rt_body = format_alert_body(
                                rt_messages,
                                co2=co2,
                                temp=temp_f,
                                humidity=humidity,
                                moisture=moisture_pct,
                            )

                            # Subject: 'Alert Cleared' if all messages are informational
                            only_info_rt = all(str(m).strip().startswith("ℹ️") for m in rt_messages if m)
                            subject_type_rt = "Alert Cleared" if only_info_rt else "Sensor Threshold"

                            logger.info(f"Preparing to send real-time alert - Type: {subject_type_rt}, Message count: {len(rt_messages)}")
                            
                            sent = email_notifier.send_alert(
                                recipient_email=None,
                                alert_type=subject_type_rt,
                                alert_message=rt_body,
                            )
                            if sent:
                                logger.info(f"📧 Real-time alert email sent successfully - Subject: {subject_type_rt}")
                            else:
                                logger.error(f"📧 Real-time alert email FAILED - Subject: {subject_type_rt}, Alert count: {len(rt_messages)}")

                            # Do not reset here; AlertSystem enforces per-violation limits
                    except Exception as e:
                        logger.error(f"Error in real-time alerting: {e}", exc_info=True)

                # Check for scheduled emails using current readings
                if ENABLE_SCHEDULED_EMAILS:
                    # Check for daily summary email(s)
                    due = should_send_daily_email()
                    if due:
                        for scheduled_time in due:
                            send_daily_summary_email(
                                moisture_pct,
                                moisture_status_last,
                                co2,
                                temp_f,
                                humidity,
                                scheduled_time=scheduled_time,
                            )

                        # After sending, announce the next schedule time
                        try:
                            nxt = get_next_daily_email_time()
                            if nxt:
                                t_str, when = nxt
                                logger.info(
                                    f"Next daily email scheduled for {t_str} ({when})"
                                )
                        except Exception:
                            pass
                    else:
                        # Periodically announce only when it changes
                        try:
                            global last_announced_next_email
                            nxt = get_next_daily_email_time()
                            if nxt:
                                t_str, when = nxt
                                descriptor = f"{when}:{t_str}"
                                if descriptor != last_announced_next_email:
                                    logger.info(
                                        f"Next daily email scheduled for {t_str} ({when})"
                                    )
                                    last_announced_next_email = descriptor
                        except Exception:
                            pass

                # Send initial reading on startup
                if not initial_reading_sent:
                    logger.info("Sending initial reading to ThingSpeak")
                    thingspeak_send(
                        co2,
                        temp_f,
                        humidity,
                        moisture_pct,
                    )
                    initial_reading_sent = True

                # Optionally send a startup status email once (not nested - runs every iteration until sent)
                if SEND_EMAIL_ON_STARTUP and not startup_email_sent:
                    try:
                        sensor_data, system_status = (
                            get_current_sensor_data_for_email(
                                co2,
                                temp_f,
                                humidity,
                                moisture_pct=moisture_pct,
                                moisture_status=moisture_status_last
                            )
                        )
                        if email_notifier.send_status_report(
                            recipient_email=None,
                            sensor_data=sensor_data,
                            system_status=system_status,
                            dedup_key="startup_status",
                        ):
                            logger.info("📧 Startup status email sent")
                            startup_email_sent = True
                        else:
                            logger.warning(
                                "Failed to send startup status email"
                            )
                    except Exception as e:
                        logger.error(
                            f"Error during startup email send: {e}"
                        )

                # Check if we have enough readings for averaging
                if len(temp_readings) >= READINGS_PER_CYCLE:
                    # Calculate averages using trimmed mean (remove outliers)
                    avg_co2 = calculate_trimmed_mean(co2_readings)
                    avg_temp = calculate_trimmed_mean(temp_readings)
                    avg_humidity = calculate_trimmed_mean(humidity_readings)
                    avg_moisture = (
                        calculate_trimmed_mean(moisture_readings)
                        if moisture_readings
                        else None
                    )
                    logger.info(f"Avg CO2: {int(avg_co2)} ppm")
                    logger.info(f"Avg Temperature: {avg_temp:.1f} °F")
                    logger.info(f"Avg Humidity: {avg_humidity:.1f}%")
                    if avg_moisture is not None:
                        logger.info(
                            f"Avg Moisture: {avg_moisture:.1f}% ({moisture_status_last or ''})"
                        )

                    # Send averaged data to ThingSpeak
                    thingspeak_send(
                        avg_co2,
                        avg_temp,
                        avg_humidity,
                        avg_moisture,
                    )

                    # Check sensor thresholds and send alerts if needed
                    has_alerts, alert_messages = alert_system.check_all(
                        co2_ppm=avg_co2,
                        temp_f=avg_temp,
                        humidity_pct=avg_humidity,
                        moisture_pct=avg_moisture,
                    )

                    if has_alerts:
                        logger.warning(f"ALERT: {' | '.join(alert_messages)}")
                        try:
                            # Format alert email subject from messages
                            alert_type = " | ".join(
                                [msg.split(":")[0] for msg in alert_messages]
                            )

                            # Format alert email body
                            alert_body = format_alert_body(
                                alert_messages,
                                co2=avg_co2,
                                temp=avg_temp,
                                humidity=avg_humidity,
                                moisture=avg_moisture,
                            )

                            # Send alert email
                            if email_notifier.send_alert(
                                recipient_email=None,
                                alert_type="Sensor Threshold",
                                alert_message=alert_body,
                            ):
                                logger.info("📧 Alert email sent successfully")
                            else:
                                logger.warning("⚠️ Alert email not sent (deduped or failed)")
                        except Exception as e:
                            logger.error(f"❌ Error sending alert email: {e}")

                        # Reset alerts for next cycle
                        alert_system.reset()

                    # Clear the reading lists for the next cycle
                    moisture_readings.clear()
                    co2_readings.clear()
                    temp_readings.clear()
                    humidity_readings.clear()

                # Sleep for 30 seconds before next reading
                sleep(SENSOR_READ_INTERVAL)
            else:
                logger.warning("Failed to get SCD41 sensor data")
                sleep(5)  # Short sleep before retrying

    except KeyboardInterrupt:
        logger.info("Bye!")

        exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

        # Sleep before potential restart
        sleep(600)


# ---------------------------- THINGSPEAK SEND ----------------------------- #
def thingspeak_send(co2, temp, hum, moisture):
    """Update the ThingSpeak channel using the requests library.

        Note: The ThingSpeak channel is configured as:
            - field1 = CO2 (ppm)
            - field2 = Humidity (%)
            - field3 = Temperature (°F)
            - field4 = Soil Moisture (%)

    If your channel uses a different field ordering, adjust the mapping below
    or make it configurable in config.py.
    """
    logger.info("Update Thingspeak Channel")

    # Map to channel fields (field1=humidity, field2=temperature, field3=pressure)
    params = {
        "api_key": TS_KEY,
        "field1": co2,
        "field2": temp,
        "field3": hum,
        "field4": moisture,
    }

    # Detailed payload log for diagnostics
    try:
        logger.debug(
            "ThingSpeak payload -> "
            f"field1(co2)={co2}ppm, "
            f"field2(temp)={temp:.1f}°F, "
            f"field1(humidity)={hum:.1f}%, "
            + (f"field4(moisture)={moisture:.1f}%")
        )
    except Exception:
        pass

    try:
        # Update data on Thingspeak
        ts_update = requests.get(
            "https://api.thingspeak.com/update", params=params, timeout=30
        )

        # Was the update successful?
        if ts_update.status_code == requests.codes.ok:
            logger.info("Data Received!")
        else:
            logger.error("Error Code: " + str(ts_update.status_code))

        # Print ThingSpeak response to console
        # ts_update.text is the thingspeak data entry number in the channel
        logger.info(f"ThingSpeak Channel Entry: {ts_update.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error sending to ThingSpeak: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in thingspeak_send: {e}")


# If a standalone program, call the main function
# Else, use as a module
if __name__ == "__main__":
    logger.info("Starting sensors ThingSpeak service...")
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")

        exit(0)
    except Exception as e:
        logger.critical(f"Critical error in main: {e}")

        exit(1)
