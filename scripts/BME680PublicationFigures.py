from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# ============================================================
# SETTINGS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"

REFERENCE_FILE = DATA_DIR / "BME680_2026-08-01_18-44-48.csv"
PERIODIC_FILE = DATA_DIR / "temperature_periodic_10s.csv"
EVENT_FILE = DATA_DIR / "temperature_event_0_10.csv"

OUTPUT_DIR = RESULTS_DIR

REFERENCE_TIME_COLUMN = "elapsed_seconds"
PERIODIC_TIME_COLUMN = "actual_time_seconds"
EVENT_TIME_COLUMN = "elapsed_seconds"
VALUE_COLUMN = "temperature_c"

PERIODIC_INTERVAL_SECONDS = 10
EVENT_THRESHOLD_C = 0.10

DETAIL_START_SECONDS = 280
DETAIL_END_SECONDS = 420

# Metrics are evaluated after both strategies have sent
# their first update following the initial measurement.
USE_POST_INITIALIZATION_METRICS = True

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


# ============================================================
# STYLE
# ============================================================
plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "legend.fontsize": 9,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 120,
    "savefig.dpi": 300,
})


# ============================================================
# LOAD AND VALIDATE FILES
# ============================================================
for file_path in [
    REFERENCE_FILE,
    PERIODIC_FILE,
    EVENT_FILE,
]:
    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found:\n{file_path}"
        )

reference_df = pd.read_csv(REFERENCE_FILE)
periodic_df = pd.read_csv(PERIODIC_FILE)
event_df = pd.read_csv(EVENT_FILE)

required_reference_columns = {
    REFERENCE_TIME_COLUMN,
    VALUE_COLUMN,
}

required_periodic_columns = {
    PERIODIC_TIME_COLUMN,
    VALUE_COLUMN,
}

required_event_columns = {
    EVENT_TIME_COLUMN,
    VALUE_COLUMN,
}

missing_reference = (
    required_reference_columns
    .difference(reference_df.columns)
)

missing_periodic = (
    required_periodic_columns
    .difference(periodic_df.columns)
)

missing_event = (
    required_event_columns
    .difference(event_df.columns)
)

if missing_reference:
    raise ValueError(
        "Missing columns in reference file: "
        f"{sorted(missing_reference)}"
    )

if missing_periodic:
    raise ValueError(
        "Missing columns in periodic file: "
        f"{sorted(missing_periodic)}"
    )

if missing_event:
    raise ValueError(
        "Missing columns in event-driven file: "
        f"{sorted(missing_event)}"
    )

reference_df = (
    reference_df
    .sort_values(
        REFERENCE_TIME_COLUMN,
        kind="stable",
    )
    .reset_index(drop=True)
)

periodic_df = (
    periodic_df
    .sort_values(
        PERIODIC_TIME_COLUMN,
        kind="stable",
    )
    .reset_index(drop=True)
)

event_df = (
    event_df
    .sort_values(
        EVENT_TIME_COLUMN,
        kind="stable",
    )
    .reset_index(drop=True)
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# ARRAYS
# ============================================================
reference_times = reference_df[
    REFERENCE_TIME_COLUMN
].to_numpy(dtype=float)

reference_values = reference_df[
    VALUE_COLUMN
].to_numpy(dtype=float)


# ============================================================
# ZERO-ORDER-HOLD RECONSTRUCTION
# ============================================================
def reconstruct_zero_order_hold(
    reference_times_array: np.ndarray,
    transmitted_df: pd.DataFrame,
    transmitted_time_column: str,
    value_column: str,
) -> np.ndarray:
    transmitted_times = transmitted_df[
        transmitted_time_column
    ].to_numpy(dtype=float)

    transmitted_values = transmitted_df[
        value_column
    ].to_numpy(dtype=float)

    if len(transmitted_times) == 0:
        raise ValueError(
            "The transmitted dataset is empty."
        )

    reconstructed = np.empty(
        len(reference_times_array),
        dtype=float,
    )

    transmission_index = 0
    current_value = transmitted_values[0]

    for index, reference_time in enumerate(
        reference_times_array
    ):
        while (
            transmission_index + 1
            < len(transmitted_times)
            and transmitted_times[
                transmission_index + 1
            ]
            <= reference_time
        ):
            transmission_index += 1

            current_value = transmitted_values[
                transmission_index
            ]

        reconstructed[index] = current_value

    return reconstructed


periodic_reconstructed = reconstruct_zero_order_hold(
    reference_times,
    periodic_df,
    PERIODIC_TIME_COLUMN,
    VALUE_COLUMN,
)

event_reconstructed = reconstruct_zero_order_hold(
    reference_times,
    event_df,
    EVENT_TIME_COLUMN,
    VALUE_COLUMN,
)


# ============================================================
# METRIC INTERVAL
# ============================================================
if len(periodic_df) < 2:
    raise ValueError(
        "Periodic data must contain at least two transmissions."
    )

if len(event_df) < 2:
    raise ValueError(
        "Event-driven data must contain at least two transmissions."
    )

first_periodic_update_time = float(
    periodic_df.iloc[1][PERIODIC_TIME_COLUMN]
)

first_event_update_time = float(
    event_df.iloc[1][EVENT_TIME_COLUMN]
)

if USE_POST_INITIALIZATION_METRICS:
    metric_start_time = max(
        first_periodic_update_time,
        first_event_update_time,
    )
else:
    metric_start_time = float(
        reference_times[0]
    )

metric_mask = (
    reference_times >= metric_start_time
)

if not metric_mask.any():
    raise ValueError(
        "No samples remain for metric evaluation."
    )


# ============================================================
# ERRORS AND METRICS
# ============================================================
periodic_signed_error = (
    periodic_reconstructed
    - reference_values
)

event_signed_error = (
    event_reconstructed
    - reference_values
)

periodic_absolute_error = np.abs(
    periodic_signed_error
)

event_absolute_error = np.abs(
    event_signed_error
)


def calculate_metrics(
    signed_error: np.ndarray,
    absolute_error: np.ndarray,
    mask: np.ndarray,
) -> dict:
    selected_signed_error = signed_error[mask]
    selected_absolute_error = absolute_error[mask]

    return {
        "mae": float(
            np.mean(selected_absolute_error)
        ),
        "rmse": float(
            np.sqrt(
                np.mean(
                    selected_signed_error ** 2
                )
            )
        ),
        "max_error": float(
            np.max(selected_absolute_error)
        ),
        "p95_error": float(
            np.percentile(
                selected_absolute_error,
                95,
            )
        ),
    }


periodic_metrics = calculate_metrics(
    periodic_signed_error,
    periodic_absolute_error,
    metric_mask,
)

event_metrics = calculate_metrics(
    event_signed_error,
    event_absolute_error,
    metric_mask,
)


# ============================================================
# SUMMARY VALUES
# ============================================================
raw_count = len(reference_df)
periodic_count = len(periodic_df)
event_count = len(event_df)

periodic_load = (
    periodic_count
    / raw_count
    * 100
)

event_load = (
    event_count
    / raw_count
    * 100
)

event_reduction_vs_periodic = (
    1
    - event_count
    / periodic_count
) * 100


# ============================================================
# SAVE COMPLETE RECONSTRUCTION DATA
# ============================================================
comparison_df = pd.DataFrame({
    "elapsed_seconds":
        reference_times,

    "reference_temperature_c":
        reference_values,

    "periodic_reconstructed_temperature_c":
        periodic_reconstructed,

    "event_reconstructed_temperature_c":
        event_reconstructed,

    "periodic_absolute_error_c":
        periodic_absolute_error,

    "event_absolute_error_c":
        event_absolute_error,

    "included_in_metrics":
        metric_mask,
})

comparison_file = (
    OUTPUT_DIR
    / "temperature_reconstruction_and_errors.csv"
)

comparison_df.to_csv(
    comparison_file,
    index=False,
)


# ============================================================
# HELPER — PHASE MARKINGS
# ============================================================
def add_phase_markings(
    axis,
    minimum_time: float,
    maximum_time: float,
) -> None:
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


# ============================================================
# FIGURE 1 — REFERENCE PROFILE
# ============================================================
fig, axis = plt.subplots(
    figsize=(12, 5.5)
)

axis.plot(
    reference_times,
    reference_values,
    color="0.2",
    linewidth=1.6,
)

add_phase_markings(
    axis,
    float(reference_times[0]),
    float(reference_times[-1]),
)

axis.set_xlabel("Time, s")
axis.set_ylabel("Temperature, °C")

axis.set_title(
    "Reference environmental temperature profile"
)

axis.grid(
    True,
    linestyle=":",
    linewidth=0.7,
    alpha=0.45,
)

fig.tight_layout()

figure_1_file = (
    OUTPUT_DIR
    / "figure_1_reference_temperature_profile.png"
)

fig.savefig(
    figure_1_file,
    bbox_inches="tight",
)

plt.show()
plt.close(fig)


# ============================================================
# DETAILED INTERVAL
# ============================================================
detail_mask = (
    (reference_times >= DETAIL_START_SECONDS)
    & (reference_times <= DETAIL_END_SECONDS)
)

if not detail_mask.any():
    raise ValueError(
        "The selected detailed interval contains no data."
    )

detail_times = reference_times[
    detail_mask
]

detail_values = reference_values[
    detail_mask
]

detail_periodic_reconstructed = (
    periodic_reconstructed[detail_mask]
)

detail_event_reconstructed = (
    event_reconstructed[detail_mask]
)

detail_periodic_transmissions = periodic_df[
    (
        periodic_df[PERIODIC_TIME_COLUMN]
        >= DETAIL_START_SECONDS
    )
    & (
        periodic_df[PERIODIC_TIME_COLUMN]
        <= DETAIL_END_SECONDS
    )
].copy()

detail_event_transmissions = event_df[
    (
        event_df[EVENT_TIME_COLUMN]
        >= DETAIL_START_SECONDS
    )
    & (
        event_df[EVENT_TIME_COLUMN]
        <= DETAIL_END_SECONDS
    )
].copy()


# ============================================================
# FIGURE 2 — TRANSMISSION INSTANTS
# ============================================================
fig, axis = plt.subplots(
    figsize=(12, 5.5)
)

axis.plot(
    detail_times,
    detail_values,
    color="0.45",
    linewidth=1.5,
    alpha=0.8,
    label="Reference temperature",
    zorder=1,
)

# Thin vertical guides for periodic transmissions
for _, row in detail_periodic_transmissions.iterrows():
    axis.vlines(
        x=row[PERIODIC_TIME_COLUMN],
        ymin=detail_values.min(),
        ymax=row[VALUE_COLUMN],
        color="tab:orange",
        linestyle=":",
        linewidth=0.8,
        alpha=0.45,
        zorder=2,
    )

# Thin vertical guides for event transmissions
for _, row in detail_event_transmissions.iterrows():
    axis.vlines(
        x=row[EVENT_TIME_COLUMN],
        ymin=detail_values.min(),
        ymax=row[VALUE_COLUMN],
        color="tab:green",
        linestyle=":",
        linewidth=0.8,
        alpha=0.45,
        zorder=2,
    )

axis.scatter(
    detail_periodic_transmissions[
        PERIODIC_TIME_COLUMN
    ],
    detail_periodic_transmissions[
        VALUE_COLUMN
    ],
    marker="o",
    s=75,
    facecolors="white",
    edgecolors="tab:orange",
    linewidths=1.8,
    label=(
        "Periodic transmissions "
        f"({PERIODIC_INTERVAL_SECONDS} s)"
    ),
    zorder=4,
)

axis.scatter(
    detail_event_transmissions[
        EVENT_TIME_COLUMN
    ],
    detail_event_transmissions[
        VALUE_COLUMN
    ],
    marker="x",
    s=75,
    color="tab:green",
    linewidths=2.0,
    label=(
        "Event-driven transmissions "
        f"(Δ = {EVENT_THRESHOLD_C:.2f} °C)"
    ),
    zorder=5,
)

axis.set_xlabel("Time, s")
axis.set_ylabel("Temperature, °C")

axis.set_title(
    "Transmission instants during the selected interval"
)

axis.grid(
    True,
    linestyle=":",
    linewidth=0.7,
    alpha=0.4,
)

axis.legend(
    loc="lower right",
    framealpha=0.95,
)

annotation_text = (
    f"Complete experiment\n"
    f"Periodic: {periodic_count} records\n"
    f"Event-driven: {event_count} records\n"
    f"Reduction: {event_reduction_vs_periodic:.1f}%"
)

axis.text(
    0.02,
    0.97,
    annotation_text,
    transform=axis.transAxes,
    ha="left",
    va="top",
    fontsize=9.5,
    bbox={
        "boxstyle": "round,pad=0.4",
        "facecolor": "white",
        "edgecolor": "0.4",
        "alpha": 0.95,
    },
)

fig.tight_layout()

figure_2_file = (
    OUTPUT_DIR
    / "figure_2_transmission_instants.png"
)

fig.savefig(
    figure_2_file,
    bbox_inches="tight",
)

plt.show()
plt.close(fig)


# ============================================================
# FIGURE 3 — PERIODIC RECONSTRUCTION
# ============================================================
fig, axis = plt.subplots(
    figsize=(12, 5.5)
)

axis.plot(
    detail_times,
    detail_values,
    color="0.45",
    linewidth=1.4,
    alpha=0.8,
    label="Reference temperature",
    zorder=1,
)

axis.step(
    detail_times,
    detail_periodic_reconstructed,
    where="post",
    color="tab:orange",
    linewidth=2.0,
    label=(
        "Periodic reconstruction "
        f"({PERIODIC_INTERVAL_SECONDS} s)"
    ),
    zorder=3,
)

axis.fill_between(
    detail_times,
    detail_values,
    detail_periodic_reconstructed,
    step="post",
    color="tab:orange",
    alpha=0.14,
    label="Reconstruction deviation",
    zorder=2,
)

axis.scatter(
    detail_periodic_transmissions[
        PERIODIC_TIME_COLUMN
    ],
    detail_periodic_transmissions[
        VALUE_COLUMN
    ],
    marker="o",
    s=70,
    facecolors="white",
    edgecolors="tab:orange",
    linewidths=1.8,
    label="Transmitted measurements",
    zorder=5,
)

axis.set_xlabel("Time, s")
axis.set_ylabel("Temperature, °C")

axis.set_title(
    "Periodic receiver-side reconstruction"
)

axis.grid(
    True,
    linestyle=":",
    linewidth=0.7,
    alpha=0.4,
)

axis.legend(
    loc="upper left",
    framealpha=0.95,
)

fig.tight_layout()

figure_3_file = (
    OUTPUT_DIR
    / "figure_3_periodic_reconstruction.png"
)

fig.savefig(
    figure_3_file,
    bbox_inches="tight",
)

plt.show()
plt.close(fig)


# ============================================================
# FIGURE 4 — EVENT-DRIVEN RECONSTRUCTION
# ============================================================
fig, axis = plt.subplots(
    figsize=(12, 5.5)
)

axis.plot(
    detail_times,
    detail_values,
    color="0.45",
    linewidth=1.4,
    alpha=0.8,
    label="Reference temperature",
    zorder=1,
)

axis.step(
    detail_times,
    detail_event_reconstructed,
    where="post",
    color="tab:green",
    linewidth=2.0,
    linestyle="--",
    label=(
        "Event-driven reconstruction "
        f"(Δ = {EVENT_THRESHOLD_C:.2f} °C)"
    ),
    zorder=3,
)

axis.fill_between(
    detail_times,
    detail_values,
    detail_event_reconstructed,
    step="post",
    color="tab:green",
    alpha=0.14,
    label="Reconstruction deviation",
    zorder=2,
)

axis.scatter(
    detail_event_transmissions[
        EVENT_TIME_COLUMN
    ],
    detail_event_transmissions[
        VALUE_COLUMN
    ],
    marker="x",
    s=75,
    color="tab:green",
    linewidths=2.0,
    label="Transmitted measurements",
    zorder=5,
)

axis.set_xlabel("Time, s")
axis.set_ylabel("Temperature, °C")

axis.set_title(
    "Event-driven receiver-side reconstruction"
)

axis.grid(
    True,
    linestyle=":",
    linewidth=0.7,
    alpha=0.4,
)

axis.legend(
    loc="upper left",
    framealpha=0.95,
)

fig.tight_layout()

figure_4_file = (
    OUTPUT_DIR
    / "figure_4_event_reconstruction.png"
)

fig.savefig(
    figure_4_file,
    bbox_inches="tight",
)

plt.show()
plt.close(fig)


# ============================================================
# FIGURE 5 — RECONSTRUCTION ERRORS
# ============================================================
metric_times = reference_times[
    metric_mask
]

metric_periodic_errors = (
    periodic_absolute_error[metric_mask]
)

metric_event_errors = (
    event_absolute_error[metric_mask]
)

fig, axes = plt.subplots(
    nrows=2,
    ncols=1,
    figsize=(12, 8),
    sharex=True,
)

# Periodic error
axes[0].plot(
    metric_times,
    metric_periodic_errors,
    color="tab:orange",
    linewidth=1.0,
)

axes[0].axhline(
    periodic_metrics["mae"],
    color="0.25",
    linestyle="--",
    linewidth=1.2,
    label=(
        f"MAE = "
        f"{periodic_metrics['mae']:.3f} °C"
    ),
)

periodic_text = (
    f"RMSE: {periodic_metrics['rmse']:.3f} °C\n"
    f"Maximum: {periodic_metrics['max_error']:.3f} °C\n"
    f"P95: {periodic_metrics['p95_error']:.3f} °C"
)

axes[0].text(
    0.98,
    0.92,
    periodic_text,
    transform=axes[0].transAxes,
    ha="right",
    va="top",
    fontsize=9,
    bbox={
        "boxstyle": "round,pad=0.35",
        "facecolor": "white",
        "edgecolor": "0.5",
        "alpha": 0.9,
    },
)

axes[0].set_ylabel(
    "Absolute error, °C"
)

axes[0].set_title(
    "Periodic reconstruction error"
)

axes[0].set_ylim(
    bottom=0
)

axes[0].grid(
    True,
    linestyle=":",
    linewidth=0.7,
    alpha=0.4,
)

axes[0].legend(
    loc="upper left"
)

# Event-driven error
axes[1].plot(
    metric_times,
    metric_event_errors,
    color="tab:green",
    linewidth=1.0,
)

axes[1].axhline(
    EVENT_THRESHOLD_C,
    color="0.25",
    linestyle=":",
    linewidth=1.3,
    label=(
        f"Event threshold = "
        f"{EVENT_THRESHOLD_C:.2f} °C"
    ),
)

axes[1].axhline(
    event_metrics["mae"],
    color="0.45",
    linestyle="--",
    linewidth=1.2,
    label=(
        f"MAE = "
        f"{event_metrics['mae']:.3f} °C"
    ),
)

event_text = (
    f"RMSE: {event_metrics['rmse']:.3f} °C\n"
    f"Maximum: {event_metrics['max_error']:.3f} °C\n"
    f"P95: {event_metrics['p95_error']:.3f} °C"
)

axes[1].text(
    0.98,
    0.92,
    event_text,
    transform=axes[1].transAxes,
    ha="right",
    va="top",
    fontsize=9,
    bbox={
        "boxstyle": "round,pad=0.35",
        "facecolor": "white",
        "edgecolor": "0.5",
        "alpha": 0.9,
    },
)

axes[1].set_xlabel(
    "Time, s"
)

axes[1].set_ylabel(
    "Absolute error, °C"
)

axes[1].set_title(
    "Event-driven reconstruction error"
)

axes[1].set_ylim(
    0,
    EVENT_THRESHOLD_C * 1.2,
)

axes[1].grid(
    True,
    linestyle=":",
    linewidth=0.7,
    alpha=0.4,
)

axes[1].legend(
    loc="upper left"
)

fig.suptitle(
    (
        "Absolute reconstruction errors after "
        f"initialization (t ≥ {metric_start_time:.3f} s)"
    ),
    y=0.995,
)

fig.tight_layout()

figure_5_file = (
    OUTPUT_DIR
    / "figure_5_reconstruction_errors.png"
)

fig.savefig(
    figure_5_file,
    bbox_inches="tight",
)

plt.show()
plt.close(fig)


# ============================================================
# FIGURE 6 — COMMUNICATION–ACCURACY TRADE-OFF
# ============================================================
fig, axis = plt.subplots(
    figsize=(8, 5.5)
)

axis.scatter(
    periodic_metrics["mae"],
    periodic_load,
    marker="o",
    s=130,
    facecolors="white",
    edgecolors="tab:orange",
    linewidths=2.2,
    label="Periodic",
    zorder=4,
)

axis.scatter(
    event_metrics["mae"],
    event_load,
    marker="x",
    s=130,
    color="tab:green",
    linewidths=2.4,
    label="Event-driven",
    zorder=5,
)

axis.annotate(
    (
        f"Periodic\n"
        f"{periodic_count} records"
    ),
    (
        periodic_metrics["mae"],
        periodic_load,
    ),
    xytext=(12, 10),
    textcoords="offset points",
)

axis.annotate(
    (
        f"Event-driven\n"
        f"{event_count} records"
    ),
    (
        event_metrics["mae"],
        event_load,
    ),
    xytext=(12, -28),
    textcoords="offset points",
)

axis.set_xlabel(
    "Mean absolute reconstruction error, °C"
)

axis.set_ylabel(
    "Communication load, %"
)

axis.set_title(
    "Communication–accuracy trade-off"
)

axis.grid(
    True,
    linestyle=":",
    linewidth=0.7,
    alpha=0.45,
)

axis.legend(
    loc="best"
)

fig.tight_layout()

figure_6_file = (
    OUTPUT_DIR
    / "figure_6_communication_accuracy_tradeoff.png"
)

fig.savefig(
    figure_6_file,
    bbox_inches="tight",
)

plt.show()
plt.close(fig)


# ============================================================
# METRIC TABLE
# ============================================================
metrics_df = pd.DataFrame([
    {
        "strategy": "Periodic",
        "configuration":
            f"{PERIODIC_INTERVAL_SECONDS} s",

        "transmissions":
            periodic_count,

        "communication_load_percent":
            periodic_load,

        "reduction_vs_raw_percent":
            (
                1
                - periodic_count
                / raw_count
            )
            * 100,

        "reduction_vs_periodic_percent":
            0.0,

        **periodic_metrics,
    },
    {
        "strategy": "Event-driven",
        "configuration":
            f"Δ = {EVENT_THRESHOLD_C:.2f} °C",

        "transmissions":
            event_count,

        "communication_load_percent":
            event_load,

        "reduction_vs_raw_percent":
            (
                1
                - event_count
                / raw_count
            )
            * 100,

        "reduction_vs_periodic_percent":
            event_reduction_vs_periodic,

        **event_metrics,
    },
])

metrics_file = (
    OUTPUT_DIR
    / "temperature_metrics_post_initialization.csv"
)

metrics_df.to_csv(
    metrics_file,
    index=False,
)


# ============================================================
# PRINT RESULTS
# ============================================================
print(
    "=== POST-INITIALIZATION METRIC EVALUATION ==="
)

print(
    f"Raw measurements: {raw_count}"
)

print(
    f"Metric start time: "
    f"{metric_start_time:.3f} s"
)

print(
    f"Samples included: "
    f"{metric_mask.sum()}"
)

print(
    f"Samples excluded during initialization: "
    f"{len(reference_df) - metric_mask.sum()}"
)

print(
    "\n=== STRATEGY RESULTS ==="
)

print(
    metrics_df
    .round(5)
    .to_string(index=False)
)

print(
    "\n=== PHASE INTERVALS ==="
)

for phase in PHASES:
    phase_end_text = (
        f"{phase['end']} s"
        if phase["end"] is not None
        else "end of experiment"
    )

    print(
        f"Phase {phase['roman']}: "
        f"{phase['start']} s to "
        f"{phase_end_text}"
    )

print(
    f"\nAll outputs were saved to:\n"
    f"{OUTPUT_DIR.resolve()}"
)