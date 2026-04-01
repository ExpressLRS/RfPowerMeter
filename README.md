# RfPowerMeter

RfPowerMeter is an open-source toolkit for logging and visualizing RF power measurements from the ImmersionRC RF Meter v2. It provides Python scripts to record power levels into CSV files and generate plots for detailed analysis and calibration.

Developed and maintained by **ExpressLRS LLC** and its passionate open source community, working together to advance reliable, high-performance radio control technology.

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
uv sync
```

## Usage

### Record measurements

```bash
rfmeter record --group <group> --test <test> --freq <frequency> [--port <port>] [--attenuation <value>] [--duration <duration>]
```

- `--group`, `-g`: Test group folder name (e.g. `zerodrag`). Creates `logs/<group>/` directory automatically.
- `--test`, `-t`: Test name (e.g. `868_ant_a`). Used in the output filename.
- `--freq`, `-f`: Frequency in MHz. Must be one of the supported values (see below).
- `--port`, `-p`: Serial port (e.g. `/dev/ttyUSB0`, `COM3`). Auto-detects if only one device is connected.
- `--attenuation`, `-a`: dBm offset to add to readings (default: 0.0).
- `--duration`, `-d`: Recording duration (e.g. `30s`, `30m`, `2h`, `1h30m`). Runs indefinitely if omitted.

Output file: `logs/<group>/<test>_<YYMMDD-HHMMSS>.csv`

#### Examples

```bash
# Auto-detect port, record at 868 MHz
rfmeter record --group zerodrag --test 868_ant_a --freq 868

# Record for 30 minutes
rfmeter record -g zerodrag -t 868_ant_a -f 868 -d 30m

# Specify port and attenuation
rfmeter record -g zerodrag -t 868_ant_a -f 868 -p /dev/ttyUSB0 -a 10.5
```

### Plot measurements

```bash
rfmeter plot [<csv_file>] [--group <group>] [--test <test>] [--correction <value>] [--max-time <minutes>] [--outlier-percentile <value>] [--window-size <size>]
```

- `csv_file`: Path to CSV file. Optional — if omitted, auto-finds the latest recording.
- `--group`, `-g`: Filter by test group folder.
- `--test`, `-t`: Filter by test name (requires `--group`).
- `--correction`, `-c`: dBm correction offset (default: 0.0).
- `--max-time`: Max time to display in minutes (default: 60).
- `--outlier-percentile`: Bottom percentile of data to filter out (default: 0.01).
- `--window-size`: Moving average window size in samples (default: 100).

#### Examples

```bash
# Plot the most recent recording across all groups
rfmeter plot

# Plot the latest recording in a group
rfmeter plot --group zerodrag

# Plot the latest recording matching a specific test
rfmeter plot --group zerodrag --test 868_ant_a

# Plot a specific file with options
rfmeter plot logs/zerodrag/868_ant_a_260401-230000.csv --correction -2.5 --max-time 30
```

### List serial ports

```bash
rfmeter list-ports
```

## Supported Frequencies (MHz)

35, 72, 433, 868, 900, 1200, 2400, 5600, 5650, 5700, 5750, 5800, 5850, 5900, 5950, 6000

## Output Format

CSV files contain three columns (no header): `timestamp_ms, dBm, mW`

## Note

If not installed globally, prefix commands with `uv run`:

```bash
uv run rfmeter record --group zerodrag --test 868_ant_a --freq 868
```
