"""Writes out a series of CSV files with timestamped temperature and humidity readings
from a given device at a given interval
"""

# imports
import asyncio
from datetime import datetime
from bleak import BleakClient
from bleak.exc import BleakDeviceNotFoundError
from openmsitoolbox import (
    ControlledProcessSingleThread,
    Runnable,
    OpenMSIArgumentParser,
)
from openmsitoolbox.argument_parsing.parser_callbacks import positive_int
from sensorpush import sensorpush as sp


class SensorPushArgumentParser(OpenMSIArgumentParser):
    """ArgumentParser for SensorPush activities"""

    ARGUMENTS = {
        **OpenMSIArgumentParser.ARGUMENTS,
        "device_address": [
            "positional",
            {
                "help": "The address (MAC or UUID) of the SensorPush device to connect to"
            },
        ],
        "sampling_interval": [
            "optional",
            {
                "help": (
                    "How often samples should be read from the sensor and written out "
                    "to CSV files (seconds). Inexact, as there is some lag in "
                    "communicating with sensors."
                ),
                "default": 10,
            },
        ],
        "n_connection_retries": [
            "optional",
            {
                "help": "Number of retries to use for connecting to a SensorPush device",
                "default": 5,
                "type": positive_int,
            },
        ],
    }


class TemperatureHumidityCSVWriter(ControlledProcessSingleThread, Runnable):
    """Writes out CSV files of timestamped temperature/humidity measurements from
    a SensorPush HT.w device on a given time interval until the user shuts it down
    """

    ARGUMENT_PARSER_TYPE = SensorPushArgumentParser
    PRINT_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
    FILENAME_TIMESTAMP_FORMAT = "%Y-%m-%d-%H-%M-%S"

    def __init__(
        self,
        device_address,
        output_dir,
        sampling_interval,
        streamlevel,
        n_connection_retries,
    ):
        super().__init__(streamlevel=streamlevel)
        self.device_address = device_address
        self.output_dir = output_dir
        self.sampling_interval = sampling_interval
        self.n_connection_retries = n_connection_retries
        self.start_time = datetime.now()
        self.n_files_written = 0
        self.last_reading_time = None

    async def get_reading(self):
        """Connect to the SensorPush device and return new temperature and humidity
        measurements
        """
        self.logger.debug(
            f"Connecting to SensorPush device at {self.device_address}..."
        )
        client = BleakClient(self.device_address)
        for iretry in range(self.n_connection_retries):
            try:
                await client.connect()
                break
            except BleakDeviceNotFoundError as exc:
                if iretry < self.n_connection_retries:
                    msg = (
                        f"Failed a connection attempt to {self.device_address}. "
                        f"Retrying ({self.n_connection_retries-iretry} left)..."
                    )
                    self.logger.debug(msg)
                else:
                    errmsg = (
                        f"Failed to connect to device after {self.n_connection_retries} "
                        "retries!"
                    )
                    self.logger.error(errmsg, exc_info=exc, reraise=True)
        self.logger.debug("Connected!")
        temp_c, hum = await asyncio.gather(
            sp.read_temperature(client), sp.read_humidity(client)
        )
        await client.disconnect()
        return temp_c, hum

    def _run_iteration(self):
        """If it's been enough time since the last reading was taken, take another"""
        if self.last_reading_time is not None and (
            (datetime.now() - self.last_reading_time).total_seconds()
            < self.sampling_interval
        ):
            return
        temp_c, hum = asyncio.run(self.get_reading())
        self.last_reading_time = datetime.now()
        csv_filename = (
            f"readings_{self.device_address}_"
            f"{datetime.strftime(self.last_reading_time,self.FILENAME_TIMESTAMP_FORMAT)}"
            ".csv"
        )
        csv_filepath = self.output_dir / csv_filename
        reading_csv_str = ",".join([str(temp_c), str(hum)])
        self.logger.debug(f"Writing reading of {temp_c} degC, {hum}% to {csv_filename}")
        with open(csv_filepath, "w") as out_fp:
            out_fp.write(reading_csv_str)
        self.n_files_written+=1

    def _on_check(self):
        """Print the number of files written out so far when the program is checked"""
        msg = (
            f"{self.n_files_written} file{'s' if self.n_files_written!=1 else ''} "
            f"written since {datetime.strftime(self.start_time,self.PRINT_TIMESTAMP_FORMAT)}"
        )
        self.logger.info(msg)

    def _on_shutdown(self):
        """Print the total number of files written out when the program is quit"""
        msg = (
            f"{self.n_files_written} file{'s' if self.n_files_written!=0 else ''} "
            f"written from {datetime.strftime(self.start_time,self.PRINT_TIMESTAMP_FORMAT)} "
            f"to {datetime.strftime(datetime.now(),self.PRINT_TIMESTAMP_FORMAT)}"
        )
        self.logger.info(msg)

    @classmethod
    def get_command_line_arguments(cls):
        super_args, super_kwargs = super().get_command_line_arguments()
        super_args.pop(super_args.index("logger_file_level"))
        cl_args = [
            *super_args,
            "device_address",
            "output_dir",
            "sampling_interval",
            "n_connection_retries",
        ]
        cl_kwargs = {**super_kwargs}
        return cl_args, cl_kwargs

    @classmethod
    def run_from_command_line(cls, args=None):
        parser = cls.get_argument_parser()
        args = parser.parse_args(args=args)
        csv_writer = cls(
            args.device_address,
            args.output_dir,
            args.logger_stream_level,
            args.sampling_interval,
            args.n_connection_retries,
        )
        csv_writer.run()


def main(args=None):
    """Run the TemperatureHumidityCSVWriter"""
    TemperatureHumidityCSVWriter.run_from_command_line(args)


if __name__ == "__main__":
    main()


# async def get_temp_humidity(connected_client):
#     """Connect to a device and get a temperature an humidity reading to print"""
#     client = BleakClient(device_address)
#     await client.connect()
#     temp_c = await sp.read_temperature(client)
#     hum = await sp.read_humidity(client)
#     print(f"temperature = {temp_c} degC")
#     print(f"humidity = {hum} %")
#     await client.disconnect()
#
#
# async def write_reading_csvs(device_address):
#     client = BleakClient(device_address)
#     await client.connect()
#
#     await client.disconnect()
#
#
# def get_args():
#     """Return a Namescape of arguments to use for running the script"""
#     parser = ArgumentParser()
#     parser.add_argument(
#         "device_address",
#         help="The address (MAC or UUID) of the SensorPush device to connect to",
#     )
#     return parser.parse_args()
#
#
# def main():
#     """Send args to print function"""
#     args = get_args()
#     asyncio.run(print_temp_humidity(args.device_address))
