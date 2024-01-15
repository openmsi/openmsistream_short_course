"""A stream processor to analyze background-subtracted XRD data, automatically extract
segments of data containing candidate peaks, fit background+pseudo-Voigt peaks to those
segments, and centralize all of the results in a SQL DB
"""

# imports
import threading
from io import BytesIO
import sqlalchemy as sqa
from sqlalchemy.orm import scoped_session, sessionmaker
import pandas as pd
from openmsistream import DataFileStreamProcessor

# pylint: disable=import-error
from utils import get_raw_file_name

# pylint: disable=import-error
from analysis import get_peak_segments, get_segment_peak_fit

# pylint: disable=import-error
from sql_tables import (
    ORMBase,
    DataSet,
    DataPoint,
    DataSegment,
    CandidatePeak,
    SegmentFit,
    Background,
    FittedPeak,
)


class XRDAnalysisStreamProcessor(DataFileStreamProcessor):
    """Process background-subtracted XRD files from streams to a SQL DB of analysis
    results
    """

    def __init__(
        self, config, topic_name, connection_string, drop_existing=False, **kwargs
    ):
        super().__init__(config, topic_name, **kwargs)
        self._engine = sqa.create_engine(connection_string)
        self._scoped_session = scoped_session(sessionmaker(bind=self._engine))
        self._sessions_by_thread_id = {}
        if drop_existing:
            self.logger.info(
                f"Dropping and recreating all tables in {connection_string}"
            )
            ORMBase.metadata.drop_all(bind=self._engine)
        ORMBase.metadata.create_all(bind=self._engine)

    def add_datafile_to_db(self, datafile, session):
        """Add the given datafile to the DB using the given session. This code is almost
        completely copy/pasted from the analysis notebook.

        Args:
            datafile (openmsistream.data_file_io.DownloadDataFile): The data file that's
                been read from the topic
            session (sqlalchemy.orm.session.Session): The SQLAlchemy Session that should
                be used to add entries for the file (maintains multithreading capability)
        """
        datafile_as_read = BytesIO(datafile.bytestring)
        dataset_entry = DataSet(
            file_name=datafile.filename,
            raw_file_name=get_raw_file_name(datafile_as_read),
        )
        session.add(dataset_entry)
        session.commit()
        dataset_id = dataset_entry.ID
        # Read the file into a dataframe and add DataPoint entries for all of its points
        xrd_df = pd.read_csv(datafile_as_read, skiprows=2, names=["angle", "counts"])
        for _, row in xrd_df.iterrows():
            datapoint_entry = DataPoint(
                dataset_id=dataset_id, angle=row["angle"], counts=row["counts"]
            )
            session.add(datapoint_entry)
        session.commit()
        # Identify segments containing candidate peaks
        peak_segments = get_peak_segments(xrd_df)
        for peak_segment in peak_segments:
            # Add an entry for the segment
            segment_entry = DataSegment(
                dataset_id=dataset_id,
                min_angle=peak_segment["min"],
                max_angle=peak_segment["max"],
            )
            session.add(segment_entry)
            session.commit()
            segment_id = segment_entry.ID
            # And entries for the candidate peaks
            for cand_peak_angle in peak_segment["peak_angles"]:
                candidate_peak_entry = CandidatePeak(
                    segment_id=segment_id, angle=cand_peak_angle
                )
                session.add(candidate_peak_entry)
            session.commit()
            # Perform the fit to the data segment and get the peak components of the model
            fit_result = get_segment_peak_fit(xrd_df, peak_segment)
            fit_summary = fit_result.summary()
            pseudo_voigt_components = []
            for component in fit_result.model.components:
                if component.prefix.startswith("voigt"):
                    pseudo_voigt_components.append(component)
            # Add an entry for the result of the fit
            segment_fit_entry = SegmentFit(
                segment_id=segment_id,
                method=fit_summary["method"],
                ndata=fit_summary["ndata"],
                chisqr=fit_summary["chisqr"],
                redchi=fit_summary["redchi"],
                rsquared=fit_summary["rsquared"],
                nfev=fit_summary["nfev"],
                aborted=fit_summary["aborted"],
                success=fit_summary["success"],
                message=fit_summary["message"],
            )
            session.add(segment_fit_entry)
            # Add an entry for the background portion of the fit
            background_fit_entry = Background(
                segment_id=segment_id,
                init_slope=fit_summary["init_values"]["linear_slope"],
                init_intercept=fit_summary["init_values"]["linear_intercept"],
                fitted_slope=fit_summary["best_values"]["linear_slope"],
                fitted_intercept=fit_summary["best_values"]["linear_intercept"],
                slope_stderr=fit_result.params["linear_slope"].stderr,
                intercept_stderr=fit_result.params["linear_intercept"].stderr,
            )
            session.add(background_fit_entry)
            # Add entries for each peak found
            for peak_comp in pseudo_voigt_components:
                prefix = peak_comp.prefix
                peak_fit_entry = FittedPeak(
                    segment_id=segment_id,
                    init_amplitude=fit_summary["init_values"][f"{prefix}amplitude"],
                    init_center=fit_summary["init_values"][f"{prefix}center"],
                    init_sigma=fit_summary["init_values"][f"{prefix}sigma"],
                    init_fraction=fit_summary["init_values"][f"{prefix}fraction"],
                    fitted_amplitude=fit_summary["best_values"][f"{prefix}amplitude"],
                    fitted_center=fit_summary["best_values"][f"{prefix}center"],
                    fitted_sigma=fit_summary["best_values"][f"{prefix}sigma"],
                    fitted_fwhm=2.0 * fit_summary["best_values"][f"{prefix}sigma"],
                    fitted_fraction=fit_summary["best_values"][f"{prefix}fraction"],
                    amplitude_stderr=fit_result.params[f"{prefix}amplitude"].stderr,
                    center_stderr=fit_result.params[f"{prefix}center"].stderr,
                    sigma_stderr=fit_result.params[f"{prefix}sigma"].stderr,
                    fraction_stderr=fit_result.params[f"{prefix}fraction"].stderr,
                )
                session.add(peak_fit_entry)
            session.commit()

    def _process_downloaded_data_file(self, datafile, lock):
        "Add the datafile to the DB"
        try:
            thread_id = threading.get_ident()
            if thread_id not in self._sessions_by_thread_id:
                with lock:
                    self._sessions_by_thread_id[thread_id] = self._scoped_session()
            session = self._sessions_by_thread_id[thread_id]
            self.add_datafile_to_db(datafile, session)
        except Exception as exc:
            return exc
        return None

    @classmethod
    def run_from_command_line(cls, args=None):
        "Run the stream processor"
        parser = cls.get_argument_parser()
        parser.add_argument(
            "--connection_string",
            default="sqlite:///xrd_analysis.sqlite",
            help=(
                "The SQLAlchemy connection string for connecting to the output DB "
                "(default = 'sqlite:///xrd_analysis.sqlite')"
            ),
        )
        parser.add_argument(
            "--drop_existing",
            action="store_true",
            help="Add this flag to drop any existing output tables in the database",
        )
        args = parser.parse_args(args)
        stream_processor = XRDAnalysisStreamProcessor(
            args.config,
            args.topic_name,
            args.connection_string,
            drop_existing=args.drop_existing,
            streamlevel=args.logger_stream_level,
            filelevel=args.logger_file_level,
            logger_file=args.logger_file_path,
            consumer_group_id=args.consumer_group_id,
            update_secs=args.update_seconds,
            mode=args.mode,
            filepath_regex=args.download_regex,
            output_dir=args.output_dir,
            n_threads=args.n_threads,
        )
        (
            n_msgs_read,
            n_msgs_processed,
            n_files_processed,
            recent_filepaths,
        ) = stream_processor.process_files_as_read()
        msg = (
            f"Read {n_msgs_read} msgs, processed {n_msgs_processed} msgs and "
            f"{n_files_processed} files. Up to {cls.N_RECENT_FILES} most recent:\n\t"
        )
        msg += "\n\t".join([str(filepath) for filepath in recent_filepaths])
        stream_processor.logger.info(msg)

    def _on_shutdown(self):
        for session in self._sessions_by_thread_id.values():
            session.close()
        return super()._on_shutdown()


def main(args=None):
    "Run the XRDAnalysisStreamProcessor"
    XRDAnalysisStreamProcessor.run_from_command_line(args)


if __name__ == "__main__":
    main()
