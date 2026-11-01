import matplotlib.pyplot as plt

from plotting_common import (
    DETAIL_END_SECONDS,
    DETAIL_START_SECONDS,
    prepare_representative_data,
    FIGURES_DIR,
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

    reference_times = data["times"]
    reference_values = data["values"]

    periodic = data["periodic"]
    event = data["event"]

    periodic_count = len(periodic)
    event_count = len(event)

    event_reduction_vs_periodic = (
        1
        - event_count / periodic_count
    ) * 100

    detail_mask = (
        (reference_times >= DETAIL_START_SECONDS)
        & (reference_times <= DETAIL_END_SECONDS)
    )

    detail_times = reference_times[
        detail_mask
    ]

    detail_values = reference_values[
        detail_mask
    ]

    detail_periodic_transmissions = periodic[
        (
            periodic["time"]
            >= DETAIL_START_SECONDS
        )
        & (
            periodic["time"]
            <= DETAIL_END_SECONDS
        )
    ].copy()

    detail_event_transmissions = event[
        (
            event["time"]
            >= DETAIL_START_SECONDS
        )
        & (
            event["time"]
            <= DETAIL_END_SECONDS
        )
    ].copy()

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

    # Thin vertical guides for periodic transmissions.
    for _, row in detail_periodic_transmissions.iterrows():
        axis.vlines(
            x=row["time"],
            ymin=detail_values.min(),
            ymax=row["value"],
            color="tab:orange",
            linestyle=":",
            linewidth=0.8,
            alpha=0.45,
            zorder=2,
        )

    # Thin vertical guides for event transmissions.
    for _, row in detail_event_transmissions.iterrows():
        axis.vlines(
            x=row["time"],
            ymin=detail_values.min(),
            ymax=row["value"],
            color="tab:green",
            linestyle=":",
            linewidth=0.8,
            alpha=0.45,
            zorder=2,
        )

    axis.scatter(
        detail_periodic_transmissions["time"],
        detail_periodic_transmissions["value"],
        marker="o",
        s=75,
        facecolors="white",
        edgecolors="tab:orange",
        linewidths=1.8,
        label="Periodic transmissions (10 s)",
        zorder=4,
    )

    axis.scatter(
        detail_event_transmissions["time"],
        detail_event_transmissions["value"],
        marker="x",
        s=75,
        color="tab:green",
        linewidths=2.0,
        label=(
            "Event-driven transmissions "
            "(Δ = 0.10 °C)"
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
        f"Reduction: "
        f"{event_reduction_vs_periodic:.2f}%"
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

    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        FIGURES_DIR
        / "figure_3_transmission_instants.png"
    )

    fig.savefig(
        output_file,
        bbox_inches="tight",
    )

    plt.show()
    plt.close(fig)

    print(
        f"Detailed interval: "
        f"{DETAIL_START_SECONDS}-"
        f"{DETAIL_END_SECONDS} s"
    )

    print(
        f"Periodic transmissions "
        f"in interval: "
        f"{len(detail_periodic_transmissions)}"
    )

    print(
        f"Event-driven transmissions "
        f"in interval: "
        f"{len(detail_event_transmissions)}"
    )

    print(
        f"Complete-experiment reduction: "
        f"{event_reduction_vs_periodic:.2f}%"
    )

    print(
        f"Figure saved to: {output_file}"
    )


if __name__ == "__main__":
    main()