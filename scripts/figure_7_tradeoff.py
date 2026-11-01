import matplotlib.pyplot as plt
import pandas as pd

from plotting_common import (
    FIGURES_DIR,
    RESULTS_DIR,
)


SWEEP_FILE = (
    RESULTS_DIR
    / "parameter_sweep.csv"
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


def load_results():
    if not SWEEP_FILE.exists():
        raise FileNotFoundError(
            f"Parameter sweep file not found: {SWEEP_FILE}\n"
            "Run parameter_sweep.py first."
        )

    return pd.read_csv(
        SWEEP_FILE
    )


def add_labels(
    axis,
    data,
    metric_column,
):
    for _, row in data.iterrows():

        if row["strategy"] == "Periodic":
            label = str(
                row["parameter"]
            )

            offset = (
                5,
                5,
            )

        else:
            label = (
                f"Δ = "
                f"{row['parameter']}"
            )

            offset = (
                5,
                -12,
            )

        axis.annotate(
            label,
            (
                row["communication_load"],
                row[metric_column],
            ),
            xytext=offset,
            textcoords="offset points",
            fontsize=7.5,
        )


def main():
    results = load_results()

    periodic = (
        results[
            results["strategy"]
            == "Periodic"
        ]
        .sort_values(
            "communication_load"
        )
        .copy()
    )

    event = (
        results[
            results["strategy"]
            == "Event-driven"
        ]
        .sort_values(
            "communication_load"
        )
        .copy()
    )

    if periodic.empty:
        raise ValueError(
            "No periodic results found"
        )

    if event.empty:
        raise ValueError(
            "No event-driven results found"
        )

    fig, axes = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(10, 4.5),
    )

    # ----------------------------------------------------------
    # (a) Communication load versus MAE
    # ----------------------------------------------------------

    axes[0].plot(
        periodic["communication_load"],
        periodic["mae"],
        marker="o",
        linewidth=1.4,
        label="Periodic",
    )

    axes[0].plot(
        event["communication_load"],
        event["mae"],
        marker="o",
        linewidth=1.4,
        label="Event-driven",
    )

    add_labels(
        axes[0],
        periodic,
        "mae",
    )

    add_labels(
        axes[0],
        event,
        "mae",
    )

    axes[0].set_xlabel(
        "Communication load (%)"
    )

    axes[0].set_ylabel(
        "Mean absolute reconstruction error (°C)"
    )

    axes[0].grid(
        True,
        alpha=0.25,
    )

    axes[0].legend(
        loc="upper right"
    )

    axes[0].text(
        0.02,
        0.97,
        "(a)",
        transform=axes[0].transAxes,
        ha="left",
        va="top",
        fontweight="bold",
    )

    # ----------------------------------------------------------
    # (b) Communication load versus maximum error
    # ----------------------------------------------------------

    axes[1].plot(
        periodic["communication_load"],
        periodic["max_error"],
        marker="o",
        linewidth=1.4,
        label="Periodic",
    )

    axes[1].plot(
        event["communication_load"],
        event["max_error"],
        marker="o",
        linewidth=1.4,
        label="Event-driven",
    )

    add_labels(
        axes[1],
        periodic,
        "max_error",
    )

    add_labels(
        axes[1],
        event,
        "max_error",
    )

    axes[1].set_xlabel(
        "Communication load (%)"
    )

    axes[1].set_ylabel(
        "Maximum absolute reconstruction error (°C)"
    )

    axes[1].grid(
        True,
        alpha=0.25,
    )

    axes[1].legend(
        loc="upper right"
    )

    axes[1].text(
        0.02,
        0.97,
        "(b)",
        transform=axes[1].transAxes,
        ha="left",
        va="top",
        fontweight="bold",
    )

    # Keep the small natural margin around the data,
    # matching the manuscript version.
    for axis in axes:
        axis.margins(
            x=0.05
        )

    fig.tight_layout()

    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        FIGURES_DIR
        / "figure_7_tradeoff.png"
    )

    fig.savefig(
        output_file,
        bbox_inches="tight",
    )

    plt.show()
    plt.close(fig)

    print(
        f"Periodic configurations: "
        f"{len(periodic)}"
    )

    print(
        f"Event-driven configurations: "
        f"{len(event)}"
    )

    print(
        f"Figure saved to: {output_file}"
    )


if __name__ == "__main__":
    main()