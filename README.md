# SensorPush Activity
Code utilities for the SensorPush-based streaming activity at the OpenMSIStream short course

The OpenMSIStream short course will involve an example of a streaming workflow using [SensorPush HT.w sensors](https://www.sensorpush.com/products/p/ht-w). Participants will use code in this repository (based on the [`sensorpush-bleak`](https://github.com/cryptomcgrath/sensorpush-bleak) library) to simplify the process of connecting to their devices using the [`Bleak`](https://bleak.readthedocs.io/en/latest/index.html) Bluetooth Low Energy (LE) client and retrieiving timestamped temperature and humidity data.

## Installation

Create and activate a new Conda environment:

    conda create -n sensorpush python=3.9
    conda activate sensorpush

Clone this repository, cd in to it, and then install the dependencies from the requirements file:

    pip install -r requirements.txt
