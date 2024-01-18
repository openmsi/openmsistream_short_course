"""Plot temperature/humidity measurements as they're received from a topic"""

# imports
from datetime import datetime
from io import BytesIO
from threading import Thread
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import animation
from openmsitoolbox import Runnable
from openmsistream import DataFileStreamProcessor
from argument_parser import SensorPushArgumentParser # pylint: disable=import-error
from sensor_push_csv_writer import SensorPushCSVWriter # pylint: disable=import-error


class SensorPushStreamPlotter(DataFileStreamProcessor, Runnable):
    """Makes and live-updates a plot of any temperature/humidity readings read
    from a topic while it's running
    """

    ARGUMENT_PARSER_TYPE = SensorPushArgumentParser

    def __init__(self, config_file, topic_name, **kwargs):
        super().__init__(config_file, topic_name, **kwargs)
        self.measurements_df = None
        self.fig, self.ax = plt.subplots(2, 1, sharex=True, figsize=(12.0, 9.0))
        self._format_plot()

    def update_plot(self, _):
        """Called as part of a FuncAnimation to update an animated plot based on the
        current state of the measurement dataframe
        """
        if self.measurements_df is None or len(self.measurements_df) < 1:
            return
        for axs in self.ax:
            axs.clear()
        self._format_plot()
        for dev_id in self.measurements_df["device_id"].unique():
            device_df = (
                self.measurements_df[self.measurements_df["device_id"] == dev_id]
            ).copy()
            device_df.sort_values("timestamp", inplace=True)
            timestamps = device_df["timestamp"]
            temps = device_df["temperature"]
            hums = device_df["humidity"]
            self.ax[0].plot(timestamps, temps, marker="o", label=dev_id)
            self.ax[1].plot(timestamps, hums, marker="o", label=dev_id)
        for axs in self.ax:
            axs.relim()
            axs.autoscale_view()
        n_devices = len(self.measurements_df["device_id"].unique())
        if n_devices > 0:
            self.ax[0].legend(
                loc="upper left", bbox_to_anchor=(1.0, 1.0), ncol=max(1,int(n_devices/8))
            )
        self.fig.tight_layout()

    def _format_plot(self):
        self.ax[0].set_title("Temperature measurements")
        self.ax[0].set_ylabel("temperature (deg C)")
        self.ax[1].set_title("Humidity measurements")
        self.ax[1].set_ylabel("humidity (%)")
        self.ax[1].set_xlabel("timestamp")

    def _process_downloaded_data_file(self, datafile, lock):
        filename_split = datafile.filename.split("_")
        dev_id = "_".join(filename_split[1:-1])
        timestamp = datetime.strptime(
            filename_split[-1][: -len(".csv")],
            SensorPushCSVWriter.FILENAME_TIMESTAMP_FORMAT,
        )
        data_line = BytesIO(datafile.bytestring).readline().decode().strip()
        temp, hum = [float(val) for val in data_line.split(",")]
        new_df = pd.DataFrame(
            [
                {
                    "device_id": dev_id,
                    "timestamp": timestamp,
                    "temperature": temp,
                    "humidity": hum,
                }
            ]
        )
        with lock:
            if self.measurements_df is None:
                self.measurements_df = new_df
            else:
                self.measurements_df = pd.concat(
                    [self.measurements_df, new_df], ignore_index=True
                )

    @classmethod
    def run_from_command_line(cls, args=None):
        parser = cls.get_argument_parser()
        args = parser.parse_args(args)
        init_args, init_kwargs = cls.get_init_args_kwargs(args)
        stream_plotter = cls(*init_args, **init_kwargs)
        processing_thread = Thread(target=stream_plotter.process_files_as_read)
        processing_thread.start()
        _ = animation.FuncAnimation(
            stream_plotter.fig, stream_plotter.update_plot, interval=500, save_count=100
        )
        plt.show()
        timestamp_string = datetime.strftime(
            datetime.now(), SensorPushCSVWriter.FILENAME_TIMESTAMP_FORMAT
        )
        stream_plotter.fig.savefig(
            stream_plotter._output_dir / f"plots_{timestamp_string}.png",
            bbox_inches="tight",
        )
        processing_thread.join()
        stream_plotter.close()
        msg = (
            f"Processed {stream_plotter.n_processed_files} file"
            f"{'s' if stream_plotter.n_processed_files!=1 else ''}."
        )
        if stream_plotter.n_processed_files > 0:
            msg += f" Up to {cls.N_RECENT_FILES} most recent shown below:\n\t"
            msg += "\n\t".join(
                [str(fp) for fp in stream_plotter.recent_processed_filepaths]
            )
        stream_plotter.logger.info(msg)


def main(args=None):
    """Run the StreamPlotter"""
    SensorPushStreamPlotter.run_from_command_line(args)


if __name__ == "__main__":
    main()
