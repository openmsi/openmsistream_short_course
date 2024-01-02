"""Uses a BleakScanner to search for SensorPush HT devices and prints their names
and addresses.

Typical usage:
    python get_device_addresses.py --timeout 60 --all
"""

# imports
import asyncio
from argparse import ArgumentParser
from bleak import BleakScanner

# constants
DEFAULT_TIMEOUT = 30.0  # The amount of time to wait to recognize devices (secs)


class SensorPushListener:
    """Discovers Bluetooth LE devices, checks their names against the SensorPush
    pattern, and prints the addresses of any devices found within the timeout
    (or stops early when the first matching device is found)

    Arguments:
        stop_early:
            If True, the program will stop when the first matching device is found
        timeout:
            The amount of time to wait to discover devices
    """

    SENSOR_NAME_START = (
        "SensorPush HT.w"  # The start of all SensorPush HT.w devices' names
    )

    def __init__(self, stop_early=True, timeout=DEFAULT_TIMEOUT):
        self.stop_early = stop_early
        self.timeout = timeout
        self.addresses_found = set()
        self.lock = asyncio.Lock()
        self.stop_event = None

    async def device_callback(self, device, _):
        """Checks if a device name matches the expected pattern, and sets the stop event
        if one is found (and the program should stop early)
        """
        async with self.lock:
            if device.name and device.name.startswith(self.SENSOR_NAME_START) and device.address not in self.addresses_found:
                print(f"Found {device.name} device with address {device.address}")
                self.addresses_found.add(device.address)
                if self.stop_early:
                    self.stop_event.set()

    async def print_device_addresses(self):
        """Prints the addresses of any SensorPush devices found within the timeout,
        plus a summary message at the end
        """
        self.stop_event = asyncio.Event()
        async with BleakScanner(self.device_callback):
            try:
                await asyncio.wait_for(self.stop_event.wait(),timeout=self.timeout)
            except asyncio.TimeoutError:
                pass
        if len(self.addresses_found) < 1:
            msg = (
                f"No {self.SENSOR_NAME_START} devices discovered in {DEFAULT_TIMEOUT} "
                "seconds. Devices must be powered on, in range, and disconnected from "
                "all other Bluetooth receivers (including the SensorPush mobile app)"
            )
            print(msg)
        elif not self.stop_early:
            print(
                f"Found {len(self.addresses_found)} total {self.SENSOR_NAME_START} devices"
            )


def get_args():
    """Returns a namespace of command line arguments for running the script"""
    parser = ArgumentParser()
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"How long to wait to find devices, in seconds (default={DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Add this flag to always wait for the whole timeout to find devices",
    )
    args = parser.parse_args()
    return args


def main():
    """Runs the class defined above as a script from command line arguments"""
    args = get_args()
    listener = SensorPushListener((not args.all), args.timeout)
    asyncio.run(listener.print_device_addresses())


if __name__ == "__main__":
    main()
