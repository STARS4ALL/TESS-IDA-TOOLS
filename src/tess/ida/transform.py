# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#-----------------------
# Standard Python imports
# ----------------------

import os
import sys
import asyncio
import logging
import itertools

from datetime import datetime
from argparse import Namespace

# -------------------
# Third party imports
# -------------------

import numpy as np
import astropy.units as u
from astropy.timeseries import TimeSeries 

from astropy.coordinates import EarthLocation
from astroplan import Observer

from dateutil.relativedelta import relativedelta
from lica.cli import execute
from lica.validators import vfile

#--------------
# local imports
# -------------

from .. import __version__

# ----------------
# Module constants
# ----------------

DESCRIPTION = "Transform TESS-W IDA monthly files to ECSV"
IDA_HEADER_LEN = 35

# Column names
IDA_NAMES = ('UTC Date & Time', 'Local Date & Time', 'Enclosure Temperature', 'Sky Temperature', 'Frequency', 'MSAS', 'ZP', 'Sequence Number')
IDA_NAMES_4C = ('UTC Date & Time', 'Local Date & Time', 'Enclosure Temperature', 'Sky Temperature', 
    'Freq1', 'MSAS1', 'ZP1', 'Freq2', 'MSAS2', 'ZP2', 'Freq3',  'MSAS3', 'ZP3', 'Freq4', 'MSAS4', 'ZP4', 'Sequence Number')

# data types for column names
IDA_DTYPES = {'UTC Date & Time': str, 'Local Date & Time': str, 'Enclosure Temperature': float, 
    'Sky Temperature': float, 'Frequency': float, 'MSAS': float, 'ZP': float, 'Sequence Number': int}
IDA_DTYPES_4C = {'UTC Date & Time': str, 'Local Date & Time': str, 'Enclosure Temperature': float, 'Sky Temperature': float, 
    'Freq1': float, 'MSAS1': float, 'ZP1': float, 'Freq2': float, 'MSAS2': float, 'ZP2': float,
    'Freq3': float, 'MSAS3': float, 'ZP3': float, 'Freq4': float, 'MSAS4': float, 'ZP4': float,
    'Sequence Number': int}

# Exclude these columns from the final Table
IDA_EXCLUDE = ('Local Date & Time',)


# -----------------------
# Module global variables
# -----------------------

# get the module logger
log = logging.getLogger(__name__.split('.')[-1])

# -------------------
# Auxiliary functions
# -------------------

def v_or_n(value: str):
    '''Value or None function'''
    value = value.strip()
    lvalue = value.lower()
    return None if lvalue == 'none' or lvalue == 'unknown' or lvalue == '' else value

def now() -> datetime:
    return datetime.now().replace(day=1,hour=0,minute=0,second=0,microsecond=0)


def grouper(n: int, iterable):
    iterable = iter(iterable)
    return iter(lambda: list(itertools.islice(iterable, n)), [])


def output_path(filename: str, base_dir: str | None) -> str:
    base_dir = os.getcwd() if base_dir is None else base_dir
    root, ext = os.path.splitext(filename)
    root, filename = os.path.split(root)
    new_dir = os.path.join(base_dir, root)
    filename = filename + '.ecsv'
    if not os.path.isdir(new_dir):
        log.debug("new directory: %s", new_dir)
        os.makedirs(new_dir)
    return os.path.join(new_dir, filename)


def daterange(from_month: datetime, to_month: datetime) -> str:
    month = from_month
    while month <=  to_month:
        yield month.strftime('%Y-%m')
        month += relativedelta(months=1)


# =============
# Work Routines
# =============


def ida_metadata(path):
    # Reads the whole header, strips off the starting '# ' and trailing '\n'
    with open(path) as f:
        lines = [next(f)[2:-1] for _ in range(IDA_HEADER_LEN)]
    lines = lines[:-13] # Strips off the last 13 lines (including comments)
    # make  key-value pairs
    pairs = [line.split(': ') for line in lines]
    pairs = list(filter(lambda x: len(x) == 2, pairs))
    pairs[2][0] = 'License' # keyword is too long ...
    # Make a dict out of (keyword, value) pairs
    header = dict(pairs)
    # Convert values from strings to numeric values or nested dictonaries
    header['Number of header lines'] = int(header['Number of header lines'])
    header['Number of channels'] = int(header['Number of channels'])
    observer, affil = header['Data supplier'].split('/')
    header['Data supplier'] = {'observer': v_or_n(observer), 'affiliation':v_or_n(affil)}
    place, town, sub_region, region, country = header['Location name'].split('/')
    header['Location name'] = {'place': v_or_n(place), 'town': v_or_n(town), 
     'sub_region': v_or_n(sub_region), 'region': v_or_n(region), 'country': v_or_n(country)}
    latitude, longitude, height = header['Position'].split(',')
    header['Position'] = {'latitude': float(latitude), 'longitude': float(longitude), 'height': float(height)}
    header['Field of view'] = float(header['Field of view'])
    header['TESS cover offset value'] = float(header['TESS cover offset value'])
    header['Number of fields per line'] = int(header['Number of fields per line'])
    if header['Number of channels'] == 1:
        assert header['Number of fields per line'] == 8
        header['TESS zero point'] = float(header['TESS zero point'])
        az, zen = header['Measurement direction per channel'][1:-1].split(',')
        header['Measurement direction per channel'] = {'azimuth': float(az), 'zenital': float(zen)}
    else:
        assert header['Number of channels'] == 4
        assert header['Number of fields per line'] == 17
        header['Filters per channel'] = [f.strip()[1:-1] for f in header['Filters per channel'][1:-1].split(',')]
        header['TESS zero point'] = [float(zp) for zp in header['TESS zero point'][1:-1].split(',')]
        az1, zen1, az2, zen2, az3, zen3, az4, zen4 = header['Measurement direction per channel'][1:-1].split(',')
        header['Measurement direction per channel'] = [{'azimuth': float(az1), 'zenital': float(zen1)},
            {'azimuth': float(az2), 'zenital': float(zen2)}, {'azimuth': float(az3), 'zenital': float(zen3)},
            {'azimuth': float(az4), 'zenital': float(zen4)}]
    return header

  
def to_table(path: str) -> TimeSeries:
    log.info("Creating a Time Series from IDA file: %s", path)
    header = ida_metadata(path)
    nchannels = header['Number of channels']
    names = IDA_NAMES if nchannels == 1 else IDA_NAMES_4C
    converters = IDA_DTYPES if nchannels == 1 else IDA_DTYPES_4C
    table = TimeSeries.read(path, 
        time_column   = IDA_NAMES[0], 
        format        ='ascii.basic', 
        delimiter     = ';', 
        data_start    = 0, 
        names         = names, 
        exclude_names = IDA_EXCLUDE, 
        converters    = converters, 
        guess=False
    )
    table.meta['ida'] = header
    del table.meta['comments']
    # Convert to quiatities by adding units
    table['Enclosure Temperature'] = table['Enclosure Temperature'] * u.deg_C
    table['Sky Temperature'] = table['Sky Temperature'] * u.deg_C
    if nchannels == 1:
        table['Frequency'] = table['Frequency'] * u.Hz
        table['MSAS'] = table['MSAS'] * u.mag(u.Hz)
    else:
        table['Freq1'] = table['Freq1'] * u.Hz
        table['MSAS1'] = table['MSAS1'] * u.mag(u.Hz)
        table['Freq2'] = table['Freq2'] * u.Hz
        table['MSAS2'] = table['MSAS2'] * u.mag(u.Hz)
        table['Freq3'] = table['Freq3'] * u.Hz
        table['MSAS3'] = table['MSAS3'] * u.mag(u.Hz)
        table['Freq4'] = table['Freq4'] * u.Hz
        table['MSAS4'] = table['MSAS4'] * u.mag(u.Hz)
    return table

def add_columns(table: TimeSeries) -> None:
    log.info("Adding Sun/Moon data to Time Series")
    latitude = table.meta['ida']['Position']['latitude']
    longitude = table.meta['ida']['Position']['longitude']
    height = table.meta['ida']['Position']['height']
    obs_name = table.meta['ida']['Data supplier']['observer']
    location = EarthLocation(lat=latitude, lon=longitude, height=height)
    observer = Observer(name=obs_name, location=location)
    log.debug("Adding new 'Sun Alt' column")
    table['Sun Alt']   = observer.sun_altaz(table['time']).alt.deg * u.deg
    log.debug("Adding new 'Moon Alt' column")
    table['Moon Alt']   = observer.moon_altaz(table['time']).alt.deg * u.deg
    log.debug("Adding new 'Moon Phase' column")
    table['Moon Phase'] = observer.moon_phase(table['time']) / (np.pi * u.rad)
  
    
# ===========
# Generic API
# ===========

def to_ecsv_single(path: str, out_dir: str) -> None:
    table = to_table(path)
    add_columns(table)
    path = output_path(path, out_dir)
    log.info("Saving Time Series to ECSV file: %s", path)
    table.write(path, format='ascii.ecsv', delimiter=',', fast_writer=True, overwrite=True)
   


# ================================
# COMMAND LINE INTERFACE FUNCTIONS
# ================================

def cli_to_ecsv_single(args: Namespace) -> None:
    to_ecsv_single(
        path = args.input_file,
        out_dir = args.out_dir,
    )


def add_args(parser):
     # Now parse the application specific parts
    subparser = parser.add_subparsers(dest='command')
    parse_single = subparser.add_parser('single', help='Transform single IDA monthly file to ECSV')
    parse_single.add_argument('-i', '--input-file', type=vfile, required=True, help='Input IDA file')
    parse_single.add_argument('-o', '--out-dir', type=str, default=None, help='Output base directory')
    return parser


CMD_TABLE = {
    'single': cli_to_ecsv_single,
}

def cli_to_ecsv(args: Namespace) -> None:
    '''The main entry point specified by pyprojectable.toml'''
    func = CMD_TABLE[args.command]
    func(args)
    log.info("done!")


def main() -> None:
    execute(main_func=cli_to_ecsv, 
        add_args_func=add_args, 
        name=__name__, 
        version=__version__,
        description = DESCRIPTION
    )

if __name__ == '__main__':
    main()
