# Top 10 Alert Testing Commands

Copy & paste ready. Run from `/path/to/PodCam` directory.

## 1. Quick System Check (10 seconds)
```bash
python3 test_alerts.py --all
```
**What it does**: Tests all 6 alert types at their limits  
**Expected**: 6 lines with ✓ ALERT TRIGGERED  
**Tells you**: System is properly configured

---

## 2. Verify Email Works (30 seconds)
```bash
python3 test_alerts.py --all --send-email
```
**What it does**: Tests all alerts AND sends actual emails  
**Expected**: ✓ Test email sent successfully! (then check inbox)  
**Tells you**: Email system working, recipients set correctly

---

## 3. Test High Temperature (5 seconds)
```bash
python3 test_alerts.py --high-temp
```
**What it does**: Tests temperature above 85°F threshold  
**Expected**: ✓ ALERT TRIGGERED  
**Tells you**: High temp alert works

---

## 4. Test Low Temperature (5 seconds)
```bash
python3 test_alerts.py --low-temp
```
**What it does**: Tests temperature below 70°F threshold  
**Expected**: ✓ ALERT TRIGGERED  
**Tells you**: Low temp alert works

---

## 5. Test Custom Temperature (5 seconds)
```bash
python3 test_alerts.py --temp 87.5
```
**What it does**: Tests specific temperature value  
**Expected**: Shows if alert would trigger at 87.5°F  
**Tells you**: Exact threshold behavior

---

## 6. Test Custom Humidity (5 seconds)
```bash
python3 test_alerts.py --humidity 88
```
**What it does**: Tests humidity at specific value  
**Expected**: Shows alert status for 88%  
**Tells you**: Humidity alert working

---

## 7. Test Custom CO2 (5 seconds)
```bash
python3 test_alerts.py --co2 1600
```
**What it does**: Tests CO2 above 1500 ppm threshold  
**Expected**: ✓ ALERT TRIGGERED  
**Tells you**: CO2 alert working

---

## 8. Test Custom Moisture (5 seconds)
```bash
python3 test_alerts.py --moisture 15
```
**What it does**: Tests soil moisture below 20% threshold  
**Expected**: ✓ ALERT TRIGGERED  
**Tells you**: Moisture alert working

---

## 9. Interactive Menu (No commands to remember)
```bash
python3 test_alerts.py
```
**What it does**: Friendly menu with 13 testing options  
**Expected**: Menu appears, select option  
**Tells you**: Everything - just pick menu options

---

## 10. Help & Documentation
```bash
python3 test_alerts.py --help
```
**What it does**: Shows all available options  
**Expected**: Formatted help text  
**Tells you**: All testing possibilities

---

## One-Command Deployment Verification

Run this before deploying to production:

```bash
python3 test_alerts.py --all && python3 test_alerts.py --all --send-email && echo "✓ READY FOR PRODUCTION"
```

If you see that final echo message, everything works!

---

## Troubleshooting One-Liners

### Email deduped? Clear state:
```bash
rm logs/email_send_state.json && python3 test_alerts.py --high-temp --send-email
```

### Want to see help?
```bash
python3 test_alerts.py --help
```

### Want to see examples?
```bash
python3 ALERT_TESTING_EXAMPLES.py
```

### Want full guide?
```bash
cat TEST_ALERTS_QUICK_REF.md
```

---

## Expected Outputs Quick Guide

| Command | ✓ Success | ✗ Failure |
|---------|-----------|-----------|
| `--high-temp` | `✓ ALERT TRIGGERED` | `✗ No alert` |
| `--low-temp` | `✓ ALERT TRIGGERED` | `✗ No alert` |
| `--temp 72` | `✗ No alert` | `✓ ALERT TRIGGERED` |
| `--all` | 6× `✓ ALERT TRIGGERED` | Any `✗ No alert` |
| `--all --send-email` | `✓ Test email sent successfully!` | `✗ failed (may be deduped)` |

---

## How to Read Results

### Alert Triggered ✓
```
✓ ALERT TRIGGERED: 🌡️ HIGH TEMPERATURE: 87°F
```
→ System would send an alert at this value ✓

### No Alert ✗
```
✗ No alert (within safe range)
```
→ Value is safe, no alert needed ✓

### Email Sent ✓
```
✓ Test email sent successfully!
```
→ Email queued to recipients ✓
→ Check inbox (may take 5-10 sec)

### Email Failed/Deduped ✗
```
✗ Test email failed (may be deduped)
```
→ Clear state: `rm logs/email_send_state.json`
→ Try again

---

## Full Testing Sequence (2 minutes)

```bash
# Step 1: Basic test
python3 test_alerts.py --all
# Should see 6 ✓ ALERT TRIGGERED

# Step 2: Email test
python3 test_alerts.py --all --send-email
# Should see ✓ Test email sent successfully!

# Step 3: Verify email
# Check inbox for email from wnccrobotics@gmail.com

# Step 4: You're done!
echo "✓ Ready for production"
```

---

## Keep These Handy

### Most Used
```bash
python3 test_alerts.py --all              # Verify all working
python3 test_alerts.py --all --send-email # Verify email works
```

### Testing Config Changes
```bash
python3 test_alerts.py --temp 87          # Test new values
```

### Quick Limit Check
```bash
python3 test_alerts.py --high-temp        # Test > threshold
python3 test_alerts.py --low-temp         # Test < threshold
```

### Interactive
```bash
python3 test_alerts.py                    # Menu-driven
```

---

## Performance

- Single test: < 100ms ⚡
- All 6 sensors: < 500ms ⚡
- With email send: 2-5 seconds 📧
- Zero impact on running service ✓

---

**That's it! Copy any command, paste it, and test your alerts instantly.**
