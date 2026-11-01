# Cloud-Oriented Meteorological Monitoring with Periodic, Event-Driven, and Hybrid Data Transmission

This repository contains the experimental dataset, analysis scripts, generated results, and figures associated with the manuscript:

**Cloud-Oriented Meteorological Monitoring with Periodic, Event-Driven, and Hybrid Data Transmission**

The repository is intended to support reproducibility of the communication-strategy analysis presented in the manuscript.

## Experimental Dataset

The experimental dataset was collected using a stationary prototype based on:

- Raspberry Pi 4 Model B
- Bosch BME680 environmental sensor

The experiment contains:

- **2432 measurements**
- approximately **0.5 s sampling interval**
- total duration of **1215.691 s**
- temperature as the primary signal used for communication-strategy evaluation

The raw measurement stream is stored in:

```text
data/raw/meteo_raw_log.csv
```

The recorded BME680 temperature stream is used as the common reference signal for comparing transmission and receiver-side reconstruction strategies. It should not be interpreted as an independently calibrated meteorological ground truth.

## Experimental Phases

The measurement session contains four consecutive environmental phases:

| Phase | Time interval | Description |
|---|---:|---|
| I | 0–300 s | Initial indoor baseline |
| II | 300–600 s | Outdoor exposure |
| III | 600–900 s | Intermediate transition |
| IV | 900 s–end | Return to indoor conditions |

These phases provide a combination of relatively stable intervals and periods of changing temperature.

## Transmission Strategies

Three representative communication configurations are evaluated.

### Periodic transmission

Measurements are selected according to scheduled transmission instants.

For each scheduled instant, the **nearest actually recorded measurement** is selected from the raw stream.

The representative configuration uses:

```text
T = 10 s
```

Additional intervals used for the parameter-sensitivity analysis are:

```text
1, 2, 5, 10, 15, 20, and 30 s
```

### Event-driven transmission

A new measurement is transmitted when:

```text
|x_current - x_last_transmitted| >= Δ
```

where `x_last_transmitted` is the most recently transmitted measurement.

The representative threshold is:

```text
Δ = 0.10 °C
```

The parameter-sensitivity analysis evaluates:

```text
0.02, 0.05, 0.10, 0.15, 0.20, and 0.30 °C
```

### Hybrid transmission

The hybrid strategy combines event-driven transmission with a maximum silent interval.

A new measurement is transmitted when either:

```text
|x_current - x_last_transmitted| >= Δ
```

or:

```text
time_since_last_transmission >= Tmax
```

For the evaluated hybrid configuration:

```text
Δ = 0.10 °C
Tmax = 30 s
```

The maximum-interval condition acts as a periodic heartbeat during periods when the event threshold is not reached.

## Receiver-Side Reconstruction

Sparse transmitted measurements are reconstructed using **zero-order hold (ZOH)**.

The most recently transmitted measurement remains available at the receiver until a new measurement is received.

No interpolation, smoothing, or predictive reconstruction is applied before calculating the reconstruction-error metrics.

## Evaluation Interval

Transmission counts and communication load are calculated over the **complete measurement session**.

Reconstruction-error metrics are calculated over a common evaluation interval beginning at:

```text
t = 30.190 s
```

This common interval removes differences caused by initialization and first-update timing between configurations.

## Evaluation Metrics

The following reconstruction metrics are calculated:

- Mean Absolute Error (**MAE**)
- Root Mean Square Error (**RMSE**)
- Maximum absolute reconstruction error
- 95th percentile absolute reconstruction error (**P95**)

Communication efficiency is evaluated using:

- number of transmitted records
- communication load relative to the raw measurement stream
- reduction relative to the representative periodic configuration

## Representative Results

| Strategy | Configuration | Transmissions | Load | MAE | RMSE | Max | P95 |
|---|---|---:|---:|---:|---:|---:|---:|
| Periodic | 10 s | 122 | 5.02% | 0.0143 °C | 0.0232 °C | 0.18 °C | 0.04 °C |
| Event-driven | Δ = 0.10 °C | 43 | 1.77% | 0.0397 °C | 0.0474 °C | 0.09 °C | 0.09 °C |
| Hybrid | Δ = 0.10 °C, Tmax = 30 s | 61 | 2.51% | 0.0305 °C | 0.0405 °C | 0.09 °C | 0.08 °C |

The representative event-driven configuration reduces the number of transmitted records by **64.75%** relative to periodic transmission at 10 s intervals.

## Equal-Budget Comparison

An additional periodic configuration was selected to produce the same number of transmissions as the representative event-driven configuration.

| Strategy | Configuration | Transmissions | Load | MAE | RMSE | Max | P95 |
|---|---|---:|---:|---:|---:|---:|---:|
| Periodic | 28.3 s | 43 | 1.77% | 0.0409 °C | 0.0610 °C | 0.34 °C | 0.12 °C |
| Event-driven | Δ = 0.10 °C | 43 | 1.77% | 0.0397 °C | 0.0474 °C | 0.09 °C | 0.09 °C |

## Repository Structure

```text
.
├── data/
│   └── raw/
│       └── meteo_raw_log.csv
│
├── scripts/
│   ├── calculate_metrics.py
│   ├── equal_budget.py
│   ├── figure_2_reference_profile.py
│   ├── figure_3_transmission_instants.py
│   ├── figure_4_periodic_reconstruction.py
│   ├── figure_5_event_reconstruction.py
│   ├── figure_6_reconstruction_errors.py
│   ├── figure_7_tradeoff.py
│   ├── parameter_sweep.py
│   ├── plotting_common.py
│   ├── run_all.py
│   ├── run_analysis.py
│   └── transmission_strategies.py
│
├── results/
│   ├── equal_budget_comparison.csv
│   ├── event_0_10_transmissions.csv
│   ├── hybrid_0_10_30s_transmissions.csv
│   ├── parameter_sweep.csv
│   ├── periodic_10s_transmissions.csv
│   ├── periodic_28_3s_transmissions.csv
│   └── representative_metrics.csv
│
├── figures/
│   ├── figure_2_reference_temperature_profile.png
│   ├── figure_3_transmission_instants.png
│   ├── figure_4_periodic_reconstruction.png
│   ├── figure_5_event_reconstruction.png
│   ├── figure_6_reconstruction_errors.png
│   └── figure_7_tradeoff.png
│
├── .gitignore
├── README.md
└── requirements.txt
```

Figure 1 of the manuscript presents the system architecture and is not generated by the experimental analysis scripts. The `figures/` directory therefore contains analysis **Figures 2–7**.

## Installation

Clone the repository and install the required Python packages:

```bash
pip install -r requirements.txt
```

The current requirements are:

```text
pandas>=2.0
numpy>=1.24
matplotlib>=3.7
```

## Reproducing All Results

From the repository root, run:

```bash
python scripts/run_all.py
```

This executes the complete reproducibility workflow:

1. representative strategy analysis
2. parameter-sensitivity analysis
3. equal-budget comparison
4. generation of manuscript Figures 2–7

Generated CSV files are written to:

```text
results/
```

Generated figures are written to:

```text
figures/
```

## Running Individual Analyses

Representative periodic, event-driven, and hybrid configurations:

```bash
python scripts/run_analysis.py
```

Parameter-sensitivity analysis:

```bash
python scripts/parameter_sweep.py
```

Equal-budget comparison:

```bash
python scripts/equal_budget.py
```

Figures can also be regenerated individually:

```bash
python scripts/figure_2_reference_profile.py
python scripts/figure_3_transmission_instants.py
python scripts/figure_4_periodic_reconstruction.py
python scripts/figure_5_event_reconstruction.py
python scripts/figure_6_reconstruction_errors.py
python scripts/figure_7_tradeoff.py
```

## Reproducibility Notes

All evaluated transmission configurations are derived from the same raw measurement stream.

The analysis scripts use repository-relative paths and do not depend on the original Raspberry Pi filesystem structure.

The repository does not include cloud credentials, Firebase service-account keys, or other private authentication information.

The generated result files included in `results/` can be compared directly with newly generated outputs to verify reproducibility.