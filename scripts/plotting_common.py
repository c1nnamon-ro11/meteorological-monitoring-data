from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from transmission_strategies import (
    event_transmissions,
    periodic_transmissions,
    reconstruct_zero_order_hold,
)

ROOT_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT_DIR
    / "data"
    / "raw"
    / "meteo_raw_log.csv"
)

RESULTS_DIR = ROOT_DIR / "results"
FIGURES_DIR = ROOT_DIR / "figures"


TIME_COLUMN = "elapsed_seconds"
VALUE_COLUMN = "temperature_c"

PERIODIC_INTERVAL_SECONDS = 10
EVENT_THRESHOLD_C = 0.10

DETAIL_START_SECONDS = 280
DETAIL_END_SECONDS = 420

METRIC_START_TIME = 30.190


PHASES = [
    {
        "roman": "I",
        "start": 0,
        "end": 300,
    },
    {
        "roman": "II",
        "start": 300,
        "end": 600,
    },
    {
        "roman": "III",
        "start": 600,
        "end": 900,
    },
    {
        "roman": "IV",
        "start": 900,
        "end": None,
    },
]


plt.rcParams.update(
    {
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "legend.fontsize": 9,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "savefig.dpi": 300,
    }
)


def load_reference_data():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = {
        TIME_COLUMN,
        VALUE_COLUMN,
    }

    missing_columns = required_columns.difference(
        df.columns
    )

    if missing_columns:
        raise ValueError(
            f"Missing required columns: "
            f"{sorted(missing_columns)}"
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


def get_reference_arrays(df):
    times = df[
        TIME_COLUMN
    ].to_numpy(dtype=float)

    values = df[
        VALUE_COLUMN
    ].to_numpy(dtype=float)

    return times, values


def prepare_representative_data():
    df = load_reference_data()

    times, values = get_reference_arrays(df)

    periodic = periodic_transmissions(
        times,
        values,
        PERIODIC_INTERVAL_SECONDS,
    )

    event = event_transmissions(
        times,
        values,
        EVENT_THRESHOLD_C,
    )

    periodic_reconstructed = (
        reconstruct_zero_order_hold(
            times,
            periodic,
        )
    )

    event_reconstructed = (
        reconstruct_zero_order_hold(
            times,
            event,
        )
    )

    return {
        "dataframe": df,
        "times": times,
        "values": values,
        "periodic": periodic,
        "event": event,
        "periodic_reconstructed":
            periodic_reconstructed,
        "event_reconstructed":
            event_reconstructed,
    }


def add_phase_markings(
    axis,
    minimum_time,
    maximum_time,
):
    for index, phase in enumerate(PHASES):
        phase_start = phase["start"]

        phase_end = (
            phase["end"]
            if phase["end"] is not None
            else maximum_time
        )

        visible_start = max(
            phase_start,
            minimum_time,
        )

        visible_end = min(
            phase_end,
            maximum_time,
        )

        if visible_start >= visible_end:
            continue

        # Alternate shading separates the experimental phases.
        if index % 2 == 0:
            axis.axvspan(
                visible_start,
                visible_end,
                color="0.7",
                alpha=0.10,
            )

        phase_center = (
            visible_start
            + visible_end
        ) / 2

        axis.text(
            phase_center,
            0.96,
            phase["roman"],
            transform=axis.get_xaxis_transform(),
            ha="center",
            va="top",
            fontweight="bold",
            fontsize=12,
        )

        if (
            phase["end"] is not None
            and minimum_time
            < phase["end"]
            < maximum_time
        ):
            axis.axvline(
                phase["end"],
                color="0.4",
                linestyle="--",
                linewidth=1.0,
                alpha=0.8,
            )


def save_figure(
    fig,
    filename,
):
    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        FIGURES_DIR
        / filename
    )

    fig.tight_layout()

    fig.savefig(
        output_file,
        bbox_inches="tight",
    )

    return output_file


if __name__ == "__main__":
    data = prepare_representative_data()

    print(
        f"Dataset loaded: "
        f"{len(data['dataframe'])} measurements"
    )

    print(
        f"Periodic transmissions: "
        f"{len(data['periodic'])}"
    )

    print(
        f"Event-driven transmissions: "
        f"{len(data['event'])}"
    )

    print(
        f"Figures directory: "
        f"{FIGURES_DIR}"
    )