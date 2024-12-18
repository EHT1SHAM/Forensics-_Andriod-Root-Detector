import subprocess
import re
import time
from pathlib import Path

def start_adb_server():
    try:
        subprocess.run(['adb', 'start-server'], capture_output=True, text=True, timeout=10)
        time.sleep(2)
    except subprocess.SubprocessError as e:
        print(f"Error starting ADB server: {e}")

def check_adb_connection():
    """Check if any Android device is connected via ADB"""
    try:
        start_adb_server()
        
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=10)
        devices = result.stdout.strip().split('\n')[1:]  # Skip first line (header)
        connected_devices = [d for d in devices if '\tdevice' in d]
        if connected_devices:
            print(f"Connected devices: {len(connected_devices)}")
            return True
        else:
            print("No devices connected.")
            return False
    except FileNotFoundError:
        print("Error: ADB not found. Please install Android SDK Platform Tools.")
        return False
    except subprocess.TimeoutExpired:
        print("Error: ADB command timed out. Please check your device connection.")
        return False
    except subprocess.SubprocessError as e:
        print(f"Error running ADB: {e}")
        return False

def check_root_indicators():
    """Check various indicators of root access"""
    root_indicators = {
        'Root Management Apps': {
            'command': 'adb shell pm list packages',
            'patterns': ['supersu', 'magisk', 'kingroot', 'oneclick', 'rootmaster']
        },
        'Su Binary': {
            'command': 'adb shell which su',
            'success_indicates_root': True,
            'additional_check': 'adb shell su -c id'
        },
        'Build Properties': {
            'command': 'adb shell getprop ro.build.tags',
            'patterns': ['test-keys']
        },
        'System RW': {
            'command': 'adb shell mount | grep system',
            'patterns': ['rw,']
        }
    }
    
    found_indicators = []
    
    for check_name, check_info in root_indicators.items():
        try:
            result = subprocess.run(check_info['command'].split(), 
                                    capture_output=True, text=True, timeout=5)
            
            if 'patterns' in check_info:
                for pattern in check_info['patterns']:
                    if pattern.lower() in result.stdout.lower():
                        found_indicators.append(f"{check_name} ({pattern})")
                        break
            elif check_info.get('success_indicates_root') and result.returncode == 0:
                if check_name == 'Su Binary':
                    try:
                        su_result = subprocess.run(check_info['additional_check'].split(),
                                                   capture_output=True, text=True, timeout=5)
                        if 'uid=0(root)' in su_result.stdout:
                            found_indicators.append(check_name)
                    except subprocess.SubprocessError:
                        pass
                else:
                    found_indicators.append(check_name)
                
        except subprocess.SubprocessError:
            print(f"Warning: Could not perform {check_name} check")
            continue
            
    return found_indicators

def FixFileName(str):
    str = str.split("successfully___")[-1] if "successfully___" in str else str
    return str

def fetch_installed_apps():
    try:
        result = subprocess.run(['adb', 'shell', 'pm', 'list', 'packages'], 
                                capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            apps = result.stdout.strip().split('\n')
            print("Installed apps:")
            for app in apps:
                print(app.replace('package:', ''))
        else:
            print("Failed to fetch installed apps.")
    except subprocess.SubprocessError as e:
        print(f"Error: {e}")

def partition_table_to_hex(input_text):
    """Convert partition table to hex dump format"""
    
    # Initialize output
    hex_dump = []
    
    # Skip header line
    lines = input_text.strip().split('\n')[1:]
    
    # Process each line
    for line in lines:
        parts = line.split()
        if len(parts) >= 6:  # Valid line should have device, size, used, etc
            device = parts[0]
            size = parts[1]
            mounted = parts[5]
            
            # Convert device name to hex
            dev_hex = ' '.join([f"{ord(c):02x}" for c in device])
            
            # Create hex dump line (16 bytes per line)
            while len(dev_hex) < 48:  # Pad to 16 bytes
                dev_hex += ' 00'
                
            # Add ASCII representation
            ascii_rep = ''.join([c if 32 <= ord(c) <= 126 else '.' for c in device])
            ascii_rep = ascii_rep.ljust(16, '.')
            
            # Format line with address, hex values and ASCII
            addr = len(hex_dump) * 16
            hex_line = f"{addr:08x}  {dev_hex}"
            
            hex_dump.append(hex_line)
    
    return '\n'.join(hex_dump)

def extract_partition_table():
    if not check_adb_connection():
        return

    try:
        start_adb_server()

        # Get device model for filename
        model_result = subprocess.run(['adb', 'shell', 'getprop', 'ro.product.model'], 
                                    capture_output=True, text=True, timeout=10)
        
        if model_result.returncode != 0:
            print(f"Error getting device model: {model_result.stderr}")
            model = "unknown_device"
        else:
            model = model_result.stdout.strip()
        
        model = re.sub(r'[^\w\-_\. ]', '_', model)
        model = model.replace(' ', '_')
        model = ''.join(c for c in model if c.isalnum() or c in ('_', '-', '.'))
        
        output_file = f"{model}_partition_table.txt"
        output_file = FixFileName(output_file)

        # Check if su exists
        su_check = subprocess.run(['adb', 'shell', 'which su'], 
                                capture_output=True, text=True, timeout=10)
        has_su = su_check.returncode == 0

        # Commands to try, prioritizing non-root methods if su is not available
        commands = []
        if has_su:
            commands.extend([
                ['adb', 'shell', 'su -c "cat /proc/partitions"'],
                ['adb', 'shell', 'su -c "df -h"'],
            ])
        
        # Non-root fallback commands
        commands.extend([
            ['adb', 'shell', 'df -h'],
            ['adb', 'shell', 'mount'],
            ['adb', 'shell', 'ls -l /dev/block/platform/*/by-name'],
            ['adb', 'shell', 'ls -l /dev/block/by-name/'],
            ['adb', 'shell', 'getprop ro.boot.slot_suffix'],
        ])

        for cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=True)
                
                if result.returncode == 0 and result.stdout.strip():
                    if "not found" not in result.stdout and "inaccessible" not in result.stdout:
                        with open(output_file, 'w') as f:
                            f.write(f"Command: {' '.join(cmd)}\n")
                            f.write("-" * 50 + "\n")
                            f.write(result.stdout)
                        
                        print(f"Partition information extracted and saved to {output_file}")
                        print("\nPartition Information Contents:")
                        print(partition_table_to_hex(result.stdout))
                        return
            except subprocess.SubprocessError:
                continue

        print("Failed to extract partition information: No partition data available")
    
    except subprocess.TimeoutExpired:
        print("Error: Command timed out")
    except subprocess.SubprocessError as e:
        print(f"Error: {e}")
    except IOError as e:
        print(f"Error reading/writing file: {e}")

def main_menu():
    while True:
        print("\nAndroid Device Analysis Tool")
        print("1. Check root status")
        print("2. Fetch names of installed apps")
        print("3. Extract partition table file")
        print("4. Exit")
        
        choice = input("Enter your choice (1-4): ")
        
        if choice == '1':
            check_root_status()
        elif choice == '2':
            fetch_installed_apps()
        elif choice == '3':
            extract_partition_table()
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

def check_root_status():
    if not check_adb_connection():
        print("\nNo Android device found or USB debugging not enabled.")
        print("Please ensure:")
        print("1. USB debugging is enabled in Developer Options")
        print("2. Device is connected via USB")
        print("3. You have confirmed the USB debugging prompt on your device")
        return
    
    print("\nChecking for root indicators...")
    print("This may take a few moments...\n")
    
    
    root_indicators = check_root_indicators()
    
    if root_indicators:
        print("Potential root indicators found:")
        for indicator in root_indicators:
            print(f"- {indicator}")
        print("\nDevice may be rooted, but further investigation is recommended.")
    else:
        print("No root indicators found.")
        print("Device appears to be unrooted, but root could still be hidden.")
    
    print("\nNote: This script provides indicators only and may not detect all root methods.")
    print("False positives and false negatives are possible.")

if __name__ == "__main__":
    main_menu()