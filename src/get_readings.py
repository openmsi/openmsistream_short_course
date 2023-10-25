"""Prints a single temperature and humidity reading for a given device"""

# imports
import asyncio
from argparse import ArgumentParser
from bleak import BleakClient
from sensorpush import sensorpush as sp


async def print_temp_humidity(device_address):
    """Connect to a device and get a temperature an humidity reading to print"""
    client = BleakClient(device_address)
    await client.connect()
    temp_c, hum = await asyncio.gather(
        sp.read_temperature(client), sp.read_humidity(client)
    )
    print(f"temperature = {temp_c} degC")
    print(f"humidity = {hum} %")
    await client.disconnect()


def get_args():
    """Return a Namescape of arguments to use for running the script"""
    parser = ArgumentParser()
    parser.add_argument(
        "device_address",
        help="The address (MAC or UUID) of the SensorPush device to connect to",
    )
    return parser.parse_args()


def main():
    """Send args to print function"""
    args = get_args()
    asyncio.run(print_temp_humidity(args.device_address))


if __name__ == "__main__":
    main()
