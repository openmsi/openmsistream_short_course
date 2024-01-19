# imports
import datetime
from io import BytesIO
from threading import Thread
from matplotlib import animation
import matplotlib.pyplot as plt
from openmsistream import DataFileStreamProcessor


class SensorPushStreamPlotter(DataFileStreamProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fig, self.ax = plt.subplots(figsize=(10.0, 5.0))
        self.datasets = {}

    def make_plot(self,frame_number):
        if len(self.datasets)<1:
            return
        self.ax.clear()
        for dev_id, point_list in self.datasets.items():
            point_list = sorted(point_list, key=lambda x: x[0])
            xvals = [p[0] for p in point_list]
            yvals = [p[1] for p in point_list]
            self.ax.plot(xvals, yvals, marker=".", label=dev_id)
        self.ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0))
        self.ax.set_xlabel("timestamp")
        self.ax.set_ylabel("temp (degC)")
        self.fig.tight_layout()

    def _process_downloaded_data_file(self, datafile, lock):
        filename = datafile.filename
        filename_split = filename.split("_")
        dev_id = "_".join(filename_split[1:-1])
        # if dev_id!="maggie":
        #     return
        timestamp_txt = filename_split[-1][: -len(".csv")]
        timestamp = datetime.datetime.strptime(timestamp_txt, "%Y-%m-%d-%H-%M-%S")
        with lock:
            if dev_id not in self.datasets:
                self.datasets[dev_id] = []
        line = BytesIO(datafile.bytestring).readline().decode()
        temp = float(line.split(",")[0])
        self.datasets[dev_id].append((timestamp, temp))

    @classmethod
    def run_from_command_line(cls, args):
        parser = cls.get_argument_parser()
        parsed_args = parser.parse_args(args)
        init_args, init_kwargs = cls.get_init_args_kwargs(parsed_args)
        plotter = SensorPushStreamPlotter(*init_args, **init_kwargs)
        plotter_thread = Thread(target=plotter.process_files_as_read)
        plotter_thread.start()
        _ = animation.FuncAnimation(
            plotter.fig, plotter.make_plot, interval=1000, save_count=100
        )
        plt.show()
        plotter_thread.join()


def main(args=None):
    SensorPushStreamPlotter.run_from_command_line(args)


if __name__ == "__main__":
    main()
