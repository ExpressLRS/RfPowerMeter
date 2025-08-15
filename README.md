# RfPowerMeter

# Before use:

install `uv` python package manager: https://docs.astral.sh/uv/getting-started/installation/

install the required libraries

```uv sync```

# RF Meter Logger (rf_meter_logger.py)

A Python script to log the measured values from a ImmersionRC RF meter, saving the results to a timestamped CSV file.

## Usage
If you run the script without any arguments, it will display usage instructions, the list of supported frequencies, and available serial ports.

```bash
uv run rf_meter_logger.py <serial_port> <frequency> [attenuation]
```

- `<serial_port>`: The serial port to connect to (e.g., `COM3` on Windows or `/dev/ttyUSB0` on Linux/Mac).
- `<frequency>`: Frequency in MHz. Must be one of the supported values (see below).
- `[attenuation]`: (Optional) Attenuation value to add to dBm readings (float).

### Examples

```bash
uv run rf_meter_logger.py COM3 900
uv run rf_meter_logger.py /dev/ttyUSB0 2400 10.5
```

## Supported Frequencies
- 35, 72, 433, 868, 900, 1200, 2400, 5600, 5650, 5700, 5750, 5800, 5850, 5900, 5950, 6000 (MHz)

## Output
- The script creates a CSV file named with the current date and time (e.g., `250417-235849.csv`).
- Each line in the CSV contains:  
  `timestamp (ms), dBm, mW`

## Troubleshooting
- If you see "No serial ports found," check your device connection and permissions.
- If you get a serial error, ensure the port is correct and not in use by another application.


# RF Power Logger Plotter (plot_powers.py)

This script visualizes RF power data from a CSV file (generated from rf_meter_logger.py), providing both raw and moving average plots for dBm and mW values.

## Features
- Reads CSV files with columns: timestamp (ms), RF power (dBm), RF power (mW)
- Optionally applies a correction offset to dBm values (e.g., for compensation of the RF meter)
- Filters to the first hour of data (≤ 3,600,000 ms)
- Excludes the lowest 1% of data (outliers) for both dBm and mW
- Generates two subplots: one for dBm, one for mW

## Usage
```bash
uv run plot_powers.py <csv_file> [correction]
```

- `<csv_file>`: Path to the CSV file to plot. The file should have three columns: timestamp in ms, RF power (dBm), RF power (mW), **without a header row**.
- `[correction]` (optional): A numeric value (float) to add to all dBm readings (e.g., for calibration).

### Example
```bash
uv run plot_powers.py data.csv
```

or with a correction offset:

```bash
uv run plot_powers.py data.csv -2.5
```

## Output

- The script displays two plots:
  - **RF Power (dBm)**: Raw data and moving average over time (minutes)
  - **RF Power (mW)**: Raw data and moving average over time (minutes)
