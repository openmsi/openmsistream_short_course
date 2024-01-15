# Example Stream Processor (XRD Analysis)

This repository contains a fully-worked, deployment-ready stream processing application for an example XRD analysis. As demoed in the [XRD analysis notebook](https://github.com/openmsi/openmsistream_short_course/blob/main/notebooks/03_xrd_analysis.ipynb), the stream processor extracts regions of background-subtracted 1D XRD data containing candidate peaks, fits those segments of data with a background+peak(s) model, and uses SQLAlchemy to add the results to a SQL database.

## Put the files in a topic

If the data files still need to be added to the topic, you can produce them with the command:

    DataFileUploadDirectory xrd_example_data_files --config config_files/confluent_cloud_broker.config --topic_name bg_sub_xrd_files --upload_existing

Once you see that all four example files have been produced you can quit the program by typing "q".

## Running the example stream processor

You can run the example stream processor with the command:

    python src/xrd_analysis/xrd_analysis_stream_processor.py --config config_files/confluent_cloud_broker.config --topic_name bg_sub_xrd_files

That command will create an output sqlite db called "`xrd_analysis.sqlite`" and a standard StreamProcessor output directory called "`XRDAnalysisStreamProcessor_output`" in the current directory. Once all four files have been processed you can shut the program down by typing "q" in the terminal.

