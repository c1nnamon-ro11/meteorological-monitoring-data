from pathlib import Path

import pandas as pd

from calculate_metrics import (
    communication_load,
    reconstruction_metrics,
)
from transmission_strategies import (
    event_transmissions,
    hybrid_transmissions,
    periodic_transmissions,
)

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

# Representative configurations.
PERIODIC_INTERVAL = 10
EVENT_THRESHOLD = 0.10
HYBRID_MAX_INTERVAL = 30

# Common accuracy interval used for reconstruction metrics.
METRIC_START_TIME = 30.190


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


def print_strategy_results(
    name,
    transmissions,
    metrics,
    raw_count,
):
    load = communication_load(
        len(transmissions),
        raw_count,
    )

    print(name)
    print(f"Transmissions: {len(transmissions)}")
    print(f"Communication load: {load:.2f}%")
    print(f"MAE: {metrics['mae']:.4f} °C")
    print(f"RMSE: {metrics['rmse']:.4f} °C")
    print(f"Maximum error: {metrics['max_error']:.2f} °C")
    print(f"P95: {metrics['p95']:.2f} °C")
    print()


def main():
    df = load_data()

    times = df[TIME_COLUMN].to_numpy(dtype=float)
    values = df[VALUE_COLUMN].to_numpy(dtype=float)

    # Generate the representative transmission sequences.
    periodic = periodic_transmissions(
        times,
        values,
        PERIODIC_INTERVAL,
    )

    event = event_transmissions(
        times,
        values,
        EVENT_THRESHOLD,
    )

    hybrid = hybrid_transmissions(
        times,
        values,
        EVENT_THRESHOLD,
        HYBRID_MAX_INTERVAL,
    )

    # Calculate receiver-side reconstruction metrics.
    periodic_metrics = reconstruction_metrics(
        times,
        values,
        periodic,
        METRIC_START_TIME,
    )

    event_metrics = reconstruction_metrics(
        times,
        values,
        event,
        METRIC_START_TIME,
    )

    hybrid_metrics = reconstruction_metrics(
        times,
        values,
        hybrid,
        METRIC_START_TIME,
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Save the transmitted measurements for each representative strategy.
    periodic.to_csv(
        RESULTS_DIR / "periodic_10s_transmissions.csv",
        index=False,
    )

    event.to_csv(
        RESULTS_DIR / "event_0_10_transmissions.csv",
        index=False,
    )

    hybrid.to_csv(
        RESULTS_DIR / "hybrid_0_10_30s_transmissions.csv",
        index=False,
    )

    raw_count = len(df)

    # Store the summary values reported in the manuscript.
    metrics_df = pd.DataFrame(
        [
            {
                "strategy": "Periodic",
                "parameter": "10 s",
                "transmissions": len(periodic),
                "communication_load": communication_load(
                    len(periodic),
                    raw_count,
                ),
                "mae": periodic_metrics["mae"],
                "rmse": periodic_metrics["rmse"],
                "max_error": periodic_metrics["max_error"],
                "p95": periodic_metrics["p95"],
            },
            {
                "strategy": "Event-driven",
                "parameter": "0.10 °C",
                "transmissions": len(event),
                "communication_load": communication_load(
                    len(event),
                    raw_count,
                ),
                "mae": event_metrics["mae"],
                "rmse": event_metrics["rmse"],
                "max_error": event_metrics["max_error"],
                "p95": event_metrics["p95"],
            },
            {
                "strategy": "Hybrid",
                "parameter": "0.10 °C + 30 s",
                "transmissions": len(hybrid),
                "communication_load": communication_load(
                    len(hybrid),
                    raw_count,
                ),
                "mae": hybrid_metrics["mae"],
                "rmse": hybrid_metrics["rmse"],
                "max_error": hybrid_metrics["max_error"],
                "p95": hybrid_metrics["p95"],
            },
        ]
    )

    metrics_df.to_csv(
        RESULTS_DIR / "representative_metrics.csv",
        index=False,
    )

    print(f"Dataset loaded: {raw_count} measurements")
    print(f"Metric start time: {METRIC_START_TIME:.3f} s")
    print()

    print_strategy_results(
        "Periodic, 10 s",
        periodic,
        periodic_metrics,
        raw_count,
    )

    print_strategy_results(
        "Event-driven, Δ = 0.10 °C",
        event,
        event_metrics,
        raw_count,
    )

    print_strategy_results(
        "Hybrid, Δ = 0.10 °C, Tmax = 30 s",
        hybrid,
        hybrid_metrics,
        raw_count,
    )

    threshold_count = (
        hybrid["trigger"] == "threshold"
    ).sum()

    max_interval_count = (
        hybrid["trigger"] == "max_interval"
    ).sum()

    print("Hybrid trigger breakdown")
    print(f"Threshold-triggered: {threshold_count}")
    print(f"Max-interval-triggered: {max_interval_count}")
    print("Initial measurement: 1")
    print()

    print(f"Results saved to: {RESULTS_DIR}")


if __name__ == "__main__":
    main()