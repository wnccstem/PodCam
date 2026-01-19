# Test Alerts - Quick Command Reference

## Fastest Tests (Copy & Paste)

### Test High Temperature Alert
```bash
python3 test_alerts.py --high-temp
```
Expected output: `✓ ALERT TRIGGERED`

### Test Low Temperature Alert
```bash
python3 test_alerts.py --low-temp
```
Expected output: `✓ ALERT TRIGGERED`

### Test All Sensors at Limits
```bash
python3 test_alerts.py --all
```
Expected output: 6 lines, all with `✓ ALERT TRIGGERED`

### Test & Send Email
```bash
python3 test_alerts.py --all --send-email
```
Check inbox for "PodsInSpace Sensor Threshold Alert"

---

## Custom Value Tests

```bash
# Temperature (in °F)
python3 test_alerts.py --temp 87
python3 test_alerts.py --temp 68

# CO2 (in ppm)
python3 test_alerts.py --co2 1600

# Humidity (in %)
python3 test_alerts.py --humidity 88

# Moisture (in %)
python3 test_alerts.py --moisture 15
```

---

## Interactive Menu

```bash
python3 test_alerts.py
```

Then choose from menu:
- Option 1-10: Test individual sensors
- Option 11-12: Test all sensors
- Option 13: View current thresholds

---

## Email Testing

```bash
# Test alert AND verify email sends
python3 test_alerts.py --high-temp --send-email

# Test all sensors AND send emails
python3 test_alerts.py --all --send-email

# Clear email state (if deduped)
rm logs/email_send_state.json
python3 test_alerts.py --high-temp --send-email
```

---

## One-Liner Tests

```bash
# Quick sequence to verify everything
echo "Testing high temp..."; python3 test_alerts.py --high-temp && \
echo "Testing low temp..."; python3 test_alerts.py --low-temp && \
echo "Testing all limits..."; python3 test_alerts.py --all && \
echo "All tests passed!"
```

---

## Help & Info

```bash
# Show all options
python3 test_alerts.py --help

# View current thresholds
python3 test_alerts.py --interactive
# Select option 13
```

---

## Common Scenarios

| What to Test | Command |
|---|---|
| Verify high temp works | `python3 test_alerts.py --high-temp` |
| Verify low temp works | `python3 test_alerts.py --low-temp` |
| Verify all alerts work | `python3 test_alerts.py --all` |
| Test email sends | `python3 test_alerts.py --high-temp --send-email` |
| Custom temperature | `python3 test_alerts.py --temp 75.5` |
| Custom CO2 | `python3 test_alerts.py --co2 1550` |
| Custom humidity | `python3 test_alerts.py --humidity 80` |
| Custom moisture | `python3 test_alerts.py --moisture 25` |
| Reset email state | `rm logs/email_send_state.json` |
| Interactive mode | `python3 test_alerts.py` or `python3 test_alerts.py -i` |

---

## Expected Outputs

### ✓ Alert Triggered (Test Passed)
```
✓ ALERT TRIGGERED: 🌡️ HIGH TEMPERATURE: 87°F (threshold: 85°F)
```
→ System detected violation correctly

### ✗ No Alert (Safe Value)
```
✗ No alert (within safe range)
```
→ Value is safe, alert not needed

### 📧 Email Sent
```
📧 Sending test email...
✓ Test email sent successfully!
```
→ Email queued to recipients

### ✗ Email Deduped
```
✗ Test email failed (may be deduped)
```
→ Fix: `rm logs/email_send_state.json`

---

## Before Production

Run this sequence:
```bash
# 1. Test all alert types
python3 test_alerts.py --all

# 2. Verify email works
python3 test_alerts.py --all --send-email

# 3. Check email received
# Look in inbox (wait 5-10 sec)

# 4. Ready to deploy
# Service will handle real sensor data
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Module not found" | `cd /path/to/PodCam` first |
| Email not deduped/blocked | `rm logs/email_send_state.json` |
| Alert not triggering | Check `alerts_config.py` has `_ENABLED = True` |
| "No alert (within safe range)" | Value is between thresholds, try higher/lower |
| Email not arriving | Check `config.py` for recipient emails |

---

## Key Points

✅ Tests don't interfere with running service  
✅ Multiple tests can be run back-to-back  
✅ Email only sent with `--send-email` flag  
✅ All test results logged automatically  
✅ Can test any custom value instantly  
✅ No waiting for sensor data
