import csv
import os
import time
from datetime import datetime

import serial
import serial.tools.list_ports

from rfmeter import BAUD_RATE, FREQUENCIES


def list_serial_ports(usb_only: bool = True) -> list[str]:
    ports = serial.tools.list_ports.comports()
    if usb_only:
        ports = [p for p in ports if p.vid is not None]
    return [port.device for port in ports]


def auto_detect_port() -> str:
    ports = list_serial_ports(usb_only=True)
    if len(ports) == 0:
        raise RuntimeError("No USB serial ports found. Check your device connection.")
    if len(ports) > 1:
        port_list = ", ".join(ports)
        raise RuntimeError(
            f"Multiple USB serial ports found: {port_list}. "
            "Please specify one with --port."
        )
    return ports[0]


def record(
    port: str,
    freq: int,
    group: str,
    test: str,
    attenuation: float = 0.0,
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
    print(f"Output: {filename}")

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

            while True:
                time.sleep(0.4)
                ser.write(b"E\n")
                time.sleep(0.1)
                line = ser.readline().decode().strip()
                ser.readline()

                timestamp = int((time.time() - start_time) * 1000)

                try:
                    dBm = round(float(line) + attenuation, 3)
                    mW = round(10 ** (dBm / 10), 2)
                except ValueError:
                    continue

                print(f"{timestamp},{dBm},{mW}")
                writer.writerow([timestamp, dBm, mW])
                file.flush()

    except KeyboardInterrupt:
        print(f"\nRecording stopped. Data saved to {filename}")
    except serial.SerialException as e:
        print(f"Serial error: {e}")
