from typing import Annotated, Optional

import typer

from rfmeter import FREQUENCIES
from rfmeter.plotter import plot as run_plot
from rfmeter.recorder import auto_detect_port, list_serial_ports, record as run_record

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
) -> None:
    """Record RF power measurements to a CSV file."""
    if port is None:
        port = auto_detect_port()
        print(f"Auto-detected port: {port}")

    run_record(
        port=port,
        freq=freq,
        group=group,
        test=test,
        attenuation=attenuation,
    )


@app.command()
def plot(
    file: Annotated[str, typer.Argument(help="Path to CSV file")],
    correction: Annotated[float, typer.Option("--correction", "-c", help="dBm correction offset")] = 0.0,
    max_time: Annotated[float, typer.Option("--max-time", help="Max time to display in minutes")] = 60.0,
    outlier_percentile: Annotated[float, typer.Option("--outlier-percentile", help="Bottom percentile to filter")] = 0.01,
    window_size: Annotated[int, typer.Option("--window-size", help="Moving average window size")] = 100,
) -> None:
    """Plot RF power measurements from a CSV file."""
    run_plot(
        filepath=file,
        correction=correction,
        max_time=max_time,
        outlier_percentile=outlier_percentile,
        window_size=window_size,
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
