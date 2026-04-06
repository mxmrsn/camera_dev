import serial
from serial import SerialException
import os
import sys
import pwd
import grp
import time
import csv
from datetime import datetime
import tkinter as tk
from tkinter.filedialog import asksaveasfilename

PORT = '/dev/ttyACM0'
BAUD = 115200
OUTFILE = ''
LOG_INTERVAL_SEC = 30

def main():

    today = datetime.now().strftime("%Y%m%d")
    default_filename = f"teensy_log_{today}.csv"

    OUTFILE = asksaveasfilename(title="Save log as", defaultextension=".csv",
                                initialfile=default_filename,
                                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])

    if not OUTFILE:
        print("No file selected. Exiting.")
        sys.exit(0)

    ser = open_serial_port_or_exit(PORT, BAUD)
    time.sleep(5)  # Increased delay for Teensy boot

    latest_data = None
    teensy_t0 = None

    with open(OUTFILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['pc_timestamp', 'teensy_ms', 'temperature_c', 'error_code', 
                         'l1', 'l2', 'l3', 'l4', 'l5'])
        
        while True:
            try:
                line = ser.readline().decode('utf-8').strip()
                if not line:
                    continue
                data = parse_frame(line)
                if data:
                    if teensy_t0 is None:
                        teensy_t0 = data['teensy_ms']
                    data['teensy_ms'] = data['teensy_ms'] - teensy_t0
                    latest_data = data
                now = time.time()

                if latest_data and (now - (teensy_t0 + latest_data['teensy_ms'] / 1000)) >= LOG_INTERVAL_SEC:
                    pc_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    writer.writerow([pc_timestamp,
                                     latest_data['teensy_ms'],
                                     latest_data['temperature_c'],
                                     latest_data['error_code'],
                                     latest_data['l1'],
                                     latest_data['l2'],
                                     latest_data['l3'],
                                     latest_data['l4'],
                                     latest_data['l5']])
                    f.flush()
                    t_sec = latest_data['teensy_ms'] / 1000
                    print(f"LOGGED: {t_sec:8.2f} sec, Temp: {latest_data['temperature_c']}, Error: {latest_data['error_code']}, Light: {latest_data['l1']}, {latest_data['l2']}, {latest_data['l3']}, {latest_data['l4']}, {latest_data['l5']}")
            except Exception as e:
                print(f"Error: {e}")

def parse_frame(line):
    parts = line.split(',')
    if len(parts) < 8:
        return None
    try:
        frame = {}
        frame['teensy_ms'] = int(parts[0])
        # thermocouple
        if parts[1].startswith("ERROR"):
            frame['temperature_c'] = None
            if ":" in parts[1]:
                frame['error_code'] = parts[1].split(":")[1]
            else:
                frame['error_code'] = -1
        else:
            frame['temperature_c'] = float(parts[1])
            frame['error_code'] = int(parts[2])
        
        # light_values
        frame['l1'] = float(parts[3])
        frame['l2'] = float(parts[4])
        frame['l3'] = float(parts[5])
        frame['l4'] = float(parts[6])
        frame['l5'] = float(parts[7])
        return frame
    
    except Exception:
        return None

def open_serial_port_or_exit(port, baud, timeout=1):
    """Try to open the serial port and print helpful diagnostics on failure, then exit."""
    try:
        ser = serial.Serial(port, baud, timeout=timeout)
        return ser
    except SerialException as e:
        print(f"Failed to open serial port {port}: {e}")
        if os.path.exists(port):
            st = os.stat(port)
            mode = oct(st.st_mode & 0o777)
            uid = st.st_uid
            gid = st.st_gid
            try:
                uname = pwd.getpwuid(uid).pw_name
            except KeyError:
                uname = str(uid)
            try:
                gname = grp.getgrgid(gid).gr_name
            except KeyError:
                gname = str(gid)
            print(f"Device exists: {port}, permissions: {mode}, owner: {uname}:{gname}")
        else:
            print(f"Device node {port} does not exist. Check `dmesg` after plugging.")
        print("Suggestions:")
        print(f"- Run: ls -l {port}")
        print("- Check kernel messages: dmesg | tail -n 20")
        print("- Add your user to the serial group (e.g. dialout): sudo usermod -a -G dialout $USER")
        print("- See udev rule template: udev/99-teensy.rules in this repo; copy to /etc/udev/rules.d/")
        sys.exit(1)

if __name__ == "__main__":
    main()