# Android Device Analysis Tool

## Description

This Python script provides a set of tools for analyzing Android devices via ADB (Android Debug Bridge). It allows users to check for root indicators, fetch partition information, and list installed applications on a connected Android device.

## Features

1. Check root status of the connected Android device
2. Fetch and display partition table information
3. List names of installed applications

## Prerequisites

- Python 3.x
- ADB (Android Debug Bridge) installed and accessible from the command line
- An Android device with USB debugging enabled

## Installation

1. Ensure you have Python 3.x installed on your system.
2. Install ADB and add it to your system PATH.
3. Download the `main.py` script to your local machine.

## Usage

1. Connect your Android device to your computer via USB.
2. Enable USB debugging on your Android device (Settings > Developer options > USB debugging).
3. Run the script using Python:
4. Follow the on-screen menu to choose the desired operation:
- Option 1: Check root status
- Option 2: Fetch partition table
- Option 3: Fetch names of installed apps
- Option 4: Exit the program

## Functions

- `check_adb_connection()`: Verifies if an Android device is connected via ADB.
- `check_root_indicators()`: Checks for various indicators of root access on the device.
- `fetch_partition_table()`: Retrieves and displays partition information of the connected device.
- `fetch_installed_apps()`: Lists all installed applications on the device.

## Notes

- The root detection method provides indicators only and may not detect all root methods.
- False positives and false negatives are possible in root detection.
- Partition information is saved to a text file named after the device model.

## Troubleshooting

- If you encounter "ADB not found" errors, ensure ADB is properly installed and added to your system PATH.
- If the device is not detected, check USB debugging is enabled and the necessary drivers are installed.

## Author

Asad Khurshid 22i-1585
Ehtisham Ul Hassan 22i-1777
Manahil Choudhry I22-1728

## Version

1.0.0