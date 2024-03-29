# OpenMSIStream Short Course

Notebooks, code, and other files needed for the OpenMSIStream Short Course taking place on the Johns Hopkins University campus on January 18th & 19th, 2024. For help beyond this repository, the [official OpenMSIStream documentation](https://openmsistream.readthedocs.io/en/latest/index.html) is hosted on readthedocs.

Please get started by working through the steps described in the [setup cheat sheet](https://github.com/openmsi/openmsistream_short_course/blob/main/cheat_sheets/01_setup_for_activities.md).

Below are details on what you can find in this repository.

## cheat_sheets

This folder holds three markdown documents listing precise commands to run. 

The first ("setup_for_activities") has instructions for getting your environment set up. You should work through what's described there *before the start of the afternoon session* on the first day of the course.

The second document ("sensorpush_activity") has details on the programs we'll run during the SensorPush activity, for the second half of the afternoon on the first day. You don't need any further set up for that, it's just the commands we'll run together during that activity.

The third document ("xrd_analysis") lists commands you can use to upload files to the example XRD analysis topic and run the example XRDAnalysisStreamProcessor program.

The fourth document("openmsistream_cheatsheet") provides comprehensive guidance on utilizing the two primary OpenMSIStream modules for data consumption and production: DataFileDownloadDirectory and DataFileUploadDirectory. The document delves into the intricacies of running the programs, configuring files, and interpreting the required arguments.








## config_files

This folder holds some config files we'll need to run OpenMSIStream programs.

## notebooks

This folder has three Jupyter notebooks in it. The first ("local_producer") demonstrates two different ways to get files into topics using Producer-side programs. The second ("consumers") demonstrates three different Consumer-side applications. The third (xrd_analysis) is an example analysis of some background-subtracted 1-D x-ray diffraction data. We'll work through all of these notebooks together.

## src

This folder has more formal Python code in it. The "sensorpush" folder has code for working with SensorPush devices, and the "xrd_analysis" folder has code used in the XRD data example analysis. You can use any of this code as reference, but we won't need to edit it directly during the course.

## xrd_example_data_files

This folder has four example data files in it. The data are background-subtracted 1D X-ray diffraction (XRD) spectra. These files are used in the example XRD Analysis that we'll go over on the second day of the course.

## xrd_example_output

This folder has a single SQLite database file in it. That database is an example of the output you should get from running the example XRD analysis, whether in the third notebook or using the example XRDAnalysisStreamProcessor. It's only here for your reference.
