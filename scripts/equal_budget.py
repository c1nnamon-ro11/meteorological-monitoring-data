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

# Configurations used for the equal-budget comparison.
PERIODIC_INTERVAL = 28.3
EVENT_THRESHOLD = 0.10

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

    # 28.3 s gives the same transmission count as the
    # representative event-driven configuration.
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

    if len(periodic) != len(event):
        raise ValueError(
            "The selected configurations do not have "
            "the same transmission count"
        )

    results_df = pd.DataFrame(
        [
            build_result(
                "Periodic",
                f"{PERIODIC_INTERVAL} s",
                periodic,
                periodic_metrics,
                raw_count,
            ),
            build_result(
                "Event-driven",
                f"{EVENT_THRESHOLD:.2f} °C",
                event,
                event_metrics,
                raw_count,
            ),
        ]
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Save the periodic sequence because this configuration is
    # specific to the equal-budget analysis.
    periodic.to_csv(
        RESULTS_DIR / "periodic_28_3s_transmissions.csv",
        index=False,
    )

    results_df.to_csv(
        RESULTS_DIR / "equal_budget_comparison.csv",
        index=False,
    )

    print(f"Dataset loaded: {raw_count} measurements")
    print(f"Metric start time: {METRIC_START_TIME:.3f} s")
    print()

    print("Equal-budget comparison")
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
    print(
        "Results saved to: "
        f"{RESULTS_DIR / 'equal_budget_comparison.csv'}"
    )


if __name__ == "__main__":
    main()