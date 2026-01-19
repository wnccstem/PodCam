#!/usr/bin/env python3
"""
Grove Capacitive Moisture Sensor Test via I2C/SMBus

Reads analog values from the Grove Capacitive Moisture Sensor
connected to a Grove Base Hat ADC on Raspberry Pi via I2C.

Hardware Setup:
- Grove Moisture Sensor -> Grove Base Hat analog port (A0-A7)
- Grove Base Hat communicates via I2C (address 0x08)
- Uses same ADC reading method as pH sensor

ADC Configuration:
- I2C Address: 0x08 (Grove Base Hat ADC)
- 12-bit ADC (0-4095)
- Reference Voltage: 3.3V

01/17/26:   Calibrate with UNL Stevens Hydroprobe sensor
"""

import time
import sys
from typing import List, Optional

try:
    from smbus2 import i2c_msg, SMBus
except ImportError:
    print("Error: smbus2 library not found.")
    print("\nTo install smbus2 library:")
    print("  pip install smbus2")
    print("or")
    print("  sudo apt-get install python3-smbus")
    sys.exit(1)

# I2C Configuration
I2C_BUS = 1  # Use I2C bus 1 (default on Raspberry Pi)
ADC_I2C_ADDR = 0x08  # Grove Base Hat ADC I2C address
SENSOR_CHANNEL = 0  # Which analog port (0=A0, 1=A1, etc.)

# ADC Constants
ADC_MAX = 4095.0  # 12-bit ADC maximum value
V_REF = 3.3  # Reference voltage (3.3V on Raspberry Pi)

# Convert to percentage (adjust calibration values for your sensor)
# Calibration: measure sensor in completely dry and completely wet conditions
# The first measurement in the tuple is wet soil
# The last measurement in the tuple is dry soil
MOISTURE_CAL_POINTS = (395, 580)


class MoistureSensorReader:
    """Reader that uses smbus2 i2c_rdwr to query the Grove Base Hat ADC."""

    def __init__(self, addr: int = ADC_I2C_ADDR, busnum: int = I2C_BUS):
        """Initialize the ADC reader.

        Args:
            addr: I2C address of the Grove Base Hat ADC (default: 0x08)
            busnum: I2C bus number (default: 1)
        """
        self.addr = addr
        self.busnum = busnum

    def _read_raw_bytes(self, channel: int = 0) -> List[int]:
        """Read raw bytes from the ADC for the specified channel.

        Args:
            channel: ADC channel to read (0-7 for A0-A7)

        Returns:
            List of 4 bytes read from the ADC
        """
        # Open I2C bus connection
        with SMBus(self.busnum) as bus:
            # Send command to ADC: [0x30, channel, 0x00, 0x00]
            write = i2c_msg.write(self.addr, [0x30, channel, 0x00, 0x00])
            bus.i2c_rdwr(write)

            # Read 4 bytes of response
            read = i2c_msg.read(self.addr, 4)
            bus.i2c_rdwr(read)

            # Convert to list of integers
            data = list(read)

        return data

    def read_raw(self, channel: int = 0) -> dict:
        """Read raw ADC value and convert to voltage.

        Args:
            channel: ADC channel to read (0-7 for A0-A7)

        Returns:
            Dictionary with raw ADC value, voltage, and raw bytes
        """
        # Read raw bytes from ADC
        data = self._read_raw_bytes(channel)

        # Try different byte interpretation methods
        candidates = []
        if len(data) >= 2:
            # Low byte first
            v0 = (data[0] | (data[1] << 8)) & 0xFFFF
            candidates.append(("low_first", v0))
        if len(data) >= 4:
            # Middle pair
            v1 = (data[2] | (data[3] << 8)) & 0xFFFF
            candidates.append(("mid_pair", v1))
            # High byte first
            v2 = (data[0] << 8) | data[1]
            candidates.append(("high_first", v2))

        # Find valid ADC reading
        raw = None
        chosen_method = None
        for name, val in candidates:
            if 0 <= val <= ADC_MAX:
                raw = int(val)
                chosen_method = name
                break

        # Fallback if no valid reading found
        if raw is None:
            raw = ((data[0] | (data[1] << 8)) & 0x0FFF) if len(data) >= 2 else 0
            chosen_method = "fallback_mask12"

        # Convert raw ADC to voltage
        voltage_v = (raw / ADC_MAX) * V_REF

        return {
            "raw": raw,
            "voltage_v": voltage_v,
            "raw_bytes": data,
            "chosen_method": chosen_method,
        }

    def read_moisture(self, channel: int = 0) -> int:
        """Read moisture sensor raw ADC value.

        Args:
            channel: ADC channel to read (0-7 for A0-A7)

        Returns:
            Raw ADC value (0-4095)
        """
        r = self.read_raw(channel)
        return int(r["raw"])

    def read_moisture_averaged(
        self,
        channel: int = 0,
        samples: int = 10,
        delay: float = 0.05,
    ) -> Optional[int]:
        """Read averaged moisture sensor value.

        Args:
            channel: ADC channel to read
            samples: Number of readings to average
            delay: Delay between readings in seconds

        Returns:
            Averaged raw ADC value, or None if no valid readings
        """
        vals: List[int] = []
        for _ in range(samples):
            try:
                vals.append(self.read_moisture(channel))
            except Exception:
                pass
            time.sleep(delay)

        if not vals:
            raise RuntimeError("No valid readings collected")

        # Calculate average
        return int(sum(vals) / len(vals))


class MoistureSensor:
    """Simplified moisture sensor wrapper class."""

    def __init__(self, channel: int = SENSOR_CHANNEL):
        """Initialize the moisture sensor reader.

        Args:
            channel: ADC channel where sensor is connected (0-7)
        """
        self.channel = channel
        self.reader = MoistureSensorReader()

    def read_moisture(self) -> Optional[int]:
        """Read single moisture sensor value.

        Returns:
            Raw ADC value (0-4095), or None on error
        """
        try:
            return self.reader.read_moisture(channel=self.channel)
        except Exception as e:
            print(f"Error reading moisture sensor: {e}")
            return None

    def read_moisture_averaged(self, samples: int = 10) -> Optional[int]:
        """Read averaged moisture sensor value.

        Args:
            samples: Number of readings to average

        Returns:
            Averaged raw ADC value, or None on error
        """
        try:
            return self.reader.read_moisture_averaged(
                channel=self.channel, samples=samples
            )
        except Exception as e:
            print(f"Error reading averaged moisture: {e}")
            return None

    # -------------------------- READ SENSOR ----------------------------------- #
    def read_sensor(self) -> Optional[dict]:
        """Read moisture sensor and return calculated values.

        Returns:
            Dictionary with sensor data:
            {
                'raw': int,              # Raw ADC value (0-4095)
                'voltage': float,        # Voltage in volts
                'moisture_percent': float,  # Calculated moisture percentage
                'status': str            # Status description
            }
            Returns None on error.
        """
        try:
            # Read moisture sensor value
            sensor_value = self.read_moisture()

            if sensor_value is None:
                return None

            # Read voltage for reference
            raw_data = self.reader.read_raw(self.channel)
            voltage = raw_data["voltage_v"]

            # Clamp value to calibration range
            clamped_value = max(
                MOISTURE_CAL_POINTS[0],
                min(sensor_value, MOISTURE_CAL_POINTS[1]),
            )
            moisture_percent = (
                (clamped_value - MOISTURE_CAL_POINTS[0])
                / (MOISTURE_CAL_POINTS[1] - MOISTURE_CAL_POINTS[0])
            ) * 100

            # Interpret moisture level
            if moisture_percent < 20:
                status = "Very Dry 🌵"
            elif moisture_percent < 40:
                status = "Dry"
            elif moisture_percent < 60:
                status = "Moderate 💧"
            elif moisture_percent < 80:
                status = "Moist"
            else:
                status = "Very Wet 💦"

            return {
                "raw": sensor_value,
                "voltage": voltage,
                "moisture_percent": moisture_percent,
                "status": status,
            }

        except Exception as e:
            print(f"Error reading sensor: {e}")
            return None


def test_all_channels():
    """Test all ADC channels to find where the moisture sensor is connected."""
    print("Testing all ADC channels to find the moisture sensor...\n")

    try:
        reader = MoistureSensorReader()

        for channel in range(8):  # Test channels 0-7
            try:
                raw_data = reader.read_raw(channel)
                voltage = raw_data["voltage_v"]
                raw_adc = raw_data["raw"]
                print(
                    f"Channel {channel}: Raw ADC = {raw_adc:4d}, Voltage = {voltage:.3f}V"
                )

                # Moisture sensor typically reads between 0.5V - 3.0V
                if 0.5 < voltage < 3.0 and raw_adc > 100:
                    print(
                        f"  *** Channel {channel} might be your moisture sensor! ***"
                    )

            except Exception as e:
                print(f"Channel {channel}: Error - {e}")

    except Exception as e:
        print(f"Error initializing ADC reader: {e}")

    print(
        "\nIf you found a channel with active signal, update SENSOR_CHANNEL in the code."
    )


def main():
    """Main test function for moisture sensor."""
    print("Grove Capacitive Moisture Sensor Test")
    print(f"I2C Bus: {I2C_BUS}, ADC Address: 0x{ADC_I2C_ADDR:02X}")
    print(f"Reading from channel A{SENSOR_CHANNEL}")
    print("Press Ctrl+C to exit\n")

    try:
        # Initialize sensor
        sensor = MoistureSensor(channel=SENSOR_CHANNEL)

        # Test I2C connection
        try:
            test_reading = sensor.read_moisture()
            if test_reading is not None:
                print(
                    f"✓ Grove Base Hat ADC detected (initial reading: {test_reading})\n"
                )
            else:
                print("✗ Warning: Could not read from ADC\n")
        except Exception as e:
            print(f"✗ Warning: Cannot detect Grove Base Hat ADC: {e}\n")

        # Run continuous monitoring every 5 seconds
        while True:
            data = sensor.read_sensor()

            if data is not None:
                print(
                    f"Moisture Sensor Value: {data['raw']:4d} ({data['voltage']:.3f}V)"
                )
                print(
                    f"Moisture: {data['moisture_percent']:.1f}% - {data['status']}\n"
                )
            else:
                print("Failed to read sensor\n")

            time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n\nExiting program")
        sys.exit(0)


if __name__ == "__main__":
    # Uncomment the line below to test all channels first
    # test_all_channels()
    # print("\n=== NOW RUNNING MOISTURE SENSOR TEST ===\n")

    main()
