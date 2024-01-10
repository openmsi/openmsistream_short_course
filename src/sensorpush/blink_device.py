"Make a specified SensorPush device blink its light (helps identify individual devices)"

# imports
import time
import asyncio
from argparse import ArgumentParser
from bleak import BleakClient

# constants
LED_CHARACTERISTIC_UUID = "EF09000C-11D6-42BA-93B8-9DD7EC090AA9"


async def blink_led(address, n_blinks):
    """Blink the LED on the SensorPush device at "address" "n_blinks" times.

    Args:
        address (str): The MAC or UUID address of the SensorPush device to connect to
        n_blinks (int): How many times to blink the LED before
    """
    print(f"Connecting to {address}....")
    async with BleakClient(address) as client:
        print(f"Connected to {address}! Blinking LED {n_blinks} times....")
        n_blinks_bytes = n_blinks.to_bytes(1, byteorder="little")
        await client.write_gatt_char(LED_CHARACTERISTIC_UUID, n_blinks_bytes)
        time.sleep(n_blinks)
        reset = 0
        reset_bytes = reset.to_bytes(1, byteorder="little")
        await client.write_gatt_char(LED_CHARACTERISTIC_UUID, reset_bytes)
        print(f"Disconnecting from {address}....")
    print("Done!")


def main():
    """Run the script to blink the device LED"""
    parser = ArgumentParser()
    parser.add_argument(
        "device_address",
        help="The address (MAC or UUID) of the SensorPush device to connect to",
    )
    parser.add_argument(
        "--n_blinks",
        type=int,
        default=10,
        help="How many times to blink the LED on the device",
    )
    args = parser.parse_args()
    if args.n_blinks < 0 or args.n_blinks > 127:
        raise ValueError(
            f"ERROR: n_blinks must be an int between 0 and 127 ({args.n_blinks} given)"
        )
    asyncio.run(blink_led(args.device_address, args.n_blinks))


if __name__ == "__main__":
    main()
