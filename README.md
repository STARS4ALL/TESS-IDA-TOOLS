# TESS-IDA-TOOLS

Collection of utilities to download and analyze TESS Photometer Network data from IDA files.

*If all that you need is simply to download IDA monthly files from our NextCloud Server, our
simple [get-tess-ida.py](doc/get-tess-ida.md) script is all that you need. Read no further.*

## Summary
* [Installation and configuration](#installation-and-configuration).
* [Available utilities](#available-utilities).
* [Usage example](#simple-usage-example).
* [The IDA monthly files](#tess-ida-monthly-files).
* [The auxiliar database](#the-auxiliar-database)

## Installation and configuration

### Installation

We strongly recommend making a Python virtual environment where you install this package and other packages related to your data analysis. A very popular way is to use [Jupyter Notebooks](https://jupyter.org/), so lets do this as an example.

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

The first one contains the base URL of our NextCloud Server where we publish the IDA files (and you should already have)
The second one is the path of an auxiliar SQLite database file that help us in the process of download and convert IDA files to ECSV

The example above shows that we will create an `adm` subdirectory inside our working directory `~/jupyter` and a database file named `tessida.db`.

As the final step, we must initialize the database:

```bash
tess-ida-db --console schema create
```

***Warning*** When issuing the `tess-ida-db schema create` command, the previous database file is deleted !

All the configuration is done now.

## Available Utilities

The TESS-IDA-TOOLS comprises the following scripts:
* `tess-ida-db`. Auxiliar database management,
* `tess-ida-get`. Download series of IDA monthly files.
* `tess-ida-ecsv`. Transform series of monthly files. Combine series of ECSV files into one.
* `tess-ida-pipe`. The complete download/transform/combine pipeline 

All script support the following ***generic options***:
* `--version`. Prints software version and quits.
* `--console`. Prints execution info on the terminal console (up to level INFO)
* `--log-file`. Appends the same execution info to a log file
* `--quiet`. Suppresses all messages except CRITICAL, ERROR and WARNING.
* `--verbose`. Includes DEBUG level messages.

All scripts include a help system (`-h` or `--help`) to describe the available commands and command options.

Examples:

```bash
tess-ida-get -h
```

shows that this script has three commands: `single`, `range` and `photometers`

Typing:

```bash
tess-ida-get single -h
tess-ida-get range -h
tess-ida-get photometers -h
```

will show available options for each command. The generic options always come *before* the command.

Example:

```bash
tess-ida-get --console --quiet photometers --list 1 703 328 --since 2024-03 --until 2024-07
```

The command above download range of files for photometers  stars1 stars703 and stars328.

Many commands include `-s | --since` and `-u | --until` options. 
If not specified, the default values are the previous month and current month respectively.

Many commands include `-i | --input-dir` and `-o | output-dir` options.
If not specified, the default value is the current working directory, like in the example above.

## Simple usage example

### Getting the IDA files and converting them to ECSV

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

2. When combining a range of dates, all monthly files metadata should be the same. If this not happens, the tool will issue a warning and the ***lastest month*** is used as metadata for the combined ECSV file. It is recommended to inspect the IDA files manually to locate the differences and contact us to fix them if possible.

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
