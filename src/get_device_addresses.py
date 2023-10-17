"""Uses a BleakScanner to search for SensorPush HT devices and prints their names
and addresses.

Typical usage:
    python get_device_addresses.py
"""

# imports
import asyncio
from bleak import BleakScanner

# constants
DEFAULT_TIMEOUT = 5.0 # The amount of time to wait to recognize devices
SENSOR_NAME_START = "SensorPush HT.w" # The start of all SensorPush HT.w devices' names

async def main():
    """Discovers all Bluetooth LE devices, checks their names against the SensorPush
    pattern, and prints the addresses of any devices found
    """
    devices = await BleakScanner.discover(timeout=DEFAULT_TIMEOUT)
    n_discovered = 0
    for device in devices:
        if device.name and device.name.startswith(SENSOR_NAME_START):
            print(f"Found {device.name} device with address {device.address}")
            n_discovered+=1
    if n_discovered<1:
        msg = (
            f"No {SENSOR_NAME_START} devices discovered in {DEFAULT_TIMEOUT} seconds. "
            "Devices must be powered on, in range, and disconnected from all other "
            "bluetooth receivers (including the SensorPush mobile app)"
        )
        print(msg)
    else:
        print(f"Found {n_discovered} total {SENSOR_NAME_START} devices")

if __name__=="__main__":
    asyncio.run(main())
