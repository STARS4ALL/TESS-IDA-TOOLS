# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#-----------------------
# Standard Python imports
# ----------------------

import os
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

from lica.cli import execute
from lica.validators import vfile, vdir, vmonth

#--------------
# local imports
# -------------

from .. import __version__
from .constants import TEW, T4C, IKW, TS, IDA_HEADER_LEN
from .utils import cur_month, prev_month, makedirs, v_or_n

# ----------------
# Module constants
# ----------------

DESCRIPTION = "Transform TESS-W IDA monthly files to ECSV"

# Column names
IDA_NAMES = TEW.values()
IDA_NAMES_4C = T4C.values()

# data types for column names
IDA_DTYPES = {TEW.UTC_TIME: str, TEW.LOCAL_TIME: str, TEW.BOX_TEMP: float, 
    TEW.SKY_TEMP: float, TEW.FREQ1: float, TEW.MAG1: float, TEW.ZP1: float, TEW.SEQ_NUM: int}
IDA_DTYPES_4C = {T4C.UTC_TIME: str, T4C.LOCAL_TIME: str,  T4C.BOX_TEMP: float, T4C.SKY_TEMP: float, 
    T4C.FREQ1: float, T4C.MAG1: float, T4C.ZP1: float, T4C.FREQ2: float, T4C.MAG2: float, T4C.ZP2: float,
    T4C.FREQ3: float, T4C.MAG3: float, T4C.ZP3: float, T4C.FREQ4: float, T4C.MAG4: float, T4C.ZP4: float,
    'Sequence Number': int}

# Exclude these columns from the final Table
IDA_EXCLUDE = (TEW.LOCAL_TIME,)


# -----------------------
# Module global variables
# -----------------------

# get the module logger
log = logging.getLogger(__name__.split('.')[-1])

# -------------------
# Auxiliary functions
# -------------------


def output_path(path: str, name: str, out_dir: str | None) -> str:
    full_dir = makedirs(out_dir, name)
    root, ext = os.path.splitext(path)
    path = os.path.basename(root)  + '.ecsv'
    return os.path.join(full_dir, path)



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
    pairs[2][0] = str(IKW.LICENSE)   # patch it, real keyword is too long ...
    # Make a dict out of (keyword, value) pairs
    header = dict(pairs)
    # Convert values from strings to numeric values or nested dictonaries
    header[IKW.NUM_HEADERS] = int(header[IKW.NUM_HEADERS])
    header[IKW.NUM_CHANNELS] = int(header[IKW.NUM_CHANNELS])
    observer, affil = header[IKW.OBSERVER].split('/')
    header[IKW.OBSERVER] = {'observer': v_or_n(observer), 'affiliation':v_or_n(affil)}
    place, town, sub_region, region, country = header[IKW.LOCATION].split('/')
    header[IKW.LOCATION] = {'place': v_or_n(place), 'town': v_or_n(town), 
     'sub_region': v_or_n(sub_region), 'region': v_or_n(region), 'country': v_or_n(country)}
    latitude, longitude, height = header[IKW.POSITION].split(',')
    header[IKW.POSITION] = {'latitude': float(latitude), 'longitude': float(longitude), 'height': float(height)}
    header[IKW.FOV] = float(header[IKW.FOV])
    header[IKW.COVER_OFFSET] = float(header[IKW.COVER_OFFSET])
    header[IKW.NUM_COLS] = int(header[IKW.NUM_COLS])
    if header[IKW.NUM_CHANNELS] == 1:
        assert header[IKW.NUM_COLS] == 8
        header[IKW.ZP] = float(header[IKW.ZP])
        az, zen = header[IKW.AIM][1:-1].split(',')
        header[IKW.AIM] = {'azimuth': float(az), 'zenital': float(zen)}
    else:
        assert header[IKW.NUM_CHANNELS] == 4
        assert header[IKW.NUM_COLS] == 17
        header['Filters per channel'] = [f.strip()[1:-1] for f in header['Filters per channel'][1:-1].split(',')]
        header[IKW.ZP] = [float(zp) for zp in header[IKW.ZP][1:-1].split(',')]
        az1, zen1, az2, zen2, az3, zen3, az4, zen4 = header[IKW.AIM][1:-1].split(',')
        header[IKW.AIM] = [{'azimuth': float(az1), 'zenital': float(zen1)},
            {'azimuth': float(az2), 'zenital': float(zen2)}, {'azimuth': float(az3), 'zenital': float(zen3)},
            {'azimuth': float(az4), 'zenital': float(zen4)}]
    return header

  
def to_table(path: str) -> TimeSeries:
    log.info("Creating a Time Series from IDA file: %s", path)
    header = ida_metadata(path)
    nchannels = header[IKW.NUM_CHANNELS]
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
    table[TEW.BOX_TEMP] = table[TEW.BOX_TEMP] * u.deg_C
    table[TEW.SKY_TEMP] = table[TEW.SKY_TEMP] * u.deg_C
    if nchannels == 1:
        table[TEW.FREQ1] = table[TEW.FREQ1] * u.Hz
        table[TEW.MAG1]  = table[TEW.MAG1] * u.mag(u.Hz)
    else:
        table[T4C.FREQ1] = table[T4C.FREQ1] * u.Hz
        table[T4C.MAG1] = table[T4C.MAG1] * u.mag(u.Hz)
        table[T4C.FREQ2] = table[T4C.FREQ2] * u.Hz
        table[T4C.MAG2] = table[T4C.MAG2] * u.mag(u.Hz)
        table[T4C.FREQ3] = table[T4C.FREQ3] * u.Hz
        table[T4C.MAG3] = table[T4C.MAG3] * u.mag(u.Hz)
        table[T4C.FREQ4] = table[T4C.FREQ4] * u.Hz
        table[T4C.MAG4] = table[T4C.MAG4] * u.mag(u.Hz)
    return table

def add_columns(table: TimeSeries) -> None:
    log.info("Adding Sun/Moon data to Time Series")
    latitude = table.meta['ida'][IKW.POSITION]['latitude']
    longitude = table.meta['ida'][IKW.POSITION]['longitude']
    height = table.meta['ida'][IKW.POSITION]['height']
    obs_name = table.meta['ida'][IKW.OBSERVER]['observer']
    location = EarthLocation(lat=latitude, lon=longitude, height=height)
    observer = Observer(name=obs_name, location=location)
    log.debug("Adding new %s column", TS.SUN_ALT)
    table[TS.SUN_ALT]   = observer.sun_altaz(table['time']).alt.deg * u.deg
    log.debug("Adding new %s column", TS.MOON_ALT)
    table[TS.MOON_ALT]   = observer.moon_altaz(table['time']).alt.deg * u.deg
    log.debug("Adding new %s column", TS.MOON_PHASE)
    table[TS.MOON_PHASE] = observer.moon_phase(table['time']) / (np.pi * u.rad)
  
    
# ===========
# Generic API
# ===========

def to_ecsv_single(path: str, out_dir: str) -> None:
    table = to_table(path)
    add_columns(table)
    name = table.meta['ida'][IKW.PHOT_NAME]
    path = output_path(path, name, out_dir)
    log.info("Saving Time Series to ECSV file: %s", path)
    table.write(path, format='ascii.ecsv', delimiter=',', fast_writer=True, overwrite=True)
   
def to_ecsv_range(in_dir: str, out_dir: str, since: datetime, until: datetime) -> None:
    pass

# ================================
# COMMAND LINE INTERFACE FUNCTIONS
# ================================

def cli_to_ecsv_single(args: Namespace) -> None:
    to_ecsv_single(
        path = args.input_file,
        out_dir = args.out_dir,
    )

def cli_to_ecsv_range(args: Namespace) -> None:
    to_ecsv_range(
        in_dir = args.input_dir,
        out_dir = args.out_dir,
        since = args.since,
        until = args.until,
    )
   

def add_args(parser):
     # Now parse the application specific parts
    subparser = parser.add_subparsers(dest='command')
    parse_single = subparser.add_parser('month', help='Transform single IDA monthly file to ECSV')
    parse_single.add_argument('-i', '--input-file', type=vfile, required=True, help='Input IDA file')
    parse_single.add_argument('-o', '--out-dir', type=str, default=None, help='Output ECSV base directory')
    parse_range = subparser.add_parser('range', help='Transform a range of IDA monthly files into a single ECSV')
    parse_range.add_argument('-i', '--input-dir', type=vdir, required=True, help='Input IDA base dir')
    parse_range.add_argument('-s', '--since',  type=vmonth, default=prev_month(), metavar='<YYYY-MM>', help='Year and Month (defaults to %(default)s)')
    parse_range.add_argument('-u', '--until',  type=vmonth, default=cur_month(), metavar='<YYYY-MM>', help='Year and Month (defaults to %(default)s)')
    parse_range.add_argument('-o', '--out-dir', type=str, default=None, help='Output ECSV base directory')
    return parser


CMD_TABLE = {
    'month': cli_to_ecsv_single,
    'range': cli_to_ecsv_range,
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
