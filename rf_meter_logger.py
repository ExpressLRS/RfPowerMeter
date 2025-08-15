import serial
import serial.tools.list_ports
import argparse
import time
import csv
import os
from datetime import datetime


def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("No serial ports found.")
    else:
        print("Available serial ports:")
        for port in ports:
            print(f"  {port.device}")


def main():
    FREQUENCIES = [35, 72, 433, 868, 900, 1200, 2400, 5600, 5650, 5700, 5750, 5800, 5850, 5900, 5950, 6000]

    parser = argparse.ArgumentParser()
    parser.add_argument("port", nargs="?", help="Serial port to connect to")
    parser.add_argument("freq", nargs="?", type=int, help="Frequency to use (in MHz)")
    parser.add_argument("attenuation", nargs="?", type=float, help="Attenuation value (optional, float)")
    args = parser.parse_args()

    # Set attenuation variable
    atten = args.attenuation if args.attenuation is not None else 0.0

    if not args.port or args.freq not in FREQUENCIES:
        print("\n[Usage] python script.py <serial_port> <frequency> [attenuation]")
        print("E.g., python script.py COM3 900 or /dev/ttyUSB0 2400")
        print("      python script.py COM3 900 10.5")
        print("\nAvailable frequencies:")
        print(", ".join(map(str, FREQUENCIES)))
        list_serial_ports()
        return

    print(f"Serial port: {args.port}")
    print(f"Frequency: {args.freq}")
    print(f"Attenuation: {atten}")

    freq_index = FREQUENCIES.index(args.freq)
    freq_command = f"F{freq_index}\n".encode()
    # Generate filename like "logs/250417-235849.csv"
    filename = os.path.join("logs", datetime.now().strftime("%y%m%d-%H%M%S") + ".csv")

    try:
        with serial.Serial(args.port, 9600, timeout=1) as ser, open(filename, mode='w', newline='') as file:
            writer = csv.writer(file, delimiter='\t')
            start_time = time.time()

            time.sleep(0.2)
            ser.write(freq_command)
            time.sleep(0.2)
            ser.readline()

            time.sleep(0.2)
            ser.write(freq_command)
            time.sleep(0.2)
            ser.readline()

            # Flush any leftover input
            ser.reset_input_buffer()

            while True:
                time.sleep(0.4)
                ser.write(b"E\n")
                time.sleep(0.1)
                line = ser.readline().decode().strip()
                ser.readline()

                timestamp = int((time.time() - start_time) * 1000)  # millis

                try:
                    dBm = round(float(line) + atten, 3)
                    mW = round(10 ** (dBm / 10), 2)
                except ValueError:
                    continue

                output = f"{timestamp},{dBm},{mW}"
                print(output)
                writer.writerow([output])
                file.flush()

    except serial.SerialException as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
