# SensorPush Activity
Code utilities for the SensorPush-based streaming activity at the OpenMSIStream short course

The OpenMSIStream short course will involve an example of a streaming workflow using [SensorPush HT.w sensors](https://www.sensorpush.com/products/p/ht-w). Participants will use code in this repository (based on the [`sensorpush-bleak`](https://github.com/cryptomcgrath/sensorpush-bleak) library) to simplify the process of connecting to their devices using the [`Bleak`](https://bleak.readthedocs.io/en/latest/index.html) Bluetooth Low Energy (LE) client and retrieiving timestamped temperature and humidity data.

## Installation

Create and activate a new Conda environment:

    conda create -n sensorpush python=3.9
    conda activate sensorpush

Clone this repository, cd in to it, and then install the dependencies from the requirements file:

    pip install -r requirements.txt

## Programs

A brief overview of the programs in this repo

### get_device_addresses

Run with:
    
    python src/get_device_addresses.py 

This program will print the address of the first SensorPush HT.w device it identifies in the local BLE space. Run it with the -h flag to see other options, including waiting for a specified period of time and printing out every unique device found instead of stopping at the first.

### get_readings

Run with:

    python src/get_readings.py [device_address]

This program will print a single temperature and humidity reading from the sensor at `[device_address]` (which can be found using the program above).

### temperature_humidity_csv_writer

Run with:

    python src/temperature_humidity_csv_writer.py [device_address] [output_dir]

This program will connect to the device at `[device_address]` and write out a small CSV file of temperature (in degrees Celcius) and relative humidity (in %) to `[output_dir]` every five seconds until it's shut down by typing `q` or `quit` in the terminal. At any time, you can type `c` or `check` to see how many files have been written out so far.

Add `-h` to the command above to see other options, including using a custom sampling interval by giving the `--sampling_interval` argument.