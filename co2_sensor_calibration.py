# pip install adafruit-circuitpython-scd4x
import time
import board
import adafruit_scd4x

i2c = board.I2C()
scd4x = adafruit_scd4x.SCD4X(i2c)

TEMPERATURE_OFFSET = -0.01


print("Serial number:", [hex(i) for i in scd4x.serial_number])


scd4x.start_periodic_measurement()
print("Waiting for first measurement....")

try:
    while True:
        if scd4x.data_ready:
            temp_c = scd4x.temperature + TEMPERATURE_OFFSET

            temp_f = temp_c * 9 / 5 + 32
            print(f"     CO2: {scd4x.CO2} ppm")
            print(f"  Temp F: {temp_f:0.1f} °F")
            print(f"  Temp C: {temp_c:0.1f} °C")
            print(f"Humidity: {scd4x.relative_humidity:0.1f} %")
            print()
        time.sleep(1)
except KeyboardInterrupt:
    print("\nMeasurement stopped by user.")
