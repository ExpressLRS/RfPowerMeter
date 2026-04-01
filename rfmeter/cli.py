import os
from pathlib import Path
from typing import Annotated, Optional

import typer

from rfmeter import FREQUENCIES
from rfmeter.plotter import plot as run_plot
from rfmeter.recorder import auto_detect_port, list_serial_ports, parse_duration
from rfmeter.recorder import record as run_record

app = typer.Typer(help="ImmersionRC RF Power Meter CLI")


def validate_freq(value: int) -> int:
    if value not in FREQUENCIES:
        freq_list = ", ".join(map(str, FREQUENCIES))
        raise typer.BadParameter(f"Must be one of: {freq_list}")
    return value


@app.command()
def record(
    group: Annotated[str, typer.Option("--group", "-g", help="Test group folder name (e.g. 'zerodrag')")],
    test: Annotated[str, typer.Option("--test", "-t", help="Test name (e.g. '868_ant_a')")],
    freq: Annotated[int, typer.Option("--freq", "-f", help="Frequency in MHz", callback=validate_freq)],
    port: Annotated[Optional[str], typer.Option("--port", "-p", help="Serial port (auto-detects if omitted)")] = None,
    attenuation: Annotated[float, typer.Option("--attenuation", "-a", help="dBm offset")] = 0.0,
    duration: Annotated[
        Optional[str], typer.Option("--duration", "-d", help="Recording duration (e.g. '30m', '1h30m', '90s')")
    ] = None,
) -> None:
    """Record RF power measurements to a CSV file."""
    if port is None:
        port = auto_detect_port()
        print(f"Auto-detected port: {port}")

    duration_seconds = None
    if duration:
        try:
            duration_seconds = parse_duration(duration)
        except ValueError as e:
            typer.echo(typer.style(str(e), fg=typer.colors.RED, bold=True), err=True)
            raise typer.Exit(1)

    run_record(
        port=port,
        freq=freq,
        group=group,
        test=test,
        attenuation=attenuation,
        duration_seconds=duration_seconds,
    )


def resolve_latest_csv(group: str | None, test: str | None) -> Path:
    """Find the most recent CSV file in logs/, optionally filtered by group and test."""
    if test and not group:
        raise typer.BadParameter("--test requires --group to be specified.")

    if group:
        search_dir = Path("logs") / group
        if not search_dir.is_dir():
            raise typer.BadParameter(f"Group directory not found: {search_dir}")
        pattern = f"{test}_*.csv" if test else "*.csv"
        matches = list(search_dir.glob(pattern))
    else:
        matches = list(Path("logs").rglob("*.csv"))

    if not matches:
        raise typer.BadParameter("No CSV files found.")

    return max(matches, key=os.path.getmtime)


def build_plot_title(filepath: Path) -> str:
    """Build a plot title from a CSV file path like logs/group/test_timestamp.csv."""
    parts = filepath.parts
    filename = filepath.name
    if len(parts) >= 3 and parts[-3] == "logs":
        group = parts[-2]
        return f"{group} / {filename}"
    elif len(parts) >= 2 and parts[-2] == "logs":
        return filename
    return filename


@app.command()
def plot(
    file: Annotated[Optional[str], typer.Argument(help="Path to CSV file (optional if using --group/--test)")] = None,
    group: Annotated[Optional[str], typer.Option("--group", "-g", help="Filter by test group")] = None,
    test: Annotated[Optional[str], typer.Option("--test", "-t", help="Filter by test name")] = None,
    correction: Annotated[float, typer.Option("--correction", "-c", help="dBm correction offset")] = 0.0,
    max_time: Annotated[float, typer.Option("--max-time", help="Max time to display in minutes")] = 60.0,
    outlier_percentile: Annotated[
        float, typer.Option("--outlier-percentile", help="Bottom percentile to filter")
    ] = 0.01,
    window_size: Annotated[int, typer.Option("--window-size", help="Moving average window size")] = 100,
) -> None:
    """Plot RF power measurements from a CSV file.

    Provide a file path directly, or use --group/--test to auto-find the latest recording.
    With no arguments, plots the most recent CSV across all groups.
    """
    if file:
        filepath = Path(file)
        if not filepath.is_file():
            typer.echo(typer.style(f"Error: File not found: {filepath}", fg=typer.colors.RED, bold=True), err=True)
            raise typer.Exit(1)
    else:
        filepath = resolve_latest_csv(group, test)
        print(f"Plotting: {filepath}")

    title = build_plot_title(filepath)

    run_plot(
        filepath=str(filepath),
        correction=correction,
        max_time=max_time,
        outlier_percentile=outlier_percentile,
        window_size=window_size,
        title=title,
    )


@app.command()
def list_ports(
    all: Annotated[bool, typer.Option("--all", help="Include non-USB serial ports")] = False,
) -> None:
    """List available serial ports."""
    ports = list_serial_ports(usb_only=not all)
    if not ports:
        print("No USB serial ports found." if not all else "No serial ports found.")
    else:
        print("Available serial ports:")
        for port in ports:
            print(f"  {port}")
