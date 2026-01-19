# Manual Alert Testing - Feature Summary

## What Was Added

A comprehensive testing utility (`test_alerts.py`) that lets you manually test alert triggers at any sensor value without waiting for actual readings to exceed thresholds.

## Key Features

✅ **Test Upper & Lower Limits** - Trigger alerts at high/low thresholds  
✅ **Custom Values** - Test any sensor value instantly  
✅ **Email Verification** - Test actual email sending  
✅ **Interactive Menu** - User-friendly testing interface  
✅ **Command-Line Mode** - Quick one-liners for automation  
✅ **All Sensors** - Test temperature, CO2, humidity, moisture  
✅ **No Service Disruption** - Tests run independently  
✅ **Logging** - All tests recorded automatically  

## Basic Usage

### Test High Temperature (Above Threshold)
```bash
python3 test_alerts.py --high-temp
```

### Test Low Temperature (Below Threshold)
```bash
python3 test_alerts.py --low-temp
```

### Test All Sensors at Limits
```bash
python3 test_alerts.py --all
```

### Test & Verify Email Works
```bash
python3 test_alerts.py --all --send-email
```

### Interactive Menu
```bash
python3 test_alerts.py
```

## Common Testing Scenarios

### Scenario 1: Verify System Works
```bash
# Test all alert types with one command
python3 test_alerts.py --all

# You should see:
# ✓ ALERT TRIGGERED (6 times for each sensor type)
```

### Scenario 2: Verify Email Delivery
```bash
# Test that emails actually get sent
python3 test_alerts.py --all --send-email

# Watch for:
# ✓ Test email sent successfully!

# Then check inbox for email from wnccrobotics@gmail.com
```

### Scenario 3: Test Custom Values
```bash
# What if your room is at 75°F?
python3 test_alerts.py --temp 75

# Should show: ✗ No alert (within safe range)
# Good, that's safe.

# Now test at limit
python3 test_alerts.py --temp 86

# Should show: ✓ ALERT TRIGGERED
```

### Scenario 4: Test Before Deployment
```bash
# Quick pre-deployment check:
python3 test_alerts.py --all

# All 6 alerts should trigger
# If not, something is misconfigured
```

## Command Line Options

```
--high-temp              Test high temperature alert
--low-temp               Test low temperature alert
--temp <value>           Test specific temperature (°F)
--co2 <value>           Test specific CO2 level (ppm)
--humidity <value>      Test specific humidity (%)
--moisture <value>      Test specific moisture (%)
--all                   Test all sensors at limits
--send-email            Send actual email (if alert triggered)
-i, --interactive       Interactive menu mode
--help                  Show all options
```

## File Structure

```
PodCam/
├── test_alerts.py                    ← NEW: Testing utility
├── alerts_config.py                  ← Uses this for thresholds
├── alert_system.py                   ← Tests this module
├── TESTING_ALERTS.md                 ← Detailed guide
├── TEST_ALERTS_QUICK_REF.md         ← Quick reference
└── sensors_ts.py                     ← No changes needed
```

## Quick Reference

| Task | Command |
|------|---------|
| Test high temp | `python3 test_alerts.py --high-temp` |
| Test low temp | `python3 test_alerts.py --low-temp` |
| Test all limits | `python3 test_alerts.py --all` |
| Test with email | `python3 test_alerts.py --all --send-email` |
| Custom temp | `python3 test_alerts.py --temp 87.5` |
| Custom CO2 | `python3 test_alerts.py --co2 1600` |
| Interactive | `python3 test_alerts.py` |
| Help | `python3 test_alerts.py --help` |

## Example Outputs

### Alert Triggered (✓)
```
==============================================================
Testing Temperature Alert: 87°F
==============================================================
Configured thresholds: 70°F - 85°F
✓ ALERT TRIGGERED: 🌡️ HIGH TEMPERATURE: 87°F (threshold: 85°F)
```

### No Alert (✗)
```
==============================================================
Testing Temperature Alert: 72°F
==============================================================
Configured thresholds: 70°F - 85°F
✗ No alert (within safe range)
```

### Email Sent
```
📧 Sending test email...
✓ Test email sent successfully!
```

## Testing Workflow

### Initial Setup
1. Run: `python3 test_alerts.py --all`
2. Should see 6 `✓ ALERT TRIGGERED` lines
3. If any show `✗`, check `alerts_config.py`

### Email Verification
1. Run: `python3 test_alerts.py --all --send-email`
2. Look for: `✓ Test email sent successfully!`
3. Check inbox within 10 seconds
4. Verify email contains all alert details

### Before Production
1. Test all limits: `python3 test_alerts.py --all`
2. Test email: `python3 test_alerts.py --high-temp --send-email`
3. Verify email received
4. Ready for deployment

## Integration Points

The testing utility works with your existing system:
- **Reads from** `alerts_config.py` (current thresholds)
- **Uses** `alert_system.py` (same logic as production)
- **Uses** `email_notification.py` (same email system)
- **Logs to** system logs (same as production)
- **Does NOT** interfere with running service

## Benefits

✅ **Instant Testing** - No waiting 10 minutes for sensor cycle  
✅ **Verify Limits** - Confirm thresholds are correct  
✅ **Email Testing** - Verify recipients get emails  
✅ **Pre-Deployment** - Catch issues before production  
✅ **Troubleshooting** - Quickly test configuration changes  
✅ **Repeatable** - Run tests any time, any number of times  

## Advanced Usage

### Clear Email State (for re-testing)
```bash
rm logs/email_send_state.json
python3 test_alerts.py --high-temp --send-email
```

### Test Sequence
```bash
# Run multiple tests in sequence
for temp in 68 72 75 85 87; do
  echo "Testing $temp°F..."
  python3 test_alerts.py --temp $temp
done
```

### Interactive Testing
```bash
# Menu-driven approach
python3 test_alerts.py

# Then select from menu:
# 1 = Test high temp
# 2 = Test low temp
# 3 = Custom value
# etc.
```

## Documentation Provided

1. **TESTING_ALERTS.md** - Complete testing guide with examples
2. **TEST_ALERTS_QUICK_REF.md** - Quick reference card
3. **test_alerts.py** - Testing utility with full docstrings
4. Built-in help: `python3 test_alerts.py --help`

## No Configuration Needed

The test utility automatically:
- Reads current thresholds from `alerts_config.py`
- Uses same email system as production
- Logs results automatically
- Works without any additional setup

Just run and test!
