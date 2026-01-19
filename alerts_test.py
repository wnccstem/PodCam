#!/usr/bin/env python3
"""
Filename: alerts_test.py
Description: Menu-based testing utility for alert system
Test upper and lower limits without waiting for sensor readings

Usage:
    python3 alerts_test.py               # Opens interactive menu
    Simply follow the menu prompts to select your test
"""

import sys
from alert_system import AlertSystem, format_alert_body
from alerts_config import (
    TEMP_ALERT_HIGH,
    TEMP_ALERT_LOW,
    CO2_ALERT_HIGH,
    HUMIDITY_ALERT_HIGH,
    HUMIDITY_ALERT_LOW,
    MOISTURE_ALERT_LOW,
)
from config import DEFAULT_RECIPIENT_EMAILS
from email_notification import EmailNotifier
from logging_config import setup_sensor_logger

logger = setup_sensor_logger()


class AlertTester:
    """Test alert system with custom sensor values."""

    def __init__(self):
        self.alert_system = AlertSystem()
        self.email_notifier = EmailNotifier()

    def test_temperature(self, temp_f, send_email=True):
        """Test temperature alert at specific value."""
        print(f"\n{'='*60}")
        print(f"Testing Temperature Alert: {temp_f}°F")
        print(f"{'='*60}")
        print(f"Configured thresholds: {TEMP_ALERT_LOW}°F - {TEMP_ALERT_HIGH}°F")

        # Check alert
        has_alert, msg = self.alert_system.check_temperature(temp_f)

        if has_alert:
            print(f"✓ ALERT TRIGGERED: {msg}")
        else:
            print(f"✗ No alert (within safe range)")

        # Send email if alert triggered
        if has_alert and send_email:
            self._send_test_email([msg], temp=temp_f)

        return has_alert

    def test_co2(self, co2_ppm, send_email=True):
        """Test CO2 alert at specific value."""
        print(f"\n{'='*60}")
        print(f"Testing CO2 Alert: {co2_ppm} ppm")
        print(f"{'='*60}")
        print(f"Configured threshold: > {CO2_ALERT_HIGH} ppm")

        # Check alert
        has_alert, msg = self.alert_system.check_co2(co2_ppm)

        if has_alert:
            print(f"✓ ALERT TRIGGERED: {msg}")
        else:
            print(f"✗ No alert (within safe range)")

        # Send email if alert triggered
        if has_alert and send_email:
            self._send_test_email([msg], co2=co2_ppm)

        return has_alert

    def test_humidity(self, humidity_pct, send_email=True):
        """Test humidity alert at specific value."""
        print(f"\n{'='*60}")
        print(f"Testing Humidity Alert: {humidity_pct}%")
        print(f"{'='*60}")
        print(
            f"Configured thresholds: {HUMIDITY_ALERT_LOW}% - {HUMIDITY_ALERT_HIGH}%"
        )

        # Check alert
        has_alert, msg = self.alert_system.check_humidity(humidity_pct)

        if has_alert:
            print(f"✓ ALERT TRIGGERED: {msg}")
        else:
            print(f"✗ No alert (within safe range)")

        # Send email if alert triggered
        if has_alert and send_email:
            self._send_test_email([msg], humidity=humidity_pct)

        return has_alert

    def test_moisture(self, moisture_pct, send_email=True):
        """Test moisture alert at specific value."""
        print(f"\n{'='*60}")
        print(f"Testing Soil Moisture Alert: {moisture_pct}%")
        print(f"{'='*60}")
        print(f"Configured threshold: < {MOISTURE_ALERT_LOW}%")

        # Check alert
        has_alert, msg = self.alert_system.check_moisture(moisture_pct)

        if has_alert:
            print(f"✓ ALERT TRIGGERED: {msg}")
        else:
            print(f"✗ No alert (within safe range)")

        # Send email if alert triggered
        if has_alert and send_email:
            self._send_test_email([msg], moisture=moisture_pct)

        return has_alert

    def test_all_at_limits(self, send_email=True):
        """Test all sensors at upper and lower limits."""
        print(f"\n{'='*70}")
        print("COMPREHENSIVE ALERT SYSTEM TEST - ALL SENSORS AT LIMITS")
        print(f"{'='*70}")

        all_alerts = []

        # Test high temperature
        print(f"\n1. HIGH TEMPERATURE TEST ({TEMP_ALERT_HIGH + 2}°F)")
        has_alert = self.test_temperature(TEMP_ALERT_HIGH + 2, send_email=False)
        if has_alert:
            _, msg = self.alert_system.check_temperature(TEMP_ALERT_HIGH + 2)
            all_alerts.append(msg)

        # Test low temperature
        print(f"\n2. LOW TEMPERATURE TEST ({TEMP_ALERT_LOW - 2}°F)")
        has_alert = self.test_temperature(TEMP_ALERT_LOW - 2, send_email=False)
        if has_alert:
            _, msg = self.alert_system.check_temperature(TEMP_ALERT_LOW - 2)
            all_alerts.append(msg)

        # Test high CO2
        print(f"\n3. HIGH CO2 TEST ({CO2_ALERT_HIGH + 100} ppm)")
        has_alert = self.test_co2(CO2_ALERT_HIGH + 100, send_email=False)
        if has_alert:
            _, msg = self.alert_system.check_co2(CO2_ALERT_HIGH + 100)
            all_alerts.append(msg)

        # Test high humidity
        print(f"\n4. HIGH HUMIDITY TEST ({HUMIDITY_ALERT_HIGH + 5}%)")
        has_alert = self.test_humidity(HUMIDITY_ALERT_HIGH + 5, send_email=False)
        if has_alert:
            _, msg = self.alert_system.check_humidity(HUMIDITY_ALERT_HIGH + 5)
            all_alerts.append(msg)

        # Test low humidity
        print(f"\n5. LOW HUMIDITY TEST ({HUMIDITY_ALERT_LOW - 5}%)")
        has_alert = self.test_humidity(HUMIDITY_ALERT_LOW - 5, send_email=False)
        if has_alert:
            _, msg = self.alert_system.check_humidity(HUMIDITY_ALERT_LOW - 5)
            all_alerts.append(msg)

        # Test low moisture
        print(f"\n6. LOW MOISTURE TEST ({MOISTURE_ALERT_LOW - 5}%)")
        has_alert = self.test_moisture(MOISTURE_ALERT_LOW - 5, send_email=False)
        if has_alert:
            _, msg = self.alert_system.check_moisture(MOISTURE_ALERT_LOW - 5)
            all_alerts.append(msg)

        # Send combined email if requested
        print(f"\n{'='*70}")
        print(f"Summary: {len(all_alerts)} alerts triggered")
        print(f"{'='*70}")

        if all_alerts and send_email:
            print("\nSending combined test email...")
            self._send_test_email(all_alerts)

        return len(all_alerts)

    def _send_test_email(self, alert_messages, co2=None, temp=None, humidity=None, moisture=None):
        """Send a test alert email to recipients configured in config.py."""
        try:
            # Format email body
            body = format_alert_body(
                alert_messages,
                co2=co2,
                temp=temp,
                humidity=humidity,
                moisture=moisture,
            )

            print("\n📧 Sending test email to:")
            for recipient in DEFAULT_RECIPIENT_EMAILS:
                print(f"   - {recipient}")

            # Send alert email using recipients from config.py
            if self.email_notifier.send_alert(
                recipient_email=DEFAULT_RECIPIENT_EMAILS,
                alert_type="TEST: Sensor Threshold",
                alert_message=body,
            ):
                print("✓ Test email sent successfully!")
                logger.info("Test alert email sent")
            else:
                print("✗ Test email failed (may be deduped)")
                logger.warning("Test alert email failed or deduped")

        except Exception as e:
            print(f"✗ Error sending email: {e}")
            logger.error(f"Error sending test email: {e}")

    def interactive_menu(self):
        """Interactive testing menu."""
        while True:
            print(f"\n{'='*60}")
            print("ALERT SYSTEM TEST MENU")
            print(f"{'='*60}")
            print("1. Test Temperature High")
            print("2. Test Temperature Low")
            print("3. Test Temperature Custom")
            print("4. Test CO2 High")
            print("5. Test CO2 Custom")
            print("6. Test Humidity High")
            print("7. Test Humidity Low")
            print("8. Test Humidity Custom")
            print("9. Test Moisture Low")
            print("10. Test Moisture Custom")
            print("11. Test ALL Limits (No Email)")
            print("12. Test ALL Limits (With Email)")
            print("13. View Current Thresholds")
            print("0. Exit")
            print(f"{'='*60}")

            choice = input("Select option: ").strip()

            if choice == "0":
                print("Exiting...")
                break

            elif choice == "1":
                self.test_temperature(TEMP_ALERT_HIGH + 2)

            elif choice == "2":
                self.test_temperature(TEMP_ALERT_LOW - 2)

            elif choice == "3":
                try:
                    temp = float(input(f"Enter temperature (°F): "))
                    self.test_temperature(temp)
                except ValueError:
                    print("Invalid input")

            elif choice == "4":
                self.test_co2(CO2_ALERT_HIGH + 100)

            elif choice == "5":
                try:
                    co2 = float(input("Enter CO2 (ppm): "))
                    self.test_co2(co2)
                except ValueError:
                    print("Invalid input")

            elif choice == "6":
                self.test_humidity(HUMIDITY_ALERT_HIGH + 5)

            elif choice == "7":
                self.test_humidity(HUMIDITY_ALERT_LOW - 5)

            elif choice == "8":
                try:
                    humidity = float(input("Enter humidity (%): "))
                    self.test_humidity(humidity)
                except ValueError:
                    print("Invalid input")

            elif choice == "9":
                self.test_moisture(MOISTURE_ALERT_LOW - 5)

            elif choice == "10":
                try:
                    moisture = float(input("Enter moisture (%): "))
                    self.test_moisture(moisture)
                except ValueError:
                    print("Invalid input")

            elif choice == "11":
                self.test_all_at_limits()

            elif choice == "12":
                self.test_all_at_limits()

            elif choice == "13":
                self.show_thresholds()

            else:
                print("Invalid option")

    def show_thresholds(self):
        """Display current configured thresholds."""
        print(f"\n{'='*60}")
        print("CURRENT ALERT THRESHOLDS")
        print(f"{'='*60}")
        print(f"Temperature:  {TEMP_ALERT_LOW}°F - {TEMP_ALERT_HIGH}°F")
        print(f"CO2:          > {CO2_ALERT_HIGH} ppm")
        print(f"Humidity:     {HUMIDITY_ALERT_LOW}% - {HUMIDITY_ALERT_HIGH}%")
        print(f"Moisture:     < {MOISTURE_ALERT_LOW}%")
        print(f"{'='*60}\n")


def main():
    """Main entry point - shows interactive menu."""
    tester = AlertTester()
    tester.interactive_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Test error: {e}")
        sys.exit(1)
