from pathlib import Path

import pandas as pd

from calculate_metrics import (
    communication_load,
    reconstruction_metrics,
)
from transmission_strategies import (
    event_transmissions,
    periodic_transmissions,
)


# Repository paths.
ROOT_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT_DIR
    / "data"
    / "raw"
    / "meteo_raw_log.csv"
)

RESULTS_DIR = ROOT_DIR / "results"

TIME_COLUMN = "elapsed_seconds"
VALUE_COLUMN = "temperature_c"

METRIC_START_TIME = 30.190

PERIODIC_INTERVALS = [
    1,
    2,
    5,
    10,
    15,
    20,
    30,
]

EVENT_THRESHOLDS = [
    0.02,
    0.05,
    0.10,
    0.15,
    0.20,
    0.30,
]


def load_data():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
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
        df.dropna(
            subset=[
                TIME_COLUMN,
                VALUE_COLUMN,
            ]
        )
        .sort_values(TIME_COLUMN)
        .reset_index(drop=True)
    )

    if df.empty:
        raise ValueError("Input dataset is empty")

    return df


def build_result(
    strategy,
    parameter,
    transmissions,
    metrics,
    raw_count,
):
    return {
        "strategy": strategy,
        "parameter": parameter,
        "transmissions": len(transmissions),
        "communication_load": communication_load(
            len(transmissions),
            raw_count,
        ),
        "mae": metrics["mae"],
        "rmse": metrics["rmse"],
        "max_error": metrics["max_error"],
        "p95": metrics["p95"],
    }


def main():
    df = load_data()

    times = df[TIME_COLUMN].to_numpy(dtype=float)
    values = df[VALUE_COLUMN].to_numpy(dtype=float)

    raw_count = len(df)
    results = []

    # Periodic strategy: evaluate several fixed reporting intervals.
    for interval in PERIODIC_INTERVALS:
        transmissions = periodic_transmissions(
            times,
            values,
            interval,
        )

        metrics = reconstruction_metrics(
            times,
            values,
            transmissions,
            METRIC_START_TIME,
        )

        results.append(
            build_result(
                "Periodic",
                f"{interval} s",
                transmissions,
                metrics,
                raw_count,
            )
        )

    # Event-driven strategy: evaluate several temperature thresholds.
    for threshold in EVENT_THRESHOLDS:
        transmissions = event_transmissions(
            times,
            values,
            threshold,
        )

        metrics = reconstruction_metrics(
            times,
            values,
            transmissions,
            METRIC_START_TIME,
        )

        results.append(
            build_result(
                "Event-driven",
                f"{threshold:.2f} °C",
                transmissions,
                metrics,
                raw_count,
            )
        )

    results_df = pd.DataFrame(results)

    # Keep enough precision for further analysis and figure generation.
    numeric_columns = [
        "communication_load",
        "mae",
        "rmse",
        "max_error",
        "p95",
    ]

    results_df[numeric_columns] = (
        results_df[numeric_columns]
        .round(6)
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        RESULTS_DIR
        / "parameter_sweep.csv"
    )

    results_df.to_csv(
        output_file,
        index=False,
    )

    print(f"Dataset loaded: {raw_count} measurements")
    print(f"Metric start time: {METRIC_START_TIME:.3f} s")
    print()

    print("Parameter sweep")
    print(
        f"{'Strategy':<14}"
        f"{'Parameter':<12}"
        f"{'Tx':>6}"
        f"{'Load %':>10}"
        f"{'MAE':>10}"
        f"{'RMSE':>10}"
        f"{'Max':>10}"
        f"{'P95':>10}"
    )

    print("-" * 82)

    for _, row in results_df.iterrows():
        print(
            f"{row['strategy']:<14}"
            f"{row['parameter']:<12}"
            f"{row['transmissions']:>6}"
            f"{row['communication_load']:>10.2f}"
            f"{row['mae']:>10.4f}"
            f"{row['rmse']:>10.4f}"
            f"{row['max_error']:>10.2f}"
            f"{row['p95']:>10.2f}"
        )

    print()
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()