import numpy as np

from transmission_strategies import reconstruct_zero_order_hold


def reconstruction_metrics(
    reference_times,
    reference_values,
    transmissions,
    start_time,
):
    reference_times = np.asarray(
        reference_times,
        dtype=float,
    )

    reference_values = np.asarray(
        reference_values,
        dtype=float,
    )

    if len(reference_times) != len(reference_values):
        raise ValueError(
            "reference times and values must have the same length"
        )

    if len(reference_times) == 0:
        raise ValueError("reference data is empty")

    # Reconstruct the values that would be available at the receiver.
    reconstructed = reconstruct_zero_order_hold(
        reference_times,
        transmissions,
    )

    # All configurations use the same accuracy interval.
    metric_mask = reference_times >= start_time

    if not metric_mask.any():
        raise ValueError(
            "no measurements remain after the metric start time"
        )

    reference_selected = reference_values[metric_mask]
    reconstructed_selected = reconstructed[metric_mask]

    error = reconstructed_selected - reference_selected
    absolute_error = np.abs(error)

    return {
        "mae": float(np.mean(absolute_error)),
        "rmse": float(
            np.sqrt(
                np.mean(error ** 2)
            )
        ),
        "max_error": float(np.max(absolute_error)),
        "p95": float(
            np.percentile(
                absolute_error,
                95,
            )
        ),
    }


def communication_load(
    transmission_count,
    raw_measurement_count,
):
    if raw_measurement_count <= 0:
        raise ValueError(
            "raw measurement count must be positive"
        )

    return (
        transmission_count
        / raw_measurement_count
        * 100
    )