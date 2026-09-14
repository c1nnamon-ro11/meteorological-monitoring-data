import csv
import time
from datetime import datetime
from pathlib import Path

import board
import adafruit_bme680


# ============================================================
# SETTINGS
# ============================================================
BME680_ADDRESS = 0x77
READ_INTERVAL_SECONDS = 0.5

MIN_TEMP = -40.0
MAX_TEMP = 85.0

MIN_PRESSURE = 300.0
MAX_PRESSURE = 1100.0

MIN_HUMIDITY = 0.0
MAX_HUMIDITY = 100.0

MIN_ALTITUDE = -500.0
MAX_ALTITUDE = 9000.0

MIN_GAS_RESISTANCE = 0.0

MAX_IDENTICAL_READINGS = 20

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)

session_started = datetime.now()
session_id = session_started.strftime("BME680_%Y-%m-%d_%H-%M-%S")


output_file = DATA_DIR / f"{session_id}.csv"


# ============================================================
# VALIDATION
# ============================================================
def values_are_valid(
    temperature: float,
    pressure: float,
    humidity: float,
    altitude: float,
    gas_resistance: float,
) -> bool:
    return (
        MIN_TEMP <= temperature <= MAX_TEMP
        and MIN_PRESSURE <= pressure <= MAX_PRESSURE
        and MIN_HUMIDITY <= humidity <= MAX_HUMIDITY
        and MIN_ALTITUDE <= altitude <= MAX_ALTITUDE
        and gas_resistance >= MIN_GAS_RESISTANCE
    )


def create_csv(filename: Path) -> None:
    # "x" prevents accidental overwriting or appending to an old experiment.
    with filename.open(mode="x", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "session_id",
            "timestamp",
            "elapsed_seconds",
            "temperature_c",
            "pressure_hpa",
            "humidity_percent",
            "altitude_m",
            "gas_resistance_kohm",
        ])


# ============================================================
# SENSOR INITIALIZATION
# ============================================================
i2c = board.I2C()

try:
    sensor = adafruit_bme680.Adafruit_BME680_I2C(
        i2c,
        address=BME680_ADDRESS,
        refresh_rate=10,
    )
except (ValueError, OSError) as error:
    raise SystemExit(
        f"BME680 was not detected at address "
        f"0x{BME680_ADDRESS:02X}: {error}"
    )

sensor.sea_level_pressure = 1013.25

create_csv(output_file)

print("BME680 detected.")
print(f"Session: {session_id}")
print(f"Output file: {output_file.resolve()}")
print(f"Sampling interval: {READ_INTERVAL_SECONDS} s")
print("Press Ctrl+C to stop.")

# monotonic() is not affected by system-clock corrections.
start_monotonic = time.monotonic()
next_read_time = start_monotonic

last_values = None
identical_reading_count = 0
successful_readings = 0
failed_readings = 0


# ============================================================
# ACQUISITION LOOP
# ============================================================
try:
    while True:
        next_read_time += READ_INTERVAL_SECONDS

        try:
            temperature = round(float(sensor.temperature), 2)
            pressure = round(float(sensor.pressure), 2)
            humidity = round(float(sensor.relative_humidity), 2)
            altitude = round(float(sensor.altitude), 2)
            gas_resistance = round(float(sensor.gas) / 1000.0, 2)

        except (OSError, RuntimeError) as error:
            failed_readings += 1
            print(f"Sensor read failed: {error}")

            sleep_time = next_read_time - time.monotonic()
            if sleep_time > 0:
                time.sleep(sleep_time)

            continue

        if not values_are_valid(
            temperature,
            pressure,
            humidity,
            altitude,
            gas_resistance,
        ):
            failed_readings += 1

            print(
                "Reading rejected: "
                f"T={temperature} °C, "
                f"P={pressure} hPa, "
                f"RH={humidity} %, "
                f"Alt={altitude} m, "
                f"Gas={gas_resistance} kΩ"
            )

            sleep_time = next_read_time - time.monotonic()
            if sleep_time > 0:
                time.sleep(sleep_time)

            continue

        current_values = (
            temperature,
            pressure,
            humidity,
            altitude,
            gas_resistance,
        )

        if current_values == last_values:
            identical_reading_count += 1
        else:
            identical_reading_count = 0

        last_values = current_values

        if identical_reading_count >= MAX_IDENTICAL_READINGS:
            print(
                "Warning: multiple identical readings detected. "
                "The reading is still recorded."
            )

        timestamp = datetime.now().isoformat(
            sep=" ",
            timespec="milliseconds",
        )

        elapsed_seconds = round(
            time.monotonic() - start_monotonic,
            3,
        )

        with output_file.open(
            mode="a",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)

            writer.writerow([
                session_id,
                timestamp,
                elapsed_seconds,
                temperature,
                pressure,
                humidity,
                altitude,
                gas_resistance,
            ])

            file.flush()

        successful_readings += 1

        print(
            f"[{timestamp}] "
            f"t={elapsed_seconds:.3f} s | "
            f"T={temperature:.2f} °C | "
            f"P={pressure:.2f} hPa | "
            f"RH={humidity:.2f} % | "
            f"Alt={altitude:.2f} m | "
            f"Gas={gas_resistance:.2f} kΩ"
        )

        sleep_time = next_read_time - time.monotonic()

        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            print(
                f"Warning: acquisition loop exceeded the "
                f"{READ_INTERVAL_SECONDS} s interval by "
                f"{abs(sleep_time):.3f} s."
            )

except KeyboardInterrupt:
    duration = time.monotonic() - start_monotonic

    print("\nData collection stopped.")
    print(f"Duration: {duration:.2f} s")
    print(f"Successful readings: {successful_readings}")
    print(f"Failed readings: {failed_readings}")
    print(f"Saved to: {output_file.resolve()}")