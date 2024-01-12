# SensorPush Activity

As an example of working with streaming data using OpenMSIStream, we'll be gathering live temperature and humidity readings from SensorPush devices in the room. This sheet is a reference for running the programs used in this activity.

## Dumping readings to a directory of CSV files

The first program will connect to your device, take readings at some regular interval (10 seconds by default) and write out one small csv file per reading. To run it from the directory containing this repo, type:

    python openmsistream_short_course/src/sensorpush/sensor_push_csv_writer.py [device_id] sensorpush_csv_files --name [sensor_name]

where `[device_id]` is the address of your device that you found during the set up phase, and `[sensor_name]` is a familiar name you'd like to use to identify your sensor (you could use your own first name, for example). Running that command will put the output in a new directory called `sensorpush_csv_files`. 

You can see other options by adding the "-h" flag. While the program is running, you can type "check" or "c" in the terminal window to see how many files have been written so far. You can quit the program by typing "quit" or "q" in the terminal.

## Producing CSV files to a topic using a DataFileUploadDirectory

The files that are written out can be added to a topic by running a standard Producer program pointed to the output directory you set in the previous step. In a new terminal window, type:

    DataFileUploadDirectory sensorpush_csv_files --config openmsistream_short_course/config_files/confluent_cloud_broker.config --topic_name sensorpush_readings --upload_existing

You can see other options available by adding the "-h" flag. While the program is running, you can type "c" in the terminal to see how many files have been uploaded, and you can shutthe program down by typing "q".

## Live-plotting data in the topic using a Stream Processor

There is also a Stream Processor program that will make a live-updated plot of the temperature and humidity data read back from the topic. To run that program, type:

    python openmsistream_short_course/src/sensorpush/sensor_push_stream_plotter.py --config openmsistream_short_course/config_files/confluent_cloud_broker.config --topic_name sensorpush_readings

You can see other options for running the code by adding the "-h" flag. Type "c" in the terminal while the program is running to see how many readings have been consumed from the topic, and type "q" to quit. When you quit the program you'll also need to close the window that it pops up with the plots in it.

Output from this program will be put in a new folder called "`SensorPushStreamPlotter_output`" in the current directory. It will have a .png of the final state of the plot window when you shut down the program.