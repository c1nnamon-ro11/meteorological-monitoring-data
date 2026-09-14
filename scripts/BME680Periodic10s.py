from pathlib import Path

import pandas as pd


# ============================================================
# SETTINGS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "BME680_2026-08-01_18-44-48.csv"
OUTPUT_FILE = DATA_DIR / "temperature_periodic_10s.csv"

TIME_COLUMN = "elapsed_seconds"
VALUE_COLUMN = "temperature_c"

INTERVAL_SECONDS = 10


# ============================================================
# LOAD AND VALIDATE DATA
# ============================================================
if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found:\n{INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE)

required_columns = {
    TIME_COLUMN,
    VALUE_COLUMN,
}

missing_columns = required_columns.difference(df.columns)

if missing_columns:
    raise ValueError(
        f"Missing required columns: {sorted(missing_columns)}"
    )

df[TIME_COLUMN] = pd.to_numeric(
    df[TIME_COLUMN],
    errors="coerce",
)

df[VALUE_COLUMN] = pd.to_numeric(
    df[VALUE_COLUMN],
    errors="coerce",
)

df = (
    df.dropna(subset=[TIME_COLUMN, VALUE_COLUMN])
      .sort_values(TIME_COLUMN)
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
# GENERATE PERIODIC TARGET TIMES
# ============================================================
first_time = float(df[TIME_COLUMN].iloc[0])
last_time = float(df[TIME_COLUMN].iloc[-1])

target_times = []

current_target = first_time

while current_target <= last_time:
    target_times.append(current_target)
    current_target += INTERVAL_SECONDS


# ============================================================
# SELECT NEAREST REAL MEASUREMENT
# ============================================================
periodic_rows = []

for target_time in target_times:
    time_differences = (
        df[TIME_COLUMN] - target_time
    ).abs()

    nearest_index = time_differences.idxmin()
    nearest_row = df.loc[nearest_index]

    periodic_rows.append({
        "target_time_seconds": round(
            target_time,
            3,
        ),
        "actual_time_seconds": float(
            nearest_row[TIME_COLUMN]
        ),
        "time_offset_seconds": round(
            float(nearest_row[TIME_COLUMN])
            - target_time,
            3,
        ),
        VALUE_COLUMN: float(
            nearest_row[VALUE_COLUMN]
        ),
        "source_row_index": int(nearest_index),
    })


periodic_df = pd.DataFrame(periodic_rows)


# ============================================================
# VALIDATION
# ============================================================
expected_count = len(target_times)
actual_count = len(periodic_df)

if actual_count != expected_count:
    raise ValueError(
        "Generated transmission count does not match "
        "the number of periodic target times."
    )

if periodic_df["source_row_index"].duplicated().any():
    print(
        "Warning: one raw measurement was selected "
        "for more than one target time."
    )

maximum_absolute_offset = (
    periodic_df["time_offset_seconds"]
    .abs()
    .max()
)


# ============================================================
# SAVE RESULTS
# ============================================================
periodic_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# PRINT VERIFICATION RESULTS
# ============================================================
print("=== PERIODIC 10-SECOND VALIDATION ===")

print(f"Raw measurements: {len(df)}")
print(f"First raw time: {first_time:.3f} s")
print(f"Last raw time: {last_time:.3f} s")

print(
    f"Periodic interval: "
    f"{INTERVAL_SECONDS} s"
)

print(
    f"Generated transmissions: "
    f"{actual_count}"
)

print(
    f"Maximum absolute time offset: "
    f"{maximum_absolute_offset:.3f} s"
)

print("\n=== FIRST 10 TRANSMISSIONS ===")
print(
    periodic_df.head(10).to_string(
        index=False
    )
)

print("\n=== LAST 10 TRANSMISSIONS ===")
print(
    periodic_df.tail(10).to_string(
        index=False
    )
)

print(
    f"\nSaved to:\n{OUTPUT_FILE}"
)