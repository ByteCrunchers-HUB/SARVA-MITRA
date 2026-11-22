"""
Serial to Cloud Forwarder
Reads JSON sensor readings from your local USB COM port (ESP32)
and forwards them to your cloud-deployed backend on Render.

Usage:
  python tools/serial_forwarder.py --port COM9 --url https://sarva-mitra-0k9a.onrender.com/api/sensors/data
"""

import argparse
import json
import time
import httpx
import serial

def main():
    parser = argparse.ArgumentParser(description="Forward ESP32 USB serial telemetry to Render cloud backend.")
    parser.add_argument("--port", default="COM9", help="Serial port (e.g., COM9 on Windows, /dev/ttyUSB0 on Linux)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument(
        "--url",
        default="https://sarva-mitra-0k9a.onrender.com/api/sensors/data",
        help="Cloud backend ingestion URL (override if your Render URL changes)",
    )
    args = parser.parse_args()

    print(f"=== ESP32 Serial -> Cloud Forwarder ===")
    print(f"Listening on: {args.port} @ {args.baud} baud")
    print(f"Target URL:   {args.url}")
    print("Press Ctrl+C to stop.\n")

    try:
        with httpx.Client(timeout=10.0) as client:
            while True:
                try:
                    print(f"Connecting to {args.port}...")
                    with serial.Serial(args.port, args.baud, timeout=2.0) as ser:
                        print("Connected! Forwarding telemetry packets...\n")
                        while True:
                            raw_line = ser.readline()
                            if not raw_line:
                                continue

                            line = raw_line.decode("utf-8", errors="ignore").strip()
                            if not (line.startswith("{") and line.endswith("}")):
                                continue

                            try:
                                payload = json.loads(line)
                            except json.JSONDecodeError as exc:
                                print(f"[Invalid JSON] Ignoring serial frame: {exc}")
                                continue

                            try:
                                response = client.post(args.url, json=payload)
                                response.raise_for_status()
                                print(f"[OK] Forwarded: {payload}")
                            except httpx.HTTPStatusError as exc:
                                print(f"[HTTP {exc.response.status_code}] Failed: {exc.response.text}")
                            except httpx.RequestError as exc:
                                print(f"[HTTP Error] {exc}. Retrying with the next sensor reading.")

                except serial.SerialException as exc:
                    print(f"[Serial Error] {exc}. Retrying in 5 seconds...")
                    time.sleep(5)
    except KeyboardInterrupt:
        print("\nStopped by user.")

if __name__ == "__main__":
    main()
