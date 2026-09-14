from pathlib import Path

import pandas as pd


# ============================================================
# SETTINGS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "BME680_2026-08-01_18-44-48.csv"
OUTPUT_FILE = DATA_DIR / "temperature_event_0_10.csv"

TIME_COLUMN = "elapsed_seconds"
VALUE_COLUMN = "temperature_c"

THRESHOLD = 0.10


# ============================================================
# LOAD AND VALIDATE DATA
# ============================================================
if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found:\n{INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE)

required_columns = {
    "session_id",
    "timestamp",
    "elapsed_seconds",
    "temperature_c",
    "pressure_hpa",
    "humidity_percent",
    "altitude_m",
    "gas_resistance_kohm",
}

missing_columns = required_columns.difference(df.columns)

if missing_columns:
    raise ValueError(
        f"Missing required columns: {sorted(missing_columns)}"
    )

numeric_columns = [
    "elapsed_seconds",
    "temperature_c",
    "pressure_hpa",
    "humidity_percent",
    "altitude_m",
    "gas_resistance_kohm",
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce",
    )

df = (
    df.dropna(
        subset=[
            TIME_COLUMN,
            VALUE_COLUMN,
        ]
    )
    .sort_values(
        TIME_COLUMN,
        kind="stable",
    )
    .reset_index(drop=True)
)

if df.empty:
    raise ValueError("Input dataset is empty.")

if not df[TIME_COLUMN].is_monotonic_increasing:
    raise ValueError(
        "elapsed_seconds is not monotonically increasing."
    )

if df[TIME_COLUMN].duplicated().any():
    raise ValueError(
        "Duplicate elapsed_seconds values were found."
    )


# ============================================================
# EVENT-DRIVEN TRANSMISSION
# ============================================================
event_rows = []

first_row = df.iloc[0]

last_sent_value = float(
    first_row[VALUE_COLUMN]
)

last_sent_time = float(
    first_row[TIME_COLUMN]
)

event_rows.append({
    "transmission_number": 1,
    "session_id": first_row["session_id"],
    "timestamp": first_row["timestamp"],
    "elapsed_seconds": last_sent_time,
    "time_since_previous_transmission": None,
    "temperature_c": float(
        first_row["temperature_c"]
    ),
    "absolute_temperature_change": None,
    "pressure_hpa": float(
        first_row["pressure_hpa"]
    ),
    "humidity_percent": float(
        first_row["humidity_percent"]
    ),
    "altitude_m": float(
        first_row["altitude_m"]
    ),
    "gas_resistance_kohm": float(
        first_row["gas_resistance_kohm"]
    ),
    "source_row_index": 0,
})


for index in range(1, len(df)):
    current_row = df.iloc[index]

    current_value = float(
        current_row[VALUE_COLUMN]
    )

    current_time = float(
        current_row[TIME_COLUMN]
    )

    absolute_change = abs(
        current_value - last_sent_value
    )

    if absolute_change >= THRESHOLD:
        time_since_previous = (
            current_time - last_sent_time
        )

        event_rows.append({
            "transmission_number":
                len(event_rows) + 1,

            "session_id":
                current_row["session_id"],

            "timestamp":
                current_row["timestamp"],

            "elapsed_seconds":
                current_time,

            "time_since_previous_transmission":
                round(
                    time_since_previous,
                    3,
                ),

            "temperature_c":
                float(
                    current_row["temperature_c"]
                ),

            "absolute_temperature_change":
                round(
                    absolute_change,
                    4,
                ),

            "pressure_hpa":
                float(
                    current_row["pressure_hpa"]
                ),

            "humidity_percent":
                float(
                    current_row["humidity_percent"]
                ),

            "altitude_m":
                float(
                    current_row["altitude_m"]
                ),

            "gas_resistance_kohm":
                float(
                    current_row[
                        "gas_resistance_kohm"
                    ]
                ),

            "source_row_index":
                int(index),
        })

        last_sent_value = current_value
        last_sent_time = current_time


event_df = pd.DataFrame(event_rows)


# ============================================================
# VALIDATION
# ============================================================
valid_changes = (
    event_df["absolute_temperature_change"]
    .dropna()
)

invalid_transmissions = event_df[
    event_df["absolute_temperature_change"].notna()
    & (
        event_df["absolute_temperature_change"]
        < THRESHOLD
    )
]

if not invalid_transmissions.empty:
    raise ValueError(
        "Found event transmissions below the threshold."
    )

if not event_df[
    "source_row_index"
].is_monotonic_increasing:
    raise ValueError(
        "Source row indices are not increasing."
    )

if not event_df[
    "elapsed_seconds"
].is_monotonic_increasing:
    raise ValueError(
        "Transmission times are not increasing."
    )


# ============================================================
# SAVE RESULTS
# ============================================================
event_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# PRINT VERIFICATION RESULTS
# ============================================================
print("=== EVENT-DRIVEN VALIDATION ===")

print(f"Raw measurements: {len(df)}")
print(f"Threshold: {THRESHOLD:.2f} °C")

print(
    f"Generated transmissions: "
    f"{len(event_df)}"
)

print(
    f"Communication load: "
    f"{len(event_df) / len(df) * 100:.3f}%"
)

print(
    f"Reduction compared with raw data: "
    f"{(1 - len(event_df) / len(df)) * 100:.3f}%"
)

if not valid_changes.empty:
    print(
        f"Minimum transmitted temperature change: "
        f"{valid_changes.min():.4f} °C"
    )

    print(
        f"Maximum transmitted temperature change: "
        f"{valid_changes.max():.4f} °C"
    )

valid_intervals = (
    event_df[
        "time_since_previous_transmission"
    ]
    .dropna()
)

if not valid_intervals.empty:
    print(
        f"Minimum time between transmissions: "
        f"{valid_intervals.min():.3f} s"
    )

    print(
        f"Maximum time between transmissions: "
        f"{valid_intervals.max():.3f} s"
    )

    print(
        f"Mean time between transmissions: "
        f"{valid_intervals.mean():.3f} s"
    )

print(
    f"Invalid transmissions below threshold: "
    f"{len(invalid_transmissions)}"
)

display_columns = [
    "transmission_number",
    "elapsed_seconds",
    "time_since_previous_transmission",
    "temperature_c",
    "absolute_temperature_change",
    "source_row_index",
]

print("\n=== FIRST 15 TRANSMISSIONS ===")
print(
    event_df[
        display_columns
    ]
    .head(15)
    .to_string(index=False)
)

print("\n=== LAST 15 TRANSMISSIONS ===")
print(
    event_df[
        display_columns
    ]
    .tail(15)
    .to_string(index=False)
)

print(
    f"\nSaved to:\n{OUTPUT_FILE}"
)