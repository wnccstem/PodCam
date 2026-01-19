#!/usr/bin/env python3

"""



01-17-26:   Add 2 minute warmup period with 10 readings

"""
import time

# pip install adafruit-circuitpython-scd4x requests
import board
import adafruit_scd4x
import time

TEMPERATURE_OFFSET = -0.01


class CO2Sensor:
    """Reader for SCD4x CO2 sensor via I2C."""

    def __init__(self):
        self.co2 = None
        self.temp_c = None
        self.temp_f = None
        self.humidity = None
        self.i2c = board.I2C()
        self.scd4x = adafruit_scd4x.SCD4X(self.i2c)
        self.scd4x.start_periodic_measurement()
        time.sleep(2)
        self._perform_initial_calibration()

    def _perform_initial_calibration(
        self, required_readings: int = 20, window_seconds: int = 120
    ) -> None:
        """Collect initial readings to allow the sensor to settle.

        Takes up to ``window_seconds`` to gather ``required_readings`` samples
        and updates the cached values with the last sample collected.
        """
        deadline = time.monotonic() + window_seconds
        collected = 0
        while collected < required_readings and time.monotonic() < deadline:
            if self.scd4x.data_ready:
                self.co2 = self.scd4x.CO2
                self.temp_c = self.scd4x.temperature + TEMPERATURE_OFFSET
                self.temp_f = self.temp_c * 9 / 5 + 32
                self.humidity = self.scd4x.relative_humidity
                collected += 1
            time.sleep(0.5)

    def read_sensors(self):
        """Read CO2, temperature (C, F), and humidity from the sensor.
        Returns tuple of (co2, temp_f, humidity) or (None, None, None) if not ready."""
        if self.scd4x.data_ready:
            self.co2 = self.scd4x.CO2
            self.temp_c = self.scd4x.temperature
            self.temp_c += TEMPERATURE_OFFSET
            self.temp_f = self.temp_c * 9 / 5 + 32
            self.humidity = self.scd4x.relative_humidity
            return self.co2, self.temp_f, self.humidity
        else:
            # Return None values when sensor data is not ready (don't return stale values)
            return None, None, None
def main():
    print("SCD4x CO2 Sensor Test")
    print("Press Ctrl+C to exit\n")
    sensor = CO2Sensor()
    try:
        while True:
            time.sleep(2)
            co2, temp_f, humidity = sensor.read_sensors()
            if co2 is not None:
                print(
                    f"CO2: {co2} ppm, Temp: {temp_f:.1f} F, Humidity: {humidity:.1f}%"
                )
            else:
                print("Waiting for sensor data...")
    except KeyboardInterrupt:
        print("\nExiting on user request.")


if __name__ == "__main__":
    main()
