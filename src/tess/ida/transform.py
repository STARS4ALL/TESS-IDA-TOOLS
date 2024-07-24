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
from astropy.time import Time
from astropy.table import QTable


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
IDA_NAMES = ('UTC Date & Time', 'Local Date & Time', 'Enclosure Temperature', 'Sky Temperature', 'Frequency', 'MSAS', 'ZP', 'Sequence Number')
IDA_EXCLUDE = ('Local Date & Time',)
IDA_DATA_TYPES = {'UTC Date & Time': str, 'Local Date & Time': str, 'Enclosure Temperature': float, 
    'Sky Temperature': float, 'Frequency': float, 'MSAS': float, 'ZP': float, 'Sequence Number': int}


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
    with open('stars1/stars1_2024-01.dat') as f:
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
    header['Field of view'] = float(header['Field of view'])
    header['Number of fields per line'] = int(header['Number of fields per line'])
    header['TESS cover offset value'] = float(header['TESS cover offset value'])
    header['TESS zero point'] = float(header['TESS zero point'])
    az, zen = header['Measurement direction per channel'][1:-1].split(',')
    header['Measurement direction per channel'] = {'azimuth': float(az), 'zenital': float(zen)}
    observer, affil = header['Data supplier'].split('/')
    header['Data supplier'] = {'observer': v_or_n(observer), 'affiliation':v_or_n(affil)}
    place, town, sub_region, region, country = header['Location name'].split('/')
    header['Location name'] = {'place': v_or_n(place), 'town': v_or_n(town), 
     'sub_region': v_or_n(sub_region), 'region': v_or_n(region), 'country': v_or_n(country)}
    latitude, longitude, height = header['Position'].split(',')
    header['Position'] = {'latitude': float(latitude), 'longitude': float(longitude), 'height': float(height)}
    return header
   
def to_table(path: str) -> QTable:
    log.info("Reading IDA file: %s", os.path.basename(path))
    header = ida_metadata(path)
    table = QTable.read(path, format='ascii.basic', delimiter=';', names=IDA_NAMES, exclude_names=IDA_EXCLUDE, converters=IDA_DATA_TYPES, guess=False)
    table.meta['ida'] = header
    del table.meta['comments']
    # Convert to quiatities by adding units
    table['Frequency'] = table['Frequency'] * u.Hz
    table['Enclosure Temperature'] = table['Enclosure Temperature'] * u.deg_C
    table['Sky Temperature'] = table['Sky Temperature'] * u.deg_C
    table['MSAS'] = table['MSAS'] * u.mag(u.Hz)
    return table

def add_columns(table: QTable) -> None:
    log.info("Transforming table")
    latitude = table.meta['ida']['Position']['latitude']
    longitude = table.meta['ida']['Position']['longitude']
    height = table.meta['ida']['Position']['height']
    obs_name = table.meta['ida']['Data supplier']['observer']
    location = EarthLocation(lat=latitude, lon=longitude, height=height)
    observer = Observer(name=obs_name, location=location)
    log.debug("Converting 'UTC Date & Time' column datatype to astropy Time")
    table['UTC Date & Time'] = Time(table['UTC Date & Time'], scale='utc', location=location)
    log.debug("Adding new 'Julian Date' column")
    table['Julian Date'] = table['UTC Date & Time'].jd
    log.debug("Adding new 'Sun Alt' column")
    table['Sun Alt']   = observer.sun_altaz(table['UTC Date & Time']).alt.deg * u.deg
    log.debug("Adding new 'Moon Alt' column")
    table['Moon Alt']   = observer.moon_altaz(table['UTC Date & Time']).alt.deg * u.deg
    log.debug("Adding new 'Moon Phase' column")
    table['Moon Phase'] = observer.moon_phase(table['UTC Date & Time']) / (np.pi * u.rad)
  
    
# ===========
# Generic API
# ===========

def to_ecsv_single(path: str, out_dir: str) -> None:
    table = to_table(path)
    add_columns(table)
    log.info("\n%s",table)
    log.info("\n%s",table.info)
    path = output_path(path, out_dir)
    log.info("Writting ECSV file: %s", os.path.basename(path))
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
