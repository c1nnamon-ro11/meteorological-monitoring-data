import matplotlib.pyplot as plt

from plotting_common import (
    FIGURES_DIR,
    add_phase_markings,
    get_reference_arrays,
    load_reference_data,
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
    df = load_reference_data()

    reference_times, reference_values = (
        get_reference_arrays(df)
    )

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

    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        FIGURES_DIR
        / "figure_2_reference_temperature_profile.png"
    )

    fig.savefig(
        output_file,
        bbox_inches="tight",
    )

    plt.show()
    plt.close(fig)

    print(
        f"Dataset loaded: {len(df)} measurements"
    )

    print(
        f"Figure saved to: {output_file}"
    )


if __name__ == "__main__":
    main()