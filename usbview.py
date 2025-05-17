#!/usr/bin/env python3
import subprocess
import re
import sys
import os
import argparse
from typing import List, Dict, Any

# USB speed mapping (in Mbps)
USB_SPEEDS = {
    '5000': 'USB 3.0',
    '10000': 'USB 3.1',
    '480': 'USB 2.0',
    '12': 'USB 1.1',
    '1.5': 'USB 1.0',
}

# Partial USB vendor lookup (expand as needed)
USB_VENDORS = {
    '046d': 'Logitech Inc.',
    '04b3': 'IBM Corporation',
    '05ac': 'Apple',
    '0403': 'Future Technology Devices International Limited',
    '04e8': 'Samsung Electronics Co., Ltd.',
    '045e': 'Microsoft Corporation',
    # Add more as needed
}

def check_lsusb_installed():
    from shutil import which
    if which('lsusb') is None:
        print("Error: 'lsusb' is not installed. Please install it to use this tool.")
        sys.exit(1)

def get_usb_devices():
    try:
        lsusb_output = subprocess.check_output(['lsusb', '-t'], text=True)
    except Exception as e:
        print(f"Error running lsusb: {e}")
        sys.exit(1)
    return lsusb_output

def get_lsusb_details():
    try:
        return subprocess.check_output(['lsusb'], text=True)
    except Exception as e:
        print(f"Error running lsusb: {e}")
        sys.exit(1)

def get_lsusb_full_details():
    try:
        return subprocess.check_output(['lsusb', '-v'], text=True, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Error running lsusb -v: {e}")
        return ""

def parse_usb_tree(tree_output):
    devices = []
    current_bus = None
    bus_stack = []
    for line in tree_output.splitlines():
        # Detect bus line and update stack
        bus_match = re.match(r'/.*Bus (\d+)\.Port (\d+): Dev (\d+), Class=([^,]+), Driver=([^,]+), (\d+(?:\.\d+)?)M', line)
        if bus_match:
            bus, port, dev, cls, driver, speed = bus_match.groups()
            current_bus = bus
            bus_stack = [bus]  # Reset stack for new root
            category = USB_SPEEDS.get(speed, f"Unknown ({speed}M)")
            devices.append({
                'Bus': bus,
                'Port': port,
                'Device': dev,
                'Class': cls,
                'Driver': driver,
                'Speed (Mbps)': speed,
                'Category': category
            })
            continue
        # Detect sub-device/interface lines
        port_match = re.match(r'(\s*)\|__ Port (\d+): Dev (\d+), If (\d+), Class=([^,]+), Driver=([^,]+), (\d+(?:\.\d+)?)M', line)
        if port_match:
            indent, port, dev, iface, cls, driver, speed = port_match.groups()
            # Infer bus from stack depth (each 4 spaces = one level)
            depth = len(indent) // 4
            bus = bus_stack[0] if bus_stack else current_bus if current_bus else 'Unknown'
            category = USB_SPEEDS.get(speed, f"Unknown ({speed}M)")
            devices.append({
                'Bus': bus,
                'Port': port,
                'Device': dev,
                'Interface': iface,
                'Class': cls,
                'Driver': driver,
                'Speed (Mbps)': speed,
                'Category': category
            })
        # Track current bus for sub-devices (for robustness)
        bus_only = re.match(r'/.*Bus (\d+)', line)
        if bus_only:
            current_bus = bus_only.group(1)
    return devices

def parse_lsusb_details(lsusb_output):
    # Parse lines like: Bus 002 Device 003: ID 046d:c534 Logitech, Inc. Unifying Receiver
    details = {}
    for line in lsusb_output.splitlines():
        m = re.match(r'Bus (\d+) Device (\d+): ID ([0-9a-f]{4}):([0-9a-f]{4})', line, re.I)
        if m:
            bus, dev, vid, pid = m.groups()
            vendor = USB_VENDORS.get(vid.lower(), f"Unknown (0x{vid})")
            details[(bus, dev)] = {'VendorID': vid, 'ProductID': pid, 'VendorName': vendor, 'Raw': line}
    return details

def parse_lsusb_full_details(lsusb_v_output):
    # Parse detailed info for each device
    devices = {}
    current = None
    for line in lsusb_v_output.splitlines():
        m = re.match(r'Bus (\d{3}) Device (\d{3}): ID ([0-9a-f]{4}):([0-9a-f]{4}) (.+)', line, re.I)
        if m:
            bus, dev, vid, pid, rest = m.groups()
            current = (bus, dev)
            devices[current] = {'VendorID': vid, 'ProductID': pid, 'VendorName': USB_VENDORS.get(vid.lower(), f"Unknown (0x{vid})"), 'ProductName': rest.strip()}
        elif current:
            # Look for iManufacturer, iProduct, iSerial
            if 'iManufacturer' in line:
                devices[current]['Manufacturer'] = line.split(' ', 2)[-1].strip()
            if 'iProduct' in line:
                devices[current]['Product'] = line.split(' ', 2)[-1].strip()
            if 'iSerial' in line:
                devices[current]['Serial'] = line.split(' ', 2)[-1].strip()
    return devices

def print_tree(devices: List[Dict[str, Any]], details: Dict, full_details: Dict, show_extra: bool = True, color: bool = True):
    try:
        from colorama import Fore, Style, init
        init(autoreset=True)
    except ImportError:
        color = False
    # Build a lookup for (bus, dev) to lsusb line
    lsusb_lines = {}
    for (bus, dev), info in details.items():
        lsusb_lines[(bus, dev)] = info['Raw']
    if not devices:
        print("No USB devices found.")
        return
    last_bus = None
    seen = set()  # Track (bus, dev) pairs already printed
    for d in devices:
        bus = d.get('Bus', '-')
        dev = d.get('Device', '-')
        iface = d.get('Interface', '-')
        key = (bus, dev)
        if key in seen:
            continue  # Skip duplicate device
        seen.add(key)
        lsusb_line = lsusb_lines.get(key)
        # Modern, professional markers
        BUS_MARK = f"\033[1;36m\u25A0 BUS {bus} \u25A0\033[0m" if color else f"=== BUS {bus} ==="
        ROOT_HUB_MARK = f"\033[1;35m\u25B2 ROOT HUB\033[0m" if color else "[ROOT HUB]"
        PORT_MARK = f"\033[1;33m\u25B6 PORT\033[0m" if color else "[PORT]"
        DEVICE_MARK = f"\033[1;32m\u25CF DEVICE\033[0m" if color else "[DEVICE]"
        # Print bus header
        if bus != last_bus:
            print(f"\n{BUS_MARK}")
            last_bus = bus
        indent = "    " if iface != '-' else "  "
        # Identify root hub
        is_root_hub = False
        if lsusb_line and 'root hub' in lsusb_line.lower():
            is_root_hub = True
        if lsusb_line:
            if is_root_hub:
                dev_str = f"{indent}{ROOT_HUB_MARK}  {lsusb_line}"
            else:
                dev_str = f"{indent}{DEVICE_MARK}  {lsusb_line}"
            print(dev_str)
            # Only print port if not already in lsusb_line
            port = d.get('Port', None)
            if port and port != '-' and f"Port {port}" not in lsusb_line:
                print(f"{indent}{PORT_MARK}  Port: {port}")
        else:
            port = d.get('Port', '-')
            cls = d.get('Class', '-')
            driver = d.get('Driver', '-')
            speed = d.get('Speed (Mbps)', '-')
            category = d.get('Category', '-')
            dev_str = f"{indent}{PORT_MARK}  Port {port} -> {DEVICE_MARK}  Device {dev}"
            print(dev_str)
            print(f"{indent}   Class: {cls}, Driver: {driver}, Speed: {speed} Mbps, Category: {category}")
        # Optionally, print extra details from -v
        if show_extra:
            prod_name = full_details.get(key, {}).get('ProductName', '')
            manuf = full_details.get(key, {}).get('Manufacturer', '')
            prod = full_details.get(key, {}).get('Product', '')
            serial = full_details.get(key, {}).get('Serial', '')
            if prod_name:
                print(f"{indent}   \033[1;37mProduct Name:\033[0m {prod_name}" if color else f"{indent}   Product Name: {prod_name}")
            if manuf:
                print(f"{indent}   \033[1;37mManufacturer:\033[0m {manuf}" if color else f"{indent}   Manufacturer: {manuf}")
            if prod:
                print(f"{indent}   \033[1;37mProduct:\033[0m {prod}" if color else f"{indent}   Product: {prod}")
            if serial:
                print(f"{indent}   \033[1;37mSerial:\033[0m {serial}" if color else f"{indent}   Serial: {serial}")

def main():
    check_lsusb_installed()
    parser = argparse.ArgumentParser(description='USB Device Tree Viewer')
    parser.add_argument('--no-color', action='store_true', help='Disable color output')
    parser.add_argument('--no-extra', action='store_true', help='Hide extra details from lsusb -v')
    args = parser.parse_args()
    tree = get_usb_devices()
    devices = parse_usb_tree(tree)
    lsusb_out = get_lsusb_details()
    details = parse_lsusb_details(lsusb_out)
    lsusb_v_out = get_lsusb_full_details()
    full_details = parse_lsusb_full_details(lsusb_v_out)
    print_tree(devices, details, full_details, show_extra=not args.no_extra, color=not args.no_color)

if __name__ == "__main__":
    main()
