# Environmental Monitoring Data Transmission Experiment

This repository contains the experimental dataset, Python source code, and generated results used to evaluate periodic and event-driven data transmission strategies for environmental monitoring.

The experiment was conducted using a Raspberry Pi 4 connected to a Bosch BME680 environmental sensor. Measurements were collected at approximately 0.5 s intervals and used as a common reference dataset for evaluating two alternative transmission strategies:

- periodic transmission with a 10 s interval;
- event-driven transmission with a temperature-change threshold of Δ = 0.10 °C.

Receiver-side signals were reconstructed using zero-order hold (ZOH), representing a monitoring system in which the most recently received value remains available until a new measurement is transmitted.

## Repository Structure

```text
.
├── README.md
├── requirements.txt
├── data/
│   ├── BME680_2026-08-01_18-44-48.csv
│   ├── temperature_periodic_10s.csv
│   └── temperature_event_0_10.csv
├── scripts/
│   ├── BME680Test.py
│   ├── BME680Periodic10s.py
│   ├── BME680EventDriven010.py
│   └── BME680PublicationFigures.py
└── results/
    ├── figure_1_reference_temperature_profile.png
    ├── figure_2_transmission_instants.png
    ├── figure_3_periodic_reconstruction.png
    ├── figure_4_event_reconstruction.png
    ├── figure_5_reconstruction_errors.png
    ├── figure_6_communication_accuracy_tradeoff.png
    ├── temperature_metrics_post_initialization.csv
    └── temperature_reconstruction_and_errors.csv
```

## Dataset

The raw experimental dataset is:

`data/BME680_2026-08-01_18-44-48.csv`

It contains the measurements collected during the BME680 experiment, including:

- session identifier;
- timestamp;
- elapsed experiment time;
- temperature;
- atmospheric pressure;
- relative humidity;
- estimated altitude;
- gas resistance.

A total of 2432 raw measurements were collected.

The two derived datasets are:

`data/temperature_periodic_10s.csv`

Periodic transmission using a 10 s interval.

`data/temperature_event_0_10.csv`

Event-driven transmission using a temperature-change threshold of Δ = 0.10 °C.

Both strategies were generated from the same raw measurement sequence to provide a consistent basis for comparison.

## Experimental Configuration

The main experimental parameters were:

| Parameter | Value |
| --- | --- |
| Processing platform | Raspberry Pi 4 |
| Environmental sensor | Bosch BME680 |
| Raw sampling interval | approximately 0.5 s |
| Raw measurements | 2432 |
| Periodic transmission interval | 10 s |
| Event-driven threshold | 0.10 °C |
| Reconstruction method | Zero-order hold (ZOH) |

The periodic strategy generated 122 transmissions, while the event-driven strategy generated 42 transmissions.

## Python Scripts

### `BME680Test.py`

Acquires measurements from a BME680 sensor connected to a Raspberry Pi through I2C and stores the measurements in CSV format.

This script is only required for collecting a new physical dataset and is not required to reproduce the results from the dataset already included in this repository.

### `BME680Periodic10s.py`

Processes the raw dataset and generates the periodic transmission sequence using a 10 s transmission interval.

### `BME680EventDriven010.py`

Processes the same raw dataset and generates an event-driven transmission whenever the absolute temperature difference relative to the most recently transmitted value reaches or exceeds 0.10 °C.

### `BME680PublicationFigures.py`

Performs receiver-side reconstruction and quantitative analysis of both communication strategies.

The script:

- performs zero-order-hold reconstruction;
- calculates reconstruction errors;
- calculates MAE, RMSE, maximum absolute error, and 95th-percentile absolute error;
- calculates communication load and transmission reduction;
- generates the figures used for analysis;
- exports reconstruction and metric results as CSV files.

## Installation

Python 3 is required.

Install the analysis dependencies using:

```bash
pip install -r requirements.txt
```

The scripts used for reproducing the analysis require:

- pandas;
- NumPy;
- Matplotlib.

### BME680 Data Acquisition

Running `BME680Test.py` additionally requires a Raspberry Pi with a compatible BME680 sensor and the corresponding Adafruit CircuitPython libraries.

The acquisition dependencies can be installed separately on the Raspberry Pi.

The physical sensor is **not required** to reproduce the analysis because the raw experimental dataset is included in this repository.

## Reproducing the Results

From the repository root, first generate the periodic transmission dataset:

```bash
python scripts/BME680Periodic10s.py
```

Then generate the event-driven transmission dataset:

```bash
python scripts/BME680EventDriven010.py
```

Finally, run the reconstruction, quantitative analysis, and figure generation:

```bash
python scripts/BME680PublicationFigures.py
```

Generated figures and quantitative result files are saved in:

```text
results/
```

The derived CSV files included in the repository can therefore be regenerated from the original raw dataset.

## Main Experimental Results

Using the included dataset, the evaluated strategies produced:

| Metric | Periodic | Event-driven |
| --- | ---: | ---: |
| Transmissions | 122 | 42 |
| Communication load | 5.02% | 1.73% |
| MAE | 0.0157 °C | 0.0379 °C |
| RMSE | 0.0280 °C | 0.0480 °C |
| Maximum absolute error | 0.25 °C | 0.10 °C |
| P95 absolute error | 0.05 °C | 0.09 °C |

Compared with periodic transmission, the event-driven strategy reduced the number of transmitted measurements by approximately 65.6%.

These results illustrate the communication-accuracy trade-off between the two strategies rather than indicating that either strategy is universally superior.

## Generated Results

The `results/` directory contains the figures and quantitative output generated by the analysis script.

`temperature_metrics_post_initialization.csv` contains the quantitative metrics for both strategies.

`temperature_reconstruction_and_errors.csv` contains the reference temperature, reconstructed receiver-side signals, absolute reconstruction errors, and information indicating which measurements were included in the quantitative evaluation.

## Data Availability

The raw experimental dataset, derived datasets, source code, and generated results required to reproduce the reported analysis are provided in this repository.