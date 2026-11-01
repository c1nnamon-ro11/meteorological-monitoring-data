import numpy as np
import pandas as pd


# Avoid missing threshold hits because of floating-point representation.
EPSILON = 1e-12


def _validate_input(times, values):
    times = np.asarray(times, dtype=float)
    values = np.asarray(values, dtype=float)

    if times.ndim != 1 or values.ndim != 1:
        raise ValueError("times and values must be one-dimensional arrays")

    if len(times) != len(values):
        raise ValueError("times and values must have the same length")

    if len(times) == 0:
        raise ValueError("input data is empty")

    if not np.all(np.isfinite(times)) or not np.all(np.isfinite(values)):
        raise ValueError("input data contains invalid numeric values")

    if np.any(np.diff(times) <= 0):
        raise ValueError("times must be strictly increasing")

    return times, values


def periodic_transmissions(times, values, interval_seconds):
    times, values = _validate_input(times, values)

    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")

    # Periodic targets start from the first recorded measurement.
    target_times = np.arange(
        times[0],
        times[-1] + EPSILON,
        interval_seconds,
    )

    rows = []

    for target_time in target_times:
        # Use the nearest real measurement to each scheduled target.
        source_index = int(np.argmin(np.abs(times - target_time)))

        rows.append(
            {
                "time": float(times[source_index]),
                "value": float(values[source_index]),
                "source_index": source_index,
                "target_time": float(target_time),
            }
        )

    result = pd.DataFrame(rows)

    # Prevent the same raw measurement from being counted twice.
    return (
        result
        .drop_duplicates(subset="source_index", keep="first")
        .reset_index(drop=True)
    )


def event_transmissions(times, values, threshold):
    times, values = _validate_input(times, values)

    if threshold <= 0:
        raise ValueError("threshold must be positive")

    rows = [
        {
            "time": float(times[0]),
            "value": float(values[0]),
            "source_index": 0,
            "absolute_change": np.nan,
        }
    ]

    last_sent_value = float(values[0])

    for index in range(1, len(times)):
        current_value = float(values[index])
        absolute_change = abs(current_value - last_sent_value)

        if absolute_change + EPSILON >= threshold:
            rows.append(
                {
                    "time": float(times[index]),
                    "value": current_value,
                    "source_index": index,
                    "absolute_change": absolute_change,
                }
            )

            last_sent_value = current_value

    return pd.DataFrame(rows)


def hybrid_transmissions(
    times,
    values,
    threshold,
    max_interval_seconds,
):
    times, values = _validate_input(times, values)

    if threshold <= 0:
        raise ValueError("threshold must be positive")

    if max_interval_seconds <= 0:
        raise ValueError("max_interval_seconds must be positive")

    rows = [
        {
            "time": float(times[0]),
            "value": float(values[0]),
            "source_index": 0,
            "trigger": "initial",
        }
    ]

    last_sent_value = float(values[0])
    last_sent_time = float(times[0])

    for index in range(1, len(times)):
        current_time = float(times[index])
        current_value = float(values[index])

        threshold_reached = (
            abs(current_value - last_sent_value) + EPSILON >= threshold
        )

        max_interval_reached = (
            current_time - last_sent_time + EPSILON
            >= max_interval_seconds
        )

        if not (threshold_reached or max_interval_reached):
            continue

        # If both conditions are met, count it as a threshold update.
        trigger = "threshold" if threshold_reached else "max_interval"

        rows.append(
            {
                "time": current_time,
                "value": current_value,
                "source_index": index,
                "trigger": trigger,
            }
        )

        last_sent_value = current_value
        last_sent_time = current_time

    return pd.DataFrame(rows)


def reconstruct_zero_order_hold(reference_times, transmissions):
    reference_times = np.asarray(reference_times, dtype=float)

    required_columns = {"time", "value"}
    missing_columns = required_columns.difference(transmissions.columns)

    if missing_columns:
        raise ValueError(
            f"missing transmission columns: {sorted(missing_columns)}"
        )

    if transmissions.empty:
        raise ValueError("transmissions must not be empty")

    transmitted_times = transmissions["time"].to_numpy(dtype=float)
    transmitted_values = transmissions["value"].to_numpy(dtype=float)

    if np.any(np.diff(transmitted_times) < 0):
        raise ValueError("transmission times must be increasing")

    # Use the latest value available at each reference timestamp.
    indices = (
        np.searchsorted(
            transmitted_times,
            reference_times,
            side="right",
        )
        - 1
    )

    indices = np.maximum(indices, 0)

    return transmitted_values[indices]