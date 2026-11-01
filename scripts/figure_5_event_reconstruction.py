import matplotlib.pyplot as plt

from plotting_common import (
    DETAIL_END_SECONDS,
    DETAIL_START_SECONDS,
    FIGURES_DIR,
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

    reference_times = data["times"]
    reference_values = data["values"]

    event = data["event"]
    event_reconstructed = data[
        "event_reconstructed"
    ]

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

    detail_event_reconstructed = (
        event_reconstructed[
            detail_mask
        ]
    )

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
            "(Δ = 0.10 °C)"
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
        detail_event_transmissions["time"],
        detail_event_transmissions["value"],
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

    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        FIGURES_DIR
        / "figure_5_event_reconstruction.png"
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
        f"Event-driven transmissions "
        f"in interval: "
        f"{len(detail_event_transmissions)}"
    )

    print(
        f"Figure saved to: {output_file}"
    )


if __name__ == "__main__":
    main()