"""Writes out a series of CSV files with timestamped temperature and humidity readings
from a given device at a given interval
"""

# imports
import asyncio
from datetime import datetime
from bleak import BleakClient
from bleak.exc import BleakDeviceNotFoundError
from openmsitoolbox import Runnable, ControlledProcessAsync
from sensorpush import sensorpush as sp

# pylint: disable=wrong-import-order, import-error
from argument_parser import SensorPushArgumentParser


class SensorPushCSVWriter(ControlledProcessAsync, Runnable):
    """Writes out CSV files of timestamped temperature/humidity measurements from
    a SensorPush HT.w device on a given time interval until the user shuts it down
    """

    #################### CONSTANTS ####################

    ARGUMENT_PARSER_TYPE = SensorPushArgumentParser
    PRINT_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
    FILENAME_TIMESTAMP_FORMAT = "%Y-%m-%d-%H-%M-%S"

    #################### PUBLIC METHODS ####################

    def __init__(
        self,
        device_address,
        output_dir,
        name,
        sampling_interval,
        n_connection_retries,
        **other_kwargs,
    ):
        super().__init__(**other_kwargs)
        self.device_address = device_address
        self.output_dir = output_dir
        self.name = name
        self.sampling_interval = sampling_interval
        self.n_connection_retries = n_connection_retries
        self.start_time = datetime.now()
        self.n_files_written = 0
        self._reading_queue = None
        self._client = None

    async def run_task(self):
        """Connect to the device and write out measurements as they come in"""
        self._reading_queue = asyncio.Queue()
        await self._connect_to_client()
        self.logger.info(
            f"Writing temperature/humidity readings every {self.sampling_interval} secs"
        )
        await asyncio.gather(self._enqueue_readings(), self._write_out_readings())

    #################### PRIVATE HELPER METHODS ####################

    def _check_for_client_and_reading_queue(self):
        """Logs and raises a RuntimeError if the client or reading queue haven't
        been initialized yet
        """
        if self._client is None:
            self.logger.error(
                "ERROR: client must be created first!", exc_type=RuntimeError
            )
        if self._reading_queue is None:
            self.logger.error(
                "ERROR: reading queue must be created first!", exc_type=RuntimeError
            )

    async def _write_out_readings(self):
        """While the process is running, get readings from the queue and write them
        out to CSV files
        """
        self._check_for_client_and_reading_queue()
        while self.alive:
            reading = await self._reading_queue.get()
            timestamp = reading[0]
            temp_c = reading[1]
            hum = reading[2]
            dev_name = self.name if self.name is not None else self.device_address
            csv_filename = (
                f"readings_{dev_name}_"
                f"{datetime.strftime(timestamp,self.FILENAME_TIMESTAMP_FORMAT)}"
                ".csv"
            )
            csv_filepath = self.output_dir / csv_filename
            reading_csv_str = ",".join([str(temp_c), str(hum)])
            self.logger.debug(
                f"Writing reading of {temp_c} degC, {hum}% to {csv_filename}"
            )
            with open(csv_filepath, "w") as out_fp:
                out_fp.write(reading_csv_str)
            self.n_files_written += 1

    async def _enqueue_readings(self):
        """While the process is running, get readings every sampling interval and add
        them to the reading queue
        """
        self._check_for_client_and_reading_queue()
        while self.alive:
            timestamp = datetime.now()
            temp_c, hum = await asyncio.gather(
                sp.read_temperature(self._client), sp.read_humidity(self._client)
            )
            self.logger.debug(f"Enqueing reading of {temp_c} degC, {hum}%")
            await self._reading_queue.put((timestamp, temp_c, hum))
            await asyncio.sleep(self.sampling_interval)

    async def _connect_to_client(self):
        """Connect to the bleak client"""
        self.logger.info(
            f"Connecting to SensorPush device at {self.device_address}..."
        )
        self._client = BleakClient(self.device_address)
        for iretry in range(self.n_connection_retries):
            try:
                await self._client.connect()
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
        batt_mv, _ = await sp.read_batt_info(self._client)
        self.logger.info(
            f"Connected to device {self.device_address} (battery power={batt_mv}V)"
        )

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
            f"{self.n_files_written} file{'s' if self.n_files_written!=1 else ''} "
            f"written from {datetime.strftime(self.start_time,self.PRINT_TIMESTAMP_FORMAT)} "
            f"to {datetime.strftime(datetime.now(),self.PRINT_TIMESTAMP_FORMAT)}"
        )
        self.logger.info(msg)

    async def _post_run(self):
        """Diconnect the client when the whole thing is done"""
        self._check_for_client_and_reading_queue()
        await self._client.disconnect()

    #################### CLASS METHODS ####################

    @classmethod
    def get_command_line_arguments(cls):
        super_args, super_kwargs = super().get_command_line_arguments()
        super_args.pop(super_args.index("logger_file_level"))
        super_args.pop(super_args.index("logger_file_path"))
        super_args.pop(super_args.index("update_seconds"))
        cl_args = [
            *super_args,
            "device_address",
            "output_dir",
            "name",
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
            args.name,
            args.sampling_interval,
            args.n_connection_retries,
            streamlevel=args.logger_stream_level,
        )
        asyncio.run(csv_writer.run_loop())


def main(args=None):
    """Run the SensorPushCSVWriter"""
    SensorPushCSVWriter.run_from_command_line(args)


if __name__ == "__main__":
    main()
