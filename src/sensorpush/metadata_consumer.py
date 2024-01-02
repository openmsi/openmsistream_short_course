"""Read metadata message from a topic and print them out"""

# imports
import json
from openmsitoolbox import Runnable
from openmsistream.kafka_wrapper.controlled_message_processor import (
    ControlledMessageProcessor,
)
from openmsistream.utilities.argument_parsing import OpenMSIStreamArgumentParser


class MetadataPrinter(ControlledMessageProcessor, Runnable):
    """Connect a group of consumers to a topic, read metadata messages, and print them
    out as they are consumed

    Args:
        config_path (pathlib.Path): path to a config file containing at least "broker"
            and "consumer" sections
        topic_name (str): the name of the topic to read messages from
        kwargs (dict): other keyword arguments are passed to parent constructors
    """

    ARGUMENT_PARSER_TYPE = OpenMSIStreamArgumentParser

    def __init__(self, config_path, topic_name, **kwargs):
        super().__init__(config_path, topic_name, **kwargs)
        field_names = [
            "RELATIVE FILEPATH",
            "SIZE (bytes)",
            "CONSUMED FROM",
            "CONSUMED ON",
            "EXTRACTION TIMESTAMP",
        ]
        self.min_widths = [40, 12, 30, 12, 20]
        header_row = "    ".join(
            [
                field_name.ljust(min_width)
                for field_name, min_width in zip(field_names, self.min_widths)
            ]
        )
        self.logger.info(header_row)

    def _process_message(self, lock, msg, *args, **kwargs):
        try:
            val = msg.value()
            vdict = json.loads(val)
            fields = [
                vdict["relative_filepath"],
                str(vdict["size_in_bytes"]),
                vdict["consumed_from"],
                vdict["consumed_on"],
                vdict["metadata_extracted_at"],
            ]
            printmsg = "    ".join(
                [
                    field.ljust(min_width)
                    for field, min_width in zip(fields, self.min_widths)
                ]
            )
            with lock:
                self.logger.info(printmsg)
            return True
        except Exception as exc:
            self.logger.error(
                "Failed to process a message. Exception will be logged and skipped.",
                exc_info=exc,
            )
            return False

    def _on_check(self):
        msg = (
            f"Read {self.n_msgs_read} message{'s' if self.n_msgs_read!=1 else ''}, "
            f"processed {self.n_msgs_processed} message"
            f"{'s' if self.n_msgs_processed!=1 else ''} so far"
        )
        self.logger.info(msg)

    def _on_shutdown(self):
        super()._on_shutdown()
        msg = (
            f"Read {self.n_msgs_read} message{'s' if self.n_msgs_read!=1 else ''}, "
            f"processed {self.n_msgs_processed} message"
            f"{'s' if self.n_msgs_processed!=1 else ''}"
        )
        self.logger.info(msg)

    @classmethod
    def get_command_line_arguments(cls):
        superargs, superkwargs = super().get_command_line_arguments()
        args = [
            *superargs,
            "config",
            "topic_name",
            "download_regex",
            "consumer_group_id",
            "update_seconds",
        ]
        args.pop(args.index("logger_file_level"))
        args.pop(args.index("logger_file_path"))
        kwargs = {
            **superkwargs,
            "n_threads": 2,
        }
        return args, kwargs

    @classmethod
    def run_from_command_line(cls, args=None):
        parser = cls.get_argument_parser()
        args = parser.parse_args(args=args)
        metadata_printer = cls(
            args.config,
            args.topic_name,
            n_threads=args.n_threads,
            filepath_regex=args.download_regex,
            consumer_group_id=args.consumer_group_id,
            update_secs=args.update_seconds,
            streamlevel=args.logger_stream_level,
            filelevel=None,
            logger_file=None,
        )
        metadata_printer.run()


def main(args=None):
    """Run the MetadataPrinter"""
    MetadataPrinter.run_from_command_line(args)


if __name__ == "__main__":
    main()
