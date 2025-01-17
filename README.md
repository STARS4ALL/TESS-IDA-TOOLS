# TESS-IDA-TOOLS

Collection of CLI scripts to download and analyze TESS Photometer Network data from IDA files.

*If all that you need is simply to download IDA monthly files from our NextCloud Server, our
simple [get-tess-ida.py](doc/get-tess-ida.md) script is all that you need. Read no further.*

* [Introduction](#introduction).
* [Installation and configuration](#installation-and-configuration).
* [Available utilities](#available-utilities).
* [Usage examples](#usage-examples).
* [The IDA monthly files](#tess-ida-monthly-files).
* [The auxiliar database](#the-auxiliar-database)

## Introduction

TESS-IDA-TOOLS is a small pipeline that can be executed as a whole (`tess-ida-pipe`) or by stages. The stages are:
* `tess-ida-get`. Download one or several IDA files from publised server by some selected criteria.
* `tess-ida-ecsv`. Converts one or more IDA files to a single, cnombined ECSV file.

There is also CLI utility (`tess-ida-db`) to fix location metadata justr in case the IDA files have not incorporated these metadata in the header. 

The scripts support generic options and comman-specific options

All scripts support the following ***generic options***:
* `--help | -h`. Prints command help and quits.
* `--version`. Prints software version and quits.
* `--console`. Prints execution info on the terminal console (up to level INFO)
* `--log-file`. Appends the same execution info to a log file
* `--quiet`. Suppresses all messages except CRITICAL, ERROR and WARNING.
* `--verbose`. Includes DEBUG level messages.

Many commands include `-s | --since` and `-u | --until` options. If not specified, the default values are the previous month and current month respectively.

Many commands include `-i | --input-dir` and `-o | output-dir` options. If not specified, the default value is the current working directory, like in the example above.

The `--help` option can be invoked at the global level to discover available subcommands and its options.

Example 1:
```bash
$ tess-ida-get -h

usage: tess-ida-get [-h] [--version] [--console] [--log-file <FILE>] [--verbose | --quiet] {single,range,photometers,near} ...

Get TESS-W IDA monthly files from NextCloud server

positional arguments:
  {single,range,photometers,near}
    single              Download single monthly file from a photometer
    range               Download a month range from a photometer
    photometers         Download a month range for selected photometers
    near                Download a month range from photometers near a given location

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --console             Log to console.
  --log-file <FILE>     Log to file.
  --verbose             Verbose output.
  --quiet               Quiet output.

```

Example 2:

```bash
usage: tess-ida-get near [-h] -lo <LON> -la <LAT> [-ra <R>] [-o OUT_DIR] [-s <YYYY-MM>] [-u <YYYY-MM>] [-c <N>] [--timeout TIMEOUT]

options:
  -h, --help            show this help message and exit
  -lo <LON>, --longitude <LON>
                        Longitude (decimal degrees)
  -la <LAT>, --latitude <LAT>
                        Latitude (decimal degrees)
  -ra <R>, --radius <R>
                        Search radius (Km) (defaults to 10 Km)
  -o OUT_DIR, --out-dir OUT_DIR
                        Output IDA base directory
  -s <YYYY-MM>, --since <YYYY-MM>
                        Year and Month (defaults to 2024-12-01 00:00:00)
  -u <YYYY-MM>, --until <YYYY-MM>
                        Year and Month (defaults to 2025-01-01 00:00:00)
  -c <N>, --concurrent <N>
                        Number of concurrent downloads (defaults to 4)
  --timeout TIMEOUT     HTTP timeout in seconds (defaults to 300 sec.)

```

## Installation and configuration

### Installation

We strongly recommend making a Python virtual environment where you install this package and other packages related to your data analysis. A very popular way of performing data analysis is to use [Jupyter Notebooks](https://jupyter.org/), so lets do this as an example.

The following lines create a jupyter folder from our home directory, a new Python virtual environment named `.venv` and activate it.

```bash
~$ mkdir jupyter
cd jupyter 
jupyter$ python3 -m venv .venv
jupyter$ source .venv/bin/activate
(.venv)  jupyter$ 
```

Now we install jupyter and matplotlib for the charts:

```bash
pip install -U pip
pip install notebook matplotlib
```

Finally, we can install the latest stable release of the tools from PyPi:
```bash
pip install tess-ida-tools
```
or use the latest development version from our [GitHub repository](https://github.com/STARS4ALL/TESS-IDA-TOOLS): 

```bash
pip install git+https://github.com/STARS4ALL/TESS-IDA-TOOLS#main
```

### Configuration

With the help of a text editor, create a new auxiliar environment file called `.env`
Inside this file, you must add two environment variables:

```text
IDA_URL=<NextCloud Server IDA base URL>
DATABASE_FILE=adm/tessida.db
```

The first one contains the base URL of our NextCloud Server where we publish the IDA files (*you should already have this information*). The second one is the path of an auxiliar SQLite database file that help us in the process of download and convert IDA files to ECSV.

The example above shows that we will create an `adm` subdirectory inside our working directory `~/jupyter` and a database file named `tessida.db`.

As the final step, we must initialize the database:

```bash
tess-ida-db --console schema create
```

***Warning*** When issuing the `tess-ida-db schema create` command, the previous database file is deleted !

All the configuration is done now.

## Usage examples

### Download a single month

Getting a single file
```bash
tess-ida-get --console single -n stars289 -m 2023-06 -o IDA
```

### Download an specific IDA file

Sometimes, the IDA files do not follow the generic `<name>_YYYY_MM.dat` format because the IDA file refers to a different location (the photometer has been reinstalled in another location).

For example, in Feb 2021, `stars201` was moved from an unknown location to a given location, so the files are named as `stars201_2020-02_-1.dat` and `stars201_2020-02_61.dat`.

```bash
tess-ida-get --console single -n stars201 -e stars201_2020-02_-1.dat -o IDA
tess-ida-get --console single -n stars201 -e stars201_2020-02_61.dat -o IDA
```
### Download files from photometers near a given location

The example below downloads files from TESS photometers since last month in a 50 Km radius of Madrid, Spain.

```bash
tess-ida-get --console near -lo -3.703790 -la 40.416775 -ra 50 -o IDA
```

### Getting IDA files and converting them to ECSV

In your jupyter working directory, with the activated virtual environment, type:

```bash
(.venv)  jupyter$  tess-ida-pipe --console range -n stars289 -s 2019-05 -u 2023-06 -i IDA -o ECSV
```

The above utility `tess-ida-pipe` is the complete pipeline that:
1. Downloads a range of IDA monthly files for stars289 since 2019-05 until 2023-06, placing them under `IDA/stars289` subdirectory.
2. Transforms them to ECSV files under `ECSV/stars289`.
3. Merges them into a combined time series file named `ECSV/stars289/stars289_201905-202306.ecsv`

As the final product for this step, we have the `ECSV/stars289/stars289_201905-202306.ecsv` ready to be analyzed in a Jupyter notebook.

***NOTES***:

1. Note that the transformation process will take a while (1-2 min per file), since every monthly file is added Solar Altitude, Moon Altitude and Moon Phase. However, if you re-run the script again, it will download all the files but will skip the transform part because the software detects no changes in IDA files.

2. When combining a range of dates, all monthly files metadata should be the same. If this not happens, the tool will issue a warning and the ***latest month*** is used as metadata for the combined ECSV file. It is recommended to inspect the IDA files manually to locate the differences and contact us to fix them if possible.

### Launching Jupyter

The second step to perform in the command line is launching Jupyter Notebook. From then all, all processing will be done in an notebook.

```bash
jupyer notebook
```

A snapshot of the notebook can be seen [here](doc/TESS-IDA-TOOLS-Example.md)

## TESS IDA Monthly Files

Readings from all TESS network are stored in a database at UCM, which also publish a series of monthly files per photometer in a NextCloud Server, known as the 'IDA Monthly Files' . For all active photometers, the current month is updated daily with a delay of one day.

The format was defined by [Dark Sky International](https://darksky.org/). The IDA Monthly files are basically a CSV file with an extra 35 line header containing additional metadata in readable text. 

IDA file header example:

```text
# Definition of the community standard for skyglow observations 1.0
# URL: http://www.darksky.org/NSBM/sdf1.0.pdf
# Number of header lines: 35
# This data is released under the following license: ODbL 1.0 http://opendatacommons.org/licenses/odbl/summary/
# Device type: TESS-W
# Instrument ID: stars1
# Data supplier: Cristóbal García / None
# Location name: Coslada, barrio de La Estación / Coslada/ Área metropolitana de Madrid y Corredor del Henares / Community of Madrid / Spain 
# Position: 40.4246043, -3.560279, 0.0
# Local timezone: Europe/Madrid
# Time Synchronization: timestamp added by MQTT subscriber
# Moving / Stationary position: STATIONARY
# Moving / Fixed look direction: FIXED
# Number of channels: 1
# Filters per channel: None
# Measurement direction per channel: (0.0, 0.0)
# Field of view: 17.0
# Number of fields per line: 8
# TESS MAC address: 18:FE:34:CF:E9:5A
# TESS firmware version: 1.0
# TESS cover offset value: 0.0
# TESS zero point: 20.1
# Comment:  
# Comment:
# Comment:
# Comment:
# Comment:
# Comment: 
# Comment: MSAS = ZP - 2.5*log10(Frequency)
# blank line 30
# blank line 31
# blank line 32
# UTC Date & Time, Local Date & Time, Enclosure Temperature, Sky Temperature, Frequency, MSAS, ZP, Sequence Number
# YYYY-MM-DDTHH:mm:ss.fff;YYYY-MM-DDTHH:mm:ss.fff;Celsius;Celsius;Hz;mag/arcsec^2;mag/arcsec^2; Multiple of Tx period
# END OF HEADER
```

From time to time, we update the IDA monthly files repository. In the 99% of the cases, the update is due to fix to unknown metadata in the headers, such as the `Position`, `Location name` or `Data supplier`. The `Position` is specially important for data analysis. So, you should not rely on inmutable IDA files and we recommend that you download the latest IDA files for the photometers of interest.

### From CSV to ECSV

The [AstroPy Python Library](https://docs.astropy.org/en/stable/index.html#) offers a very convenient `tables utility` to analyze tabular times series data like these. These tables can be loaded, manipulated (queried, filtered, augmented, etc) and  finally stored to a file in another text-based format named ECSV. This ECSV format also follows the convention of placing a header before ordinary CSV data and it is meant to recreate a Table variable in your python scripts exactly as it was written, with all the column names, data types, additional metadata.

As part of this tools package, there are utilities to parse IDA monthly files amd convert them to ECSV montly files and combine some them to a ceratin time frame. The IDA metadata is contained in a `table.meta['ida']` dictionary.

## The Auxiliar Database

The TESS-IDA-TOOLS work with an auxiliary database with the purpose of being efficient in transforming monthly IDA files to monthly ECSV files.
There are two issues to solve:
* Detect change of monthly IDA files (most likely metadata)
* Supply `Position` coordinates when needed if the IDA monthly file doesn't provide them.

### IDA Monthly Files change

Computing Sun & Moon data for a monthly file takes about 1-2 minutes, depending on the file size and computer. This must be multiplied for the number of downloaded files. This is unavoidable the first time the files are downloaded. However, unnecesary recalculations should be avoided when re-runing the pipeline. The problem is that IDA monthly files may change in the UCM NextCloud Server, most likely by updating observer, location or position metadata.

To avoid the lengthy computations, the pipeline always download the files (unless instructed not to do so) and compare an MD5 sum of these files against stored MD5 sums of previous downloads. For each file, if they match, there is no change and we skip the lengthy computation.

### Managing Position.

The pipeline will stop if it detects that there is not known `Position` during the Sun & Moon data computation. If you happen to know an approximated photometer Position with enough accuracy for your purpose, you may enter it in the database.

### Entering new position

1. Enter new cordinates in the database

```bash
tess-ida-db --console coords add --name stars4 --latitude 40.5 --longitude -3.1 --height 650
```

2. Then, re-run the pipeline with the `--fix` flag

```bash
(.venv)  jupyter$  tess-ida-pipe --console range -n stars4 -s 2024-03 -u 2024-06 -i IDA -o ECSV --fix
```

### Listing positions

TBD

### Modifing position

1. Modify coordinates in the database

You may modify any or all coordinates.

```bash
tess-ida-db --console coords update --name stars4 --longitude -3.15
tess-ida-db --console coords update --name stars4 --latitude 40.8 --height 690
```

2. Delete ***all related ECSV files !***

```bash
rm -fr ECSV/stars4/*.ecsv
```

3. Then, re-run the pipeline with the `--fix` flag

```bash
(.venv)  jupyter$  tess-ida-pipe --console range -n stars4 -s 2024-03 -u 2024-06 -i IDA -o ECSV --fix
```


### Deleting position

You probably want this once you know that the IDA monthly files incorporate Position metadata in the header


1. Delete coordinates from the database

```bash
tess-ida-db --console coords delete --name stars4
```

2. Delete ***all related ECSV files !***

```bash
rm -fr ECSV/stars4/*.ecsv
```

3. Then, re-run the pipeline ***without*** the  `--fix` flag

```bash
(.venv)  jupyter$  tess-ida-pipe --console range -n stars4 -s 2024-03 -u 2024-06 -i IDA -o ECSV
```
