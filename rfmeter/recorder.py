import csv
import os
import re
import time
from datetime import datetime

import serial
import serial.tools.list_ports
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from rfmeter import BAUD_RATE, FREQUENCIES


def list_serial_ports(usb_only: bool = True) -> list[str]:
    ports = serial.tools.list_ports.comports()
    if usb_only:
        ports = [p for p in ports if p.vid is not None]
    return [port.device for port in ports]


IMMERSIONRC_VID = 1240
IMMERSIONRC_PID = 10
IMMERSIONRC_MANUFACTURER = "ImmersionRC"


def is_immersionrc(port) -> bool:
    if port.vid == IMMERSIONRC_VID and port.pid == IMMERSIONRC_PID:
        return True
    return port.manufacturer is not None and IMMERSIONRC_MANUFACTURER in port.manufacturer


def find_immersionrc_ports() -> list[str]:
    return [p.device for p in serial.tools.list_ports.comports() if is_immersionrc(p)]


def auto_detect_port() -> str:
    ports = find_immersionrc_ports()
    if len(ports) == 1:
        return ports[0]
    if len(ports) > 1:
        port_list = ", ".join(ports)
        raise RuntimeError(f"Multiple ImmersionRC devices found: {port_list}. Please specify one with --port.")
    # Fallback to any USB serial port
    usb_ports = list_serial_ports(usb_only=True)
    if len(usb_ports) == 0:
        raise RuntimeError("No USB serial ports found. Check your device connection.")
    if len(usb_ports) == 1:
        return usb_ports[0]
    port_list = ", ".join(usb_ports)
    raise RuntimeError(
        f"No ImmersionRC device found. Multiple USB ports available: {port_list}. Please specify one with --port."
    )


_DURATION_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(h|m|s)", re.IGNORECASE)
_UNIT_MULTIPLIERS = {"h": 3600, "m": 60, "s": 1}


def parse_duration(value: str) -> float:
    """Parse a duration string into seconds.

    Supports: '90s', '30m', '2h', '1h30m', '1h30m15s', or plain number (seconds).
    """
    matches = _DURATION_PATTERN.findall(value)
    if matches:
        return sum(float(num) * _UNIT_MULTIPLIERS[unit.lower()] for num, unit in matches)
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"Invalid duration format: '{value}'. Use e.g. '30m', '1h30m', '90s'.")


def _format_elapsed(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _progress_bar(fraction: float, width: int = 20) -> str:
    filled = int(fraction * width)
    return "█" * filled + "░" * (width - filled)


def _build_panel(
    group: str,
    test: str,
    elapsed: float,
    duration_seconds: float | None,
    current_dBm: float,
    current_mW: float,
    min_dBm: float,
    max_dBm: float,
    sum_dBm: float,
    min_mW: float,
    max_mW: float,
    sum_mW: float,
    sample_count: int,
) -> Panel:
    lines = []

    # Line 1: elapsed / progress
    if duration_seconds:
        fraction = min(elapsed / duration_seconds, 1.0)
        pct = int(fraction * 100)
        bar = _progress_bar(fraction)
        lines.append(f"  {_format_elapsed(elapsed)} / {_format_elapsed(duration_seconds)}   {bar}  {pct}%")
    else:
        lines.append(f"  {_format_elapsed(elapsed)} elapsed  |  #{sample_count} samples")

    # Line 2: current values
    lines.append(f"  Current: {current_dBm:.3f} dBm  |  {current_mW:.2f} mW")
    lines.append("")

    # Lines 3-4: stats
    if sample_count > 0:
        avg_dBm = sum_dBm / sample_count
        avg_mW = sum_mW / sample_count
        lines.append(f"  dBm   min: {min_dBm:.3f}   max: {max_dBm:.3f}   avg: {avg_dBm:.3f}")
        lines.append(f"  mW    min: {min_mW:.2f}    max: {max_mW:.2f}    avg: {avg_mW:.2f}")

    content = Text("\n".join(lines))
    return Panel(content, title=f"Recording: {group} / {test}", expand=False)


def record(
    port: str,
    freq: int,
    group: str,
    test: str,
    attenuation: float = 0.0,
    duration_seconds: float | None = None,
) -> None:
    freq_index = FREQUENCIES.index(freq)
    freq_command = f"F{freq_index}\n".encode()

    log_dir = os.path.join("logs", group)
    os.makedirs(log_dir, exist_ok=True)

    timestamp_str = datetime.now().strftime("%y%m%d-%H%M%S")
    filename = os.path.join(log_dir, f"{test}_{timestamp_str}.csv")

    print(f"Serial port: {port}")
    print(f"Frequency: {freq} MHz")
    print(f"Attenuation: {attenuation}")
    if duration_seconds:
        print(f"Duration: {_format_elapsed(duration_seconds)}")
    print(f"Output: {filename}")
    print()

    try:
        with serial.Serial(port, BAUD_RATE, timeout=1) as ser, open(filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            start_time = time.time()

            # Set frequency (send twice for reliability)
            time.sleep(0.2)
            ser.write(freq_command)
            time.sleep(0.2)
            ser.readline()

            time.sleep(0.2)
            ser.write(freq_command)
            time.sleep(0.2)
            ser.readline()

            ser.reset_input_buffer()

            # Running stats
            min_dBm = float("inf")
            max_dBm = float("-inf")
            sum_dBm = 0.0
            min_mW = float("inf")
            max_mW = float("-inf")
            sum_mW = 0.0
            sample_count = 0
            current_dBm = 0.0
            current_mW = 0.0

            with Live(refresh_per_second=4) as live:
                while True:
                    elapsed = time.time() - start_time

                    if duration_seconds and elapsed >= duration_seconds:
                        break

                    time.sleep(0.4)
                    ser.write(b"E\n")
                    time.sleep(0.1)
                    line = ser.readline().decode().strip()
                    ser.readline()

                    timestamp = int((time.time() - start_time) * 1000)

                    try:
                        current_dBm = round(float(line) + attenuation, 3)
                        current_mW = round(10 ** (current_dBm / 10), 2)
                    except ValueError:
                        continue

                    sample_count += 1
                    min_dBm = min(min_dBm, current_dBm)
                    max_dBm = max(max_dBm, current_dBm)
                    sum_dBm += current_dBm
                    min_mW = min(min_mW, current_mW)
                    max_mW = max(max_mW, current_mW)
                    sum_mW += current_mW

                    writer.writerow([timestamp, current_dBm, current_mW])
                    file.flush()

                    live.update(
                        _build_panel(
                            group=group,
                            test=test,
                            elapsed=elapsed,
                            duration_seconds=duration_seconds,
                            current_dBm=current_dBm,
                            current_mW=current_mW,
                            min_dBm=min_dBm,
                            max_dBm=max_dBm,
                            sum_dBm=sum_dBm,
                            min_mW=min_mW,
                            max_mW=max_mW,
                            sum_mW=sum_mW,
                            sample_count=sample_count,
                        )
                    )

        print(f"Recording complete. {sample_count} samples saved to {filename}")

    except KeyboardInterrupt:
        print(f"\nRecording stopped. {sample_count} samples saved to {filename}")
    except serial.SerialException as e:
        print(f"Serial error: {e}")
