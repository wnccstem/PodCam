# Quick Setup Guide: Temperature Alerts

## In 3 Steps

### Step 1: Enable Alerts in `alerts_config.py`
```python
TEMP_ALERT_ENABLED = True
TEMP_ALERT_HIGH = 85      # Alert if above 85°F
TEMP_ALERT_LOW = 70       # Alert if below 70°F
```

### Step 2: Restart the Service
```bash
sudo systemctl restart sensors-ts
```

### Step 3: Wait & Test
- Wait 10 minutes for the ThingSpeak cycle
- Check logs: `grep ALERT /var/log/wncc_PodsInSpace/sensors.log`
- Check email inbox for alerts

---

## What Happens

When a sensor reading is outside your thresholds at the 10-minute interval:

1. **Alert Detected** → Logged to system logs
2. **Email Sent** → To all configured recipients
3. **State Reset** → Ready for next violation

---

## Configuration Reference

All settings are in `alerts_config.py`:

| Setting | Default | Purpose |
|---------|---------|---------|
| `TEMP_ALERT_ENABLED` | `True` | Enable/disable temperature alerts |
| `TEMP_ALERT_HIGH` | `85` | Upper threshold (°F) |
| `TEMP_ALERT_LOW` | `70` | Lower threshold (°F) |
| `CO2_ALERT_ENABLED` | `False` | Enable/disable CO2 alerts |
| `CO2_ALERT_HIGH` | `1500` | CO2 threshold (ppm) |
| `HUMIDITY_ALERT_ENABLED` | `False` | Enable/disable humidity alerts |
| `HUMIDITY_ALERT_HIGH` | `85` | Upper humidity threshold (%) |
| `HUMIDITY_ALERT_LOW` | `35` | Lower humidity threshold (%) |
| `MOISTURE_ALERT_ENABLED` | `False` | Enable/disable soil moisture alerts |
| `MOISTURE_ALERT_LOW` | `20` | Lower moisture threshold (%) |
| `ALERT_DEDUP` | `True` | Prevent duplicate alerts |

---

## Adding New Alert Types

### 1. Add Configuration
In `alerts_config.py`:
```python
PUMP_ALERT_ENABLED = False
PUMP_PRESSURE_HIGH = 50  # psi
```

### 2. Add Check Method
In `alert_system.py` AlertSystem class:
```python
def check_pump(self, pressure_psi):
    if not PUMP_ALERT_ENABLED or pressure_psi is None:
        return False, None
    
    if pressure_psi > PUMP_PRESSURE_HIGH:
        alert_key = "pump_pressure"
        if not ALERT_DEDUP or not self.active_alerts.get(alert_key):
            msg = f"⚠️ HIGH PUMP PRESSURE: {pressure_psi} psi"
            self.active_alerts[alert_key] = True
            return True, msg
    else:
        self.active_alerts.pop("pump_pressure", None)
    
    return False, None
```

### 3. Update check_all()
In `alert_system.py` AlertSystem class:
```python
def check_all(self, ..., pressure_psi=None):
    # ... existing checks ...
    
    pump_alert, pump_msg = self.check_pump(pressure_psi)
    if pump_alert:
        messages.append(pump_msg)
    
    return len(messages) > 0, messages
```

### 4. Call in sensors_ts.py
```python
has_alerts, alert_messages = alert_system.check_all(
    temp_f=avg_temp,
    # ... other sensors ...
    pressure_psi=avg_pump_pressure  # Add new sensor
)
```

---

## Monitoring & Troubleshooting

### View Current Status
```bash
# See latest sensor readings
tail -20 /var/log/wncc_PodsInSpace/sensors.log | grep "Avg "

# See alerts sent
grep ALERT /var/log/wncc_PodsInSpace/sensors.log | tail -10

# See email status
grep -i "alert email" /var/log/wncc_PodsInSpace/sensors.log
```

### Enable/Disable Alerts
```bash
# Edit thresholds
nano alerts_config.py

# Restart to apply
sudo systemctl restart sensors-ts
```

### Check Deduplication State
```bash
# See what was recently sent
cat logs/email_send_state.json

# Manual dedup reset (for testing)
rm logs/email_send_state.json
```

### Test Without Waiting
```python
# In Python console
from alert_system import AlertSystem
alert_sys = AlertSystem()
has_alert, msg = alert_sys.check_temperature(87.5)
print(has_alert, msg)  # Verify logic works
```

---

## Architecture

```
Sensors (30s)
    ↓
Collect readings
    ↓
After 20 readings (10 min)
    ↓
Calculate averages
    ↓
Send to ThingSpeak
    ↓
Run Alert Checks
    ├─ check_temperature()
    ├─ check_co2()
    ├─ check_humidity()
    └─ check_moisture()
    ↓
If violations found:
    ├─ Log alert
    ├─ Format email
    ├─ Send email
    └─ Reset state
    ↓
Start next cycle
```

---

## Key Benefits

✅ **Modular** - Easy to add new sensor types  
✅ **Configurable** - All settings in one file  
✅ **Smart** - Built-in deduplication prevents alert spam  
✅ **Reliable** - Integrated with existing email system  
✅ **Efficient** - Checks at 10-minute averaging interval  
✅ **Documented** - Comprehensive guides included  

---

## Files Included

| File | Purpose |
|------|---------|
| `alerts_config.py` | Configure thresholds (edit this) |
| `alert_system.py` | Core alert logic (extend for new types) |
| `ALERT_SYSTEM.md` | Complete documentation |
| `ALERT_EXAMPLES.py` | Example configurations |
| `ALERT_WORKFLOW.py` | Testing & troubleshooting guide |
| `ALERT_SYSTEM_IMPLEMENTATION.md` | Implementation details |

---

## Support

For detailed information, see:
- **Setup Guide**: ALERT_SYSTEM.md
- **Examples**: ALERT_EXAMPLES.py
- **Testing**: ALERT_WORKFLOW.py
- **Adding New Types**: ALERT_SYSTEM.md → "Example: Adding a New Alert Type"

---

## Default Configuration

Currently enabled with these thresholds:
- Temperature: Alert if > 85°F or < 70°F

Enable other alerts as needed:
- CO2: Edit `alerts_config.py` and set `CO2_ALERT_ENABLED = True`
- Humidity: Edit `alerts_config.py` and set `HUMIDITY_ALERT_ENABLED = True`
- Moisture: Edit `alerts_config.py` and set `MOISTURE_ALERT_ENABLED = True`
