# USB View

This tool is a simple Python program that shows all your USB devices on Linux. It uses the `lsusb` command to display detailed information about each USB device, like its speed, type, driver, and manufacturer. It presents this information in a clear, colored tree format.

## Features

- **Tree-style output**: Clearly shows the hierarchy of USB buses, root hubs, ports, and devices.
- **Color-coded and Unicode markers**: Visually distinguish BUS, ROOT HUB, PORT, and DEVICE for easy reading (with fallback to plain text if color is not available).
- **Detailed device info**: Includes speed, class, driver, vendor, product name, manufacturer, and serial number (where available).
- **No dependencies on workspace files**: Standalone script, only requires Python 3 and `lsusb`.
- **Command-line options**:
  - `--no-color`: Disable color output.
  - `--no-extra`: Hide extra details from `lsusb -v`.

## Requirements

- Linux system with Python 3
- `lsusb` utility (usually provided by the `usbutils` package)
- (Optional) `colorama` Python package for best color support: `pip install --user colorama`

## Usage

```sh
python3 usb_list.py [--no-color] [--no-extra]
```

- By default, the script will display a colorized, detailed tree of all USB devices.
- Use `--no-color` for plain text output (useful for logs or non-color terminals).
- Use `--no-extra` to hide extra details (manufacturer, product, serial) for a more compact view.

## Example Output

```
=== BUS 001 ===
  [ROOT HUB]  Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
  [PORT]  Port: 001
     Product Name: Linux Foundation 2.0 root hub
     Manufacturer: Linux 6.14.6-arch1-1 xhci-hcd
     Product: xHCI Host Controller
     Serial: 0000:00:14.0
    [DEVICE]  Bus 001 Device 002: ID 25a7:fa23 Areson Technology Corp 2.4G Receiver
    [PORT]  Port: 001
       Product Name: Areson Technology Corp 2.4G Receiver
       Manufacturer: Compx
       Product: 2.4G Receiver
       Serial: 0
```

## How It Works

- The script parses the output of `lsusb -t` to build the USB device tree and extract bus, port, device, class, driver, and speed information.
- It uses `lsusb` and `lsusb -v` to enrich device information with vendor, product, manufacturer, and serial number.
- Color and Unicode symbols are used for a modern, professional look (with fallback to plain text if color is not available).

## Customization

- To add more vendor names, expand the `USB_VENDORS` dictionary in the script.
- The script can be further extended to support filtering, exporting, or more advanced formatting.

## License

This script is provided as-is, without warranty. You are free to use, modify, and distribute it.

---

Inspired by the Windows USBView tool, but designed for Linux and modern terminals.
