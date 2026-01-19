# Alert Testing Documentation Index

## Quick Start (Start Here!)

👉 **[TEST_ALERTS_QUICK_REF.md](TEST_ALERTS_QUICK_REF.md)** - One-page command reference
- Copy & paste ready commands
- Common scenarios in table format
- Expected outputs

## In-Depth Guides

📖 **[TESTING_ALERTS.md](TESTING_ALERTS.md)** - Complete testing guide
- Detailed scenarios with explanations
- Troubleshooting section
- Email state management
- Integration notes

📚 **[TESTING_SUMMARY.md](TESTING_SUMMARY.md)** - Feature overview
- What was added
- Key benefits
- File structure
- Integration points

## Examples & Real-World Usage

💡 **[ALERT_TESTING_EXAMPLES.py](ALERT_TESTING_EXAMPLES.py)** - Runnable examples
- 10 real-world testing scenarios
- Performance notes
- Pro tips & tricks
- Can be executed directly: `python3 ALERT_TESTING_EXAMPLES.py`

## The Testing Tool

🧪 **[test_alerts.py](test_alerts.py)** - Main testing utility
- Interactive menu mode: `python3 test_alerts.py`
- Command-line mode: `python3 test_alerts.py --help`
- Tests all sensor types
- Optional email sending

---

## Fastest Start (30 seconds)

### Test High Temp Alert
```bash
python3 test_alerts.py --high-temp
```
✓ See `ALERT TRIGGERED` → System works!

### Test All Limits
```bash
python3 test_alerts.py --all
```
✓ See 6 `ALERT TRIGGERED` → All configured!

### Test Email
```bash
python3 test_alerts.py --all --send-email
# Check inbox in 10 seconds
```
✓ See email → Delivery works!

---

## Common Commands

```bash
# Test specific values
python3 test_alerts.py --temp 87       # Test temperature
python3 test_alerts.py --humidity 88   # Test humidity
python3 test_alerts.py --co2 1600      # Test CO2
python3 test_alerts.py --moisture 15   # Test moisture

# Test quick limits
python3 test_alerts.py --high-temp     # Test above high limit
python3 test_alerts.py --low-temp      # Test below low limit

# Test all at once
python3 test_alerts.py --all           # All sensors at limits
python3 test_alerts.py --all --send-email  # With email

# Interactive mode
python3 test_alerts.py                 # Menu-driven interface
python3 test_alerts.py -i              # Same as above

# Utilities
python3 test_alerts.py --help          # Show all options
python3 ALERT_TESTING_EXAMPLES.py      # Show example scenarios
```

---

## What You Can Test

✅ **Upper Limits**
- High temperature (above 85°F)
- High CO2 (above 1500 ppm)
- High humidity (above 85%)

✅ **Lower Limits**
- Low temperature (below 70°F)
- Low humidity (below 35%)
- Low moisture (below 20%)

✅ **Custom Values**
- Any temperature, CO2, humidity, or moisture value
- Verify exact threshold boundaries
- Test your specific room conditions

✅ **Email Sending**
- Verify emails actually reach recipients
- Check email content and formatting
- Test email system independently

---

## Testing Workflows

### Initial Setup
```bash
python3 test_alerts.py --all
# All 6 sensors should show ✓ ALERT TRIGGERED
```

### Verify Email Works
```bash
python3 test_alerts.py --all --send-email
# Should say ✓ Test email sent successfully!
# Check inbox within 10 seconds
```

### After Config Changes
```bash
# Edit alerts_config.py
nano alerts_config.py

# Test changes immediately
python3 test_alerts.py --all

# If good, restart service
sudo systemctl restart sensors-ts
```

### Before Production
```bash
# Run full suite
python3 test_alerts.py --all           # ✓ All trigger
python3 test_alerts.py --all --send-email  # ✓ Email works
# Check inbox                          # ✓ Email received
```

---

## Expected Outputs

### ✓ Success
```
✓ ALERT TRIGGERED: 🌡️ HIGH TEMPERATURE: 87°F (threshold: 85°F)
```
Alert will be sent at this value.

### ✗ Safe Value
```
✗ No alert (within safe range)
```
No alert needed - value is safe.

### 📧 Email Sent
```
✓ Test email sent successfully!
```
Email queued to recipients.

### Deduped
```
✗ Test email failed (may be deduped)
```
Fix: `rm logs/email_send_state.json`

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tests show no alerts | Check `TEMP_ALERT_ENABLED = True` in config |
| Email not sending | Run `rm logs/email_send_state.json` then retry |
| Wrong thresholds shown | Verify `alerts_config.py` values |
| Module not found | Make sure you're in `/path/to/PodCam` directory |

---

## File Organization

```
Testing Documentation:
├── TEST_ALERTS_QUICK_REF.md          ← Quick command reference
├── TESTING_ALERTS.md                 ← Detailed guide
├── TESTING_SUMMARY.md                ← Feature overview
└── ALERT_TESTING_EXAMPLES.py         ← Real-world examples

Testing Tool:
└── test_alerts.py                    ← Main utility

Related Configuration:
├── alerts_config.py                  ← Thresholds (used by tests)
├── alert_system.py                   ← Alert logic (tested by tool)
└── sensors_ts.py                     ← Production service
```

---

## Key Points

📝 **No Configuration Needed** - Tests use existing settings  
⚡ **Instant Results** - No waiting for 10-minute sensor cycles  
🎯 **No Service Impact** - Tests run independently  
📊 **Multiple Runs** - Test as many times as needed  
🔍 **Complete Logging** - All results logged automatically  
✉️ **Email Testing** - Verify actual email delivery  

---

## Next Steps

1. **Read**: [TEST_ALERTS_QUICK_REF.md](TEST_ALERTS_QUICK_REF.md)
2. **Run**: `python3 test_alerts.py --all`
3. **Verify**: Check that all 6 sensors trigger alerts
4. **Email**: `python3 test_alerts.py --all --send-email`
5. **Ready**: Production deployment

---

## Support Resources

- **Quick Commands**: TEST_ALERTS_QUICK_REF.md
- **Detailed Guide**: TESTING_ALERTS.md
- **Real Examples**: ALERT_TESTING_EXAMPLES.py
- **Built-in Help**: `python3 test_alerts.py --help`

---

## Testing Checklist

- [ ] Run `python3 test_alerts.py --all` → All 6 show ✓
- [ ] Run `python3 test_alerts.py --all --send-email` → Shows ✓
- [ ] Check email inbox → Email received
- [ ] Verify email content → Contains alert details
- [ ] Test custom value → `python3 test_alerts.py --temp 87`
- [ ] Ready for production → All above passed

---

## One Command to Verify Everything

```bash
python3 test_alerts.py --all && echo "✓ All alerts working!"
```

If you see ✓ 6 times and final message, you're ready!
