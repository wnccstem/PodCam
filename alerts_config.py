"""
Configuration file for sensor alerts
Define thresholds and alert settings here for easy maintenance
"""

# Temperature Alert Thresholds
TEMP_ALERT_HIGH = 85 # 85°F - Alert if temperature exceeds this
TEMP_ALERT_LOW =  70 # 70°F - Alert if temperature drops below this
TEMP_ALERT_ENABLED = False

# CO2 Alert Thresholds
CO2_ALERT_HIGH = 1500  # ppm - Alert if CO2 exceeds this
CO2_ALERT_ENABLED = False  # Set to True to enable CO2 alerts

# Humidity Alert Thresholds
HUMIDITY_ALERT_HIGH = 85  # 85% - Alert if humidity exceeds this
HUMIDITY_ALERT_LOW = 65  # 65% - Alert if humidity drops below this
HUMIDITY_ALERT_ENABLED = False  # Set to True to enable humidity alerts

# Moisture Alert Thresholds
MOISTURE_ALERT_LOW = 20  # % - Alert if soil moisture drops below this
MOISTURE_ALERT_ENABLED = False  # Set to True to enable moisture alerts

# Alert Behavior
# Only send alerts at ThingSpeak interval (matching sensor averaging)
# Set to True to send alerts immediately on violation
ALERT_REALTIME = False

# Dedup alerts - only send once per violation cycle
# Prevents spam if threshold is violated for multiple averaging periods
ALERT_DEDUP = True

