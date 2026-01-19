# Alert System Testing Guide

## Overview

The `test_alerts.py` script allows you to manually test alert triggers without waiting for actual sensor readings to exceed thresholds.

## Quick Start: Test Temperature Limits

### Test High Temperature (above threshold)
```bash
python3 test_alerts.py --high-temp
```
Output:
```
==============================================================
Testing Temperature Alert: 87°F
==============================================================
Configured thresholds: 70°F - 85°F
✓ ALERT TRIGGERED: 🌡️ HIGH TEMPERATURE: 87°F (threshold: 85°F)
```

### Test Low Temperature (below threshold)
```bash
python3 test_alerts.py --low-temp
```
Output:
```
==============================================================
Testing Temperature Alert: 68°F
==============================================================
Configured thresholds: 70°F - 85°F
✓ ALERT TRIGGERED: 🌡️ LOW TEMPERATURE: 68°F (threshold: 70°F)
```

### Test Safe Range (no alert)
```bash
python3 test_alerts.py --temp 72
```
Output:
```
==============================================================
Testing Temperature Alert: 72°F
==============================================================
Configured thresholds: 70°F - 85°F
✗ No alert (within safe range)
```

---

## All Testing Options

### Command Line Mode

#### Test Specific Sensor Values
```bash
# Test temperature at custom value
python3 test_alerts.py --temp 87

# Test CO2 at custom value
python3 test_alerts.py --co2 1600

# Test humidity at custom value
python3 test_alerts.py --humidity 88

# Test moisture at custom value
python3 test_alerts.py --moisture 15
```

#### Test Quick Limits
```bash
# Test high temperature (High threshold + 2)
python3 test_alerts.py --high-temp

# Test low temperature (Low threshold - 2)
python3 test_alerts.py --low-temp

# Test all sensors at extreme limits (no email)
python3 test_alerts.py --all

# Test all sensors at extreme limits (WITH email)
python3 test_alerts.py --all --send-email
```

#### Send Test Email
```bash
# Test temperature AND send email if alert triggered
python3 test_alerts.py --temp 87 --send-email

# Test CO2 AND send email
python3 test_alerts.py --co2 1700 --send-email

# Test all limits AND send email
python3 test_alerts.py --all --send-email
```

### Interactive Mode

Run without arguments for menu-driven testing:
```bash
python3 test_alerts.py
# or
python3 test_alerts.py -i
```

Menu Options:
```
1. Test Temperature High       (Above upper limit)
2. Test Temperature Low        (Below lower limit)
3. Test Temperature Custom     (Any value you enter)
4. Test CO2 High              (Above limit)
5. Test CO2 Custom            (Any value)
6. Test Humidity High         (Above limit)
7. Test Humidity Low          (Below limit)
8. Test Humidity Custom       (Any value)
9. Test Moisture Low          (Below limit)
10. Test Moisture Custom       (Any value)
11. Test ALL Limits (No Email) (All extremes, no email)
12. Test ALL Limits (With Email) (All extremes + send email)
13. View Current Thresholds    (Show configured limits)
0. Exit
```

---

## Common Testing Scenarios

### Scenario 1: Verify High Temp Alert Works
```bash
# 1. Test the alert triggers
python3 test_alerts.py --high-temp

# 2. Verify it triggers (should see ✓ ALERT TRIGGERED)
# 3. Check current config
python3 test_alerts.py
# Then select option 13 to view thresholds
```

### Scenario 2: Verify Email Delivery
```bash
# 1. Test and send email
python3 test_alerts.py --high-temp --send-email

# 2. Watch for output
# Output: ✓ Test email sent successfully!

# 3. Check inbox for email from wnccrobotics@gmail.com
# Subject: "PodsInSpace Sensor Threshold Alert"
```

### Scenario 3: Test Multiple Sensors
```bash
# 1. Run comprehensive test
python3 test_alerts.py --all

# 2. View results for each sensor:
#    - High Temperature ✓
#    - Low Temperature ✓
#    - High CO2 ✓
#    - High Humidity ✓
#    - Low Humidity ✓
#    - Low Moisture ✓

# 3. Optionally with email
python3 test_alerts.py --all --send-email
```

### Scenario 4: Test Custom Threshold
```bash
# 1. You suspect a sensor is wrong
# 2. Test with expected value
python3 test_alerts.py --temp 75.5

# 3. See if alert triggers (should NOT at 75.5)
# 4. Test just above limit
python3 test_alerts.py --temp 85.1

# 5. Should trigger now (✓ ALERT TRIGGERED)
```

---

## Understanding Test Output

### Alert Triggered (✓)
```
✓ ALERT TRIGGERED: 🌡️ HIGH TEMPERATURE: 87°F (threshold: 85°F)
```
- **Meaning**: Alert would be sent at this value
- **Action**: Email system would be triggered
- **Email sent?**: Only if you use `--send-email`

### No Alert (✗)
```
✗ No alert (within safe range)
```
- **Meaning**: This value is safe, no alert
- **Action**: Email would NOT be sent
- **Status**: System working correctly for safe values

### Test Email Sent
```
📧 Sending test email...
✓ Test email sent successfully!
```
- **Meaning**: Email was queued for sending
- **Check**: Look in inbox (may take a few seconds)
- **Note**: If deduped, you may need to clear state

### Test Email Deduped
```
✗ Test email failed (may be deduped)
```
- **Meaning**: Email system suppressed it (duplicate)
- **Why**: Recent identical alert already sent
- **Fix**: Clear email state: `rm logs/email_send_state.json`

---

## Testing Workflow

### 1. Initial Setup Test
```bash
# Verify system is configured and working
python3 test_alerts.py --all

# All 6 should show ✓ ALERT TRIGGERED
# If any show ✗, check alerts_config.py
```

### 2. Email Delivery Test
```bash
# Test that emails actually send
python3 test_alerts.py --high-temp --send-email

# Check output for:
# - ✓ ALERT TRIGGERED
# - ✓ Test email sent successfully!

# Then check your email inbox
```

### 3. Threshold Verification
```bash
# Test at exact threshold values
python3 test_alerts.py --temp 85        # At limit
python3 test_alerts.py --temp 85.1      # Above limit
python3 test_alerts.py --temp 70        # At limit
python3 test_alerts.py --temp 69.9      # Below limit
```

### 4. Custom Sensor Test
```bash
# Test with your specific setup values
python3 test_alerts.py --humidity 65    # Your typical humidity
python3 test_alerts.py --humidity 85    # At alert threshold

# Verify which triggers and which doesn't
```

---

## Clearing Email State for Re-testing

If you want to re-test email sending and it's deduped:

```bash
# Option 1: Clear entire state file
rm logs/email_send_state.json

# Option 2: Clear just sensor alert state
python3 << 'EOF'
import json
import os

state_file = "logs/email_send_state.json"
if os.path.exists(state_file):
    with open(state_file, "r") as f:
        state = json.load(f)
    state.pop("sensor_alert", None)  # Remove sensor alert entry
    with open(state_file, "w") as f:
        json.dump(state, f)
    print("Cleared sensor alert state")
else:
    print("No state file found")
EOF

# Then test again
python3 test_alerts.py --high-temp --send-email
```

---

## Testing All Thresholds

### View Current Thresholds
```bash
python3 test_alerts.py --interactive
# Then select option 13
```

Output:
```
==============================================================
CURRENT ALERT THRESHOLDS
==============================================================
Temperature:  70°F - 85°F
CO2:          > 1500 ppm
Humidity:     35% - 85%
Moisture:     < 20%
==============================================================
```

### Test Each at Limits
```bash
# Temperature
python3 test_alerts.py --temp 86      # Above
python3 test_alerts.py --temp 69      # Below

# CO2
python3 test_alerts.py --co2 1501     # Above

# Humidity
python3 test_alerts.py --humidity 86  # Above
python3 test_alerts.py --humidity 34  # Below

# Moisture
python3 test_alerts.py --moisture 19  # Below
```

---

## Troubleshooting Tests

### "Error: Module not found"
```bash
# Make sure you're in the project directory
cd /path/to/PodCam
python3 test_alerts.py --help
```

### "Test email failed (may be deduped)"
```bash
# Clear the email state and try again
rm logs/email_send_state.json
python3 test_alerts.py --high-temp --send-email
```

### "ALERT_ENABLED is False"
```bash
# Check alerts_config.py
grep "ALERT_ENABLED" alerts_config.py

# If False, enable it
nano alerts_config.py
# Change: TEMP_ALERT_ENABLED = True

# Then test again
python3 test_alerts.py --high-temp
```

### "Email still not arriving"
```bash
# 1. Verify configuration
grep -E "DEFAULT_SENDER|DEFAULT_RECIPIENT" config.py

# 2. Check if email service working
python3 << 'EOF'
from email_notification import EmailNotifier
notifier = EmailNotifier()
print(f"Sender: {notifier.sender_email}")
print(f"SMTP: {notifier.smtp_server}:{notifier.smtp_port}")
EOF

# 3. Check email log
tail -20 /var/log/wncc_PodsInSpace/email.log
```

---

## Quick Reference Commands

```bash
# Test specific values
python3 test_alerts.py --temp 87.5
python3 test_alerts.py --co2 1700
python3 test_alerts.py --humidity 88
python3 test_alerts.py --moisture 15

# Test limits
python3 test_alerts.py --high-temp
python3 test_alerts.py --low-temp
python3 test_alerts.py --all

# Test with email
python3 test_alerts.py --temp 87 --send-email
python3 test_alerts.py --all --send-email

# Interactive menu
python3 test_alerts.py
python3 test_alerts.py -i

# View thresholds
python3 test_alerts.py -i
# Then select option 13

# Clear test state
rm logs/email_send_state.json

# View help
python3 test_alerts.py --help
```

---

## Integration with Production

### Testing Before Deployment
```bash
# 1. Test alert system locally
python3 test_alerts.py --all

# 2. Verify all 6 sensors work
# Expected: All show ✓ ALERT TRIGGERED

# 3. Test email
python3 test_alerts.py --high-temp --send-email

# 4. Check inbox
# Wait 5-10 seconds and check email

# 5. Ready to deploy
# No changes needed - just running tests
```

### On-the-fly Testing (Production)
```bash
# While service is running, test an alert
ssh your_pi
cd /path/to/PodCam
python3 test_alerts.py --temp 87

# Does it trigger? Good.
# Want to verify email works?
python3 test_alerts.py --temp 87 --send-email

# This will NOT interfere with running service
# Each test is independent
```

---

## Notes

- Tests do **NOT** interfere with the running service
- Tests show what **would** happen with that sensor value
- Email is only sent if you use `--send-email` flag
- All results logged to `sensors.log`
- Thresholds shown come from `alerts_config.py`
- Tests can run multiple times without issues
