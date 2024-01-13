# Setting Up for Hands-On Activities

We're going to be running a bunch of code together, and even writing some of our own, during this short course. This cheat sheet will walk you through setting up your computing environment to be able to participate in these activities.

## Installing miniconda

Conda is an open source package and environment manager that runs on Windows, Mac, and Linux operating systems. It's one of the easiest ways to intall open source software packages and manage sequestered computing environments on your machine. We'll do everything for these activities in a special-made Conda environment, so that you can complete these activities without needing to permanently install stuff on your own machine.

If you already have Anaconda or miniconda installed, you can skip to the next step. If not, you should install miniconda on your system. You can find instructions for how to do that in the docs on [this page](https://conda.io/projects/conda/en/latest/user-guide/install/index.html), and you can find installers for your system on [this page](https://docs.conda.io/projects/miniconda/en/latest/). Check [this section](https://docs.conda.io/projects/miniconda/en/latest/#quick-command-line-install) for the fastest way to install the latest version of miniconda on your system.

If you're on a Windows system, you should have access to a program called "Anaconda Powershell Prompt" that will act as your "terminal" for these activities. If you're on a Mac or Linux system, you can use the regular Terminal program. If you've installed Conda correctly, you should see "(base)" to the left of your terminal prompt when you open a new window. Once you see that, move on to the next step.

## Environment setup

Next we'll get an environment set up to install all of the code we'll run in this course.

### Creating a new environment

We'll install all of the dependencies for the software we'll use in this course in a new Conda environment. In a new terminal window, type:

    conda create -n openmsistream_short_course python=3.9 -y

This will create your new Conda environment. Then, activate your new environment with:

    conda activate openmsistream_short_course

You should then see "(openmsistream_short_course)" to the left of your terminal prompt, indicating the environment is active. **You will need to activate the environment in every terminal you open for this course.**

### Conda environment variable setup (WINDOWS ONLY)

If you're on a Windows system, you'll need to set an environment variable value to make sure that globally-installed DLL files can be found in your Cond environments. To do that, type:

    conda env config vars set CONDA_DLL_SEARCH_MODIFICATION_ENABLE=1
    conda deactivate
    conda activate openmsistream_short_course

to set the variable value and restart your environment.

### Install libsodium

Next we'll install the "libsodium" dependency using the Conda package manager. Type:

    conda install -c anaconda libsodium -y

and allow the installtion to completes.

### Install librdkafka (MAC ONLY)

If you're working on a Mac system, you'll need a *system-wide* install of librdkafka. You can check if it is already installed with:

    /usr/bin/xcodebuild -version

If it's not installed, the easiest way to install librdkafka is to use the "homebrew" package manager. You can find instructions for installing homebrew [here](https://brew.sh/). With homebrew installed, you can install librdkafka by typing:

    xcode-select --install
    brew install librdkafka

## Cloning and installing this repository

Now we're ready to get the code that's in this repository! To do that, create a new folder called "short_course" on your Desktop, navigate to it in your terminal window, and type:

    git clone https://github.com/openmsi/openmsistream_short_course.git

cd into the repository with:

    cd openmsistream_short_course

and install it by typing:

    pip install -r requirements.txt

## Setting Kafka cluster access environment variables

Using OpenMSIStream requires configuring access to a Kafka broker. There are a number of options for where that Kafka broker may be running (and you'll hear about some of them!) but for this course, we'll be using a managed cloud-based broker hosted on the commercial website Confluent Cloud. To connect to that broker, you'll need to set the following three environment variables on your machine:

- `KAFKA_CLUSTER_BOOTSTRAP_SERVERS`
- `KAFKA_CLUSTER_USERNAME`
- `KAFKA_CLUSTER_PASSWORD`

Values for these variables will be provided to you on the morning of the course.

## SensorPush devices

When you've completed to above steps, you can collect your SensorPush device and set up your access to it. The SensorPush is a Bluetooth Low Energy (BLE) device so you should be sure your laptop has bluetooth turned on. This activity is customized to interact only with the SensorPush HT.w device so if you are doing this activity outside the short course be sure to use the HT.w, second generation or newer model; you'll have to modify the code to work with other BLE devices. With your device nearby, cd to this repository and run the following command:

    python src/sensorpush/get_device_addresses.py --all

That program will run for 30 seconds, and print out the addresses of every unique SensorPush device it detects in that time. SensorPush devices broadcast using Bluetooth Low Energy (BLE) so they work best when they are nearby and unobstructed. If your device is near your computer while you're running that program, one of the addresses it prints out is most likely yours.

You can see which address corresponds to which device by running a second program:

    python src/sensorpush/blink_device.py [device_address]

where `[device_address]` is a SensorPush device address to test. That program will blink the small red LED on the device 10 times once it connects to the device. Use this program to test that you know your device's address, and save it somewhere accessible once you know what it is.
