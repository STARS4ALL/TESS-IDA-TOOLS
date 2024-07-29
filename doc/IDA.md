# TESSW IDA Monthly files

Readings from all TESSW network are stored in a database at UCM, which also publish a series of monthly files per photometer, known as the 'IDA Monthly Files' in a NextCloud Server. For all active photometers, the current month is updated daily with a delay of one day.

The format was defined by [Dark Sky International](https://darksky.org/). The IDA Monthly files are basically an spreadsheet CSV file with an extra 35 line header containing additional metadata in readable text. 

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

From time to time, we update all the IDA monthly files. In the 99% of the cases, this is due to unknown metadata in the headers, such as the `Position`, `Location name` or `Data supplier`. The `Position` is specially important for data analysis. So, you should not rely on inmutable IDA files and we recommend that you download the latest IDA files for the photometers of interest.

# AstroPy Tables

The [AstroPy Python Library](https://docs.astropy.org/en/stable/index.html#) offers a very convenient `tables utility` to analyze tabular times series data like these. These tables can be loaded, manipulated (queried, filtere, augmented, etc) and  finallystored to a file in another text-based format named ECSV. This ECSV format also follows the convention of placing a header before ordinary CSV data and it is meant to recreate a Table variable in your python scripts exactly as it was written, with all the column names, data types, additional metadata.

As part of this tools package, there are utilities to parse IDA monthly files amd convert them to ECSV montly files and combine some them to a ceratin time frame.
The IDA metadata is contained in a `table.meta['ida']` dictionary.
