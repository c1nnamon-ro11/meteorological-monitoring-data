import matplotlib.pyplot as plt
import numpy as np

from calculate_metrics import reconstruction_metrics
from plotting_common import (
    EVENT_THRESHOLD_C,
    FIGURES_DIR,
    METRIC_START_TIME,
    prepare_representative_data,
)

plt.rcParams.update(
    {
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "legend.fontsize": 9,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "figure.dpi": 120,
        "savefig.dpi": 300,
    }
)


def main():
    data = prepare_representative_data()

    times = data["times"]
    values = data["values"]

    periodic = data["periodic"]
    event = data["event"]

    periodic_reconstructed = data[
        "periodic_reconstructed"
    ]

    event_reconstructed = data[
        "event_reconstructed"
    ]

    periodic_error = np.abs(
        periodic_reconstructed - values
    )

    event_error = np.abs(
        event_reconstructed - values
    )

    metric_mask = (
        times >= METRIC_START_TIME
    )

    metric_times = times[
        metric_mask
    ]

    periodic_metric_error = periodic_error[
        metric_mask
    ]

    event_metric_error = event_error[
        metric_mask
    ]

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

    fig, axes = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(10, 6.5),
        sharex=True,
    )

    # Periodic reconstruction error.
    axes[0].plot(
        metric_times,
        periodic_metric_error,
        linewidth=1.0,
    )

    axes[0].text(
        0.015,
        0.96,
        (
            f"MAE = {periodic_metrics['mae']:.4f} °C\n"
            f"RMSE = {periodic_metrics['rmse']:.4f} °C\n"
            f"Max = {periodic_metrics['max_error']:.2f} °C\n"
            f"P95 = {periodic_metrics['p95']:.2f} °C"
        ),
        transform=axes[0].transAxes,
        ha="left",
        va="top",
        fontsize=9,
    )

    axes[0].set_ylabel(
        "Absolute error (°C)"
    )

    axes[0].set_title(
        "Periodic reconstruction error (10 s)"
    )

    axes[0].set_ylim(
        0,
        periodic_metrics["max_error"] * 1.08,
    )

    axes[0].grid(
        True,
        alpha=0.25,
    )

    # Event-driven reconstruction error.
    axes[1].plot(
        metric_times,
        event_metric_error,
        linewidth=1.0,
    )

    axes[1].text(
        0.015,
        0.96,
        (
            f"MAE = {event_metrics['mae']:.4f} °C\n"
            f"RMSE = {event_metrics['rmse']:.4f} °C\n"
            f"Max = {event_metrics['max_error']:.2f} °C\n"
            f"P95 = {event_metrics['p95']:.2f} °C"
        ),
        transform=axes[1].transAxes,
        ha="left",
        va="top",
        fontsize=9,
    )

    axes[1].axhline(
        EVENT_THRESHOLD_C,
        linestyle="--",
        linewidth=1.0,
        label="Event threshold (0.10 °C)",
    )

    axes[1].set_xlabel(
        "Elapsed time (s)"
    )

    axes[1].set_ylabel(
        "Absolute error (°C)"
    )

    axes[1].set_title(
        "Event-driven reconstruction error "
        "(Δ = 0.10 °C)"
    )

    axes[1].set_ylim(
        0,
        0.105,
    )

    axes[1].grid(
        True,
        alpha=0.25,
    )

    axes[1].legend(
        loc="upper right"
    )

    # The evaluated data start at 30.190 s.
    # Keep normal Matplotlib tick placement.
    for axis in axes:
        axis.set_xlim(
            metric_times[0],
            metric_times[-1],
        )

    fig.suptitle(
        (
            "Absolute reconstruction errors over the "
            "common evaluation interval "
            f"(t ≥ {METRIC_START_TIME:.3f} s)"
        ),
        fontsize=12,
    )

    fig.tight_layout(
        rect=(0, 0, 1, 0.96)
    )

    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        FIGURES_DIR
        / "figure_6_reconstruction_errors.png"
    )

    fig.savefig(
        output_file,
        bbox_inches="tight",
    )

    plt.show()
    plt.close(fig)

    print(
        f"Metric interval: "
        f"{metric_times[0]:.3f}-"
        f"{metric_times[-1]:.3f} s"
    )

    print()

    print("Periodic")
    print(
        f"MAE: {periodic_metrics['mae']:.4f} °C"
    )
    print(
        f"RMSE: {periodic_metrics['rmse']:.4f} °C"
    )
    print(
        f"Maximum error: "
        f"{periodic_metrics['max_error']:.2f} °C"
    )
    print(
        f"P95: {periodic_metrics['p95']:.2f} °C"
    )

    print()

    print("Event-driven")
    print(
        f"MAE: {event_metrics['mae']:.4f} °C"
    )
    print(
        f"RMSE: {event_metrics['rmse']:.4f} °C"
    )
    print(
        f"Maximum error: "
        f"{event_metrics['max_error']:.2f} °C"
    )
    print(
        f"P95: {event_metrics['p95']:.2f} °C"
    )

    print()

    print(
        f"Figure saved to: {output_file}"
    )


if __name__ == "__main__":
    main()