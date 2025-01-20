# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# -----------------------
# Standard Python imports
# ----------------------

import os
import glob
import logging

from datetime import datetime
from argparse import Namespace, ArgumentParser
from typing import Union, Dict, Any

# -------------------
# Third party imports
# -------------------

import numpy as np

import astropy.units as u
from astropy.table import vstack
from astropy.timeseries import TimeSeries
from astropy.coordinates import EarthLocation
from astroplan import Observer

from lica.cli import execute
from lica.typing import OptStr

# --------------
# local imports
# -------------

from . import __version__
from .dbase import (
    aux_dbase_load,
    aux_dbase_save,
    aux_table_hashes_lookup,
    aux_table_hashes_insert,
    aux_table_hashes_update,
    aux_table_coords_lookup,
)

from .constants import (
    TESSW_COLS as TEW,
    TESS4C_COLS as T4C,
    TIMESERIES_COLS as TS,
    IDA_KEYWORDS as IKW,
    IDA_HEADER_LEN,
)
from .utils.utils import (
    to_phot_dir,
    makedirs,
    v_or_n,
    month_range,
    name_month,
    hash_func,
)

from .utils import parser as prs

# ----------------
# Module constants
# ----------------

DESCRIPTION = "Transform TESS-W IDA monthly files to ECSV"
OptDate = Union[datetime, None]

# Column names
IDA_NAMES = TEW.values()
IDA_NAMES_4C = T4C.values()

# data types for column names
IDA_DTYPES = {
    TEW.UTC_TIME: str,
    TEW.LOCAL_TIME: str,
    TEW.BOX_TEMP: float,
    TEW.SKY_TEMP: float,
    TEW.FREQ: float,
    TEW.MAG: float,
    TEW.ZP: float,
    TEW.SEQ_NUM: int,
}
IDA_DTYPES_4C = {
    T4C.UTC_TIME: str,
    T4C.LOCAL_TIME: str,
    T4C.BOX_TEMP: float,
    T4C.SKY_TEMP: float,
    T4C.FREQ1: float,
    T4C.MAG1: float,
    T4C.ZP1: float,
    T4C.FREQ2: float,
    T4C.MAG2: float,
    T4C.ZP2: float,
    T4C.FREQ3: float,
    T4C.MAG3: float,
    T4C.ZP3: float,
    T4C.FREQ4: float,
    T4C.MAG4: float,
    T4C.ZP4: float,
    "Sequence Number": int,
}

# Exclude these columns from the final Table
IDA_EXCLUDE = (TEW.LOCAL_TIME,)


# -----------------------
# Module global variables
# -----------------------

# get the module logger
log = logging.getLogger(__name__.split(".")[-1])

# -----------------
# Custom Exceptions
# -----------------


class NoCoordinatesError(Exception):
    pass


# -------------------
# Auxiliary functions
# -------------------

# =============
# Work Routines
# =============


def ida_metadata(path: str, fix: bool) -> Dict[str, Any]:
    # Reads the whole header, strips off the starting '# ' and trailing '\n'
    name, month = name_month(path)
    with open(path) as f:
        lines = [next(f)[2:-1] for _ in range(IDA_HEADER_LEN)]
    lines = lines[:-13]  # Strips off the last 13 lines (including comments)
    # make  key-value pairs
    pairs = [line.split(": ") for line in lines]
    pairs = list(filter(lambda x: len(x) == 2, pairs))
    pairs[2][0] = str(IKW.LICENSE)  # patch it, real keyword is too long ...
    # Make a dict out of (keyword, value) pairs
    header = dict(pairs)
    # Convert values from strings to numeric values or nested dictonaries
    header[IKW.NUM_HEADERS] = int(header[IKW.NUM_HEADERS])
    header[IKW.NUM_CHANNELS] = int(header[IKW.NUM_CHANNELS])
    observer, affil = header[IKW.OBSERVER].split("/")
    header[IKW.OBSERVER] = {"observer": v_or_n(observer), "affiliation": v_or_n(affil)}
    place, town, sub_region, region, country = header[IKW.LOCATION].split("/")
    header[IKW.LOCATION] = {
        "place": v_or_n(place),
        "town": v_or_n(town),
        "sub_region": v_or_n(sub_region),
        "region": v_or_n(region),
        "country": v_or_n(country),
    }
    latitude, longitude, height = header[IKW.POSITION].split(",")
    try:
        header[IKW.POSITION] = {
            "latitude": float(v_or_n(latitude)),
            "longitude": float(v_or_n(longitude)),
            "height": float(v_or_n(height)) if v_or_n(height) else 0.0,
        }
    except TypeError:
        if not fix:
            log.error("[%s] [%s] Unknown Observer coordinates", name, month)
            log.error(
                "[%s] [%s] Add coordinates to aux. coordinates table & re-run with --fix",
                name,
                month,
            )
            raise NoCoordinatesError
        coords = next(aux_table_coords_lookup(name))
        if not coords:
            log.error(
                "[%s] [%s] Could not find alternative coordinates in the aux. coordinates table",
                name,
                month,
            )
            raise NoCoordinatesError
        _, lati, longi, h = coords
        log.warning(
            "[%s] [%s] Fixed alternative coordinates (lat: %f, long: %f, h: %f) from the adm coordinates table",
            name,
            month,
            lati,
            longi,
            h,
        )
        header[IKW.POSITION] = {"latitude": lati, "longitude": longi, "height": h}
    header[IKW.FOV] = float(header[IKW.FOV])
    header[IKW.COVER_OFFSET] = float(header[IKW.COVER_OFFSET])
    header[IKW.NUM_COLS] = int(header[IKW.NUM_COLS])
    if header[IKW.NUM_CHANNELS] == 1:
        assert header[IKW.NUM_COLS] == 8
        header[IKW.ZP] = float(
            header[IKW.ZP].split("(")[0]
        )  # get rid of possible comments on the right of (
        az, zen = header[IKW.AIM][1:-1].split(",")
        header[IKW.AIM] = {"azimuth": float(az), "zenital": float(zen)}
    else:
        assert header[IKW.NUM_CHANNELS] == 4
        assert header[IKW.NUM_COLS] == 17
        header["Filters per channel"] = [
            f.strip()[1:-1] for f in header["Filters per channel"][1:-1].split(",")
        ]
        header[IKW.ZP] = [float(zp) for zp in header[IKW.ZP][1:-1].split(",")]
        az1, zen1, az2, zen2, az3, zen3, az4, zen4 = header[IKW.AIM][1:-1].split(",")
        header[IKW.AIM] = [
            {"azimuth": float(az1), "zenital": float(zen1)},
            {"azimuth": float(az2), "zenital": float(zen2)},
            {"azimuth": float(az3), "zenital": float(zen3)},
            {"azimuth": float(az4), "zenital": float(zen4)},
        ]
    return header


def ida_to_table(path: str, fix: bool) -> TimeSeries:
    header = ida_metadata(path, fix)
    nchannels = header[IKW.NUM_CHANNELS]
    names = IDA_NAMES if nchannels == 1 else IDA_NAMES_4C
    converters = IDA_DTYPES if nchannels == 1 else IDA_DTYPES_4C
    table = TimeSeries.read(
        path,
        time_column=IDA_NAMES[0],
        format="ascii.basic",
        delimiter=";",
        data_start=0,
        names=names,
        exclude_names=IDA_EXCLUDE,
        converters=converters,
        guess=False,
    )
    table.meta["ida"] = header
    del table.meta["comments"]
    # Convert to quiatities by adding units
    table[TEW.BOX_TEMP] = table[TEW.BOX_TEMP] * u.deg_C
    table[TEW.SKY_TEMP] = table[TEW.SKY_TEMP] * u.deg_C
    if nchannels == 1:
        table[TEW.FREQ] = table[TEW.FREQ] * u.Hz
        table[TEW.MAG] = table[TEW.MAG] * u.mag() / u.arcsec**2
    else:
        table[T4C.FREQ1] = table[T4C.FREQ1] * u.Hz
        table[T4C.MAG1] = table[T4C.MAG1] * u.mag() / u.arcsec**2
        table[T4C.FREQ2] = table[T4C.FREQ2] * u.Hz
        table[T4C.MAG2] = table[T4C.MAG2] * u.mag() / u.arcsec**2
        table[T4C.FREQ3] = table[T4C.FREQ3] * u.Hz
        table[T4C.MAG3] = table[T4C.MAG3] * u.mag() / u.arcsec**2
        table[T4C.FREQ4] = table[T4C.FREQ4] * u.Hz
        table[T4C.MAG4] = table[T4C.MAG4] * u.mag() / u.arcsec**2
    return table


def add_columns(table: TimeSeries, name: str, month: str) -> None:
    latitude = table.meta["ida"][IKW.POSITION]["latitude"]
    longitude = table.meta["ida"][IKW.POSITION]["longitude"]
    height = table.meta["ida"][IKW.POSITION]["height"]
    obs_name = table.meta["ida"][IKW.OBSERVER]["observer"]
    zenital = table.meta["ida"][IKW.AIM]["zenital"]  # Only valid for TESS-W
    location = EarthLocation(lat=latitude, lon=longitude, height=height)
    observer = Observer(name=obs_name, location=location)
    log.info("[%s] [%s] Adding new %s column", name, month, TS.SUN_ALT)
    sun_altaz = observer.sun_altaz(table["time"])
    table[TS.SUN_ALT] = np.round(sun_altaz.alt.deg, 2) * u.deg
    if zenital != 0.0:
        log.info("[%s] [%s] Adding new %s column", name, month, TS.SUN_AZ)
        table[TS.SUN_AZ] = np.round(sun_altaz.az.deg, 2) * u.deg
    log.info("[%s] [%s] Adding new %s column", name, month, TS.MOON_ALT)
    moon_altaz = observer.moon_altaz(table["time"])
    table[TS.MOON_ALT] = np.round(moon_altaz.alt.deg) * u.deg
    if zenital != 0.0:
        log.info("[%s] [%s] Adding new %s column", name, month, TS.MOON_AZ)
        table[TS.MOON_AZ] = np.round(moon_altaz.az.deg, 2) * u.deg
    log.info("[%s] [%s] Adding new %s column", name, month, TS.MOON_ILLUM)
    table[TS.MOON_ILLUM] = np.round(observer.moon_illumination(table["time"]), 3)


def create_table(path: str, fix: bool) -> TimeSeries:
    """Create TimeSeries or loads table from IDA file"""
    name, month = name_month(path)
    log.info("[%s] [%s] Creating a Time Series from IDA file: %s", name, month, path)
    table = ida_to_table(path, fix)
    add_columns(table, name, month)
    return table


def load_table(path: str) -> TimeSeries:
    """Read TimeSeries table from ECSV file"""
    return TimeSeries.read(path, format="ascii.ecsv", delimiter=",")


def save_table(table: TimeSeries, path: str) -> None:
    """Read TimeSeries table from ECSV file"""
    name, month = name_month(path)
    log.info("[%s] [%s] Saving Time Series to ECSV file: %s", name, month, path)
    table.write(
        path, format="ascii.ecsv", delimiter=",", fast_writer=True, overwrite=True
    )


def append_table(acc: TimeSeries, table: TimeSeries) -> TimeSeries:
    return vstack([acc, table])


def do_to_ecsv_single(in_path: str, out_path: str, fix: bool) -> None:
    name, month = name_month(in_path)
    data = [os.path.basename(in_path), hash_func(in_path)]
    result = next(aux_table_hashes_lookup(data[0]))
    if result:
        _, stored_hash_str = result
        if data[1] != stored_hash_str or not os.path.isfile(out_path):
            aux_table_hashes_update(data)
            table = create_table(in_path, fix)
            save_table(table, out_path)
        else:
            log.info(
                "[%s] [%s] Time Series already in ECSV file: %s", name, month, out_path
            )
    else:
        aux_table_hashes_insert(data)
        table = create_table(in_path, fix)
        save_table(table, out_path)


# ===========
# Generic API
# ===========


def to_ecsv_single(
    base_dir: OptStr, name: str, month: OptDate, exact: OptStr, out_dir: str, fix: bool
) -> None:
    in_dir_path = to_phot_dir(base_dir, name)
    filename = name + "_" + month.strftime("%Y-%m") + ".dat" if not exact else exact
    in_path = os.path.join(in_dir_path, filename)
    out_dir_path = makedirs(out_dir, name)
    filename = os.path.splitext(filename)[0]
    out_path = os.path.join(out_dir_path, filename + ".ecsv")
    do_to_ecsv_single(in_path, out_path, fix)


def to_ecsv_range(
    base_dir: OptStr,
    name: str,
    out_dir: str,
    since: datetime,
    until: datetime,
    fix: bool,
) -> None:
    in_dir_path = to_phot_dir(base_dir, name)
    months = [m for m in month_range(since, until)]
    search_path = os.path.join(in_dir_path, "*.dat")
    candidate_path = list()
    for path in sorted(glob.iglob(search_path)):
        candidate_month = os.path.splitext(os.path.basename(path))[0].split("_")[1]
        if candidate_month in months:
            candidate_path.append(path)
    for in_path in candidate_path:
        filename = os.path.splitext(os.path.basename(in_path))[0] + ".ecsv"
        dirname = makedirs(out_dir, name)
        out_path = os.path.join(dirname, filename)
        do_to_ecsv_single(in_path, out_path, fix)


def to_ecsv_combine(
    base_dir: OptStr, name: str, since: datetime, until: datetime, oname: str
) -> None:
    in_dir_path = to_phot_dir(base_dir, name)
    months = [m for m in month_range(since, until)]
    log.info(
        "[%s] Combining %d months from %s to %s into a single ECSV",
        name,
        len(months),
        months[0],
        months[-1],
    )
    search_path = os.path.join(in_dir_path, "stars*.ecsv")
    candidate_path = list()
    for path in sorted(glob.iglob(search_path)):
        candidate_month = os.path.splitext(os.path.basename(path))[0].split("_")[1]
        if candidate_month in months:
            candidate_path.append(path)
    if len(candidate_path) < 1:
        log.warning("[%s] No tables to combine. Check range input parameters.", name)
        return
    acc_table = load_table(candidate_path[0])
    acc_table.meta["combined"] = [os.path.basename(candidate_path[0])]
    for in_path in candidate_path[1:]:
        table = load_table(in_path)
        acc_table = append_table(acc_table, table)
        acc_table.meta["combined"].append(os.path.basename(in_path))
    dirname = os.path.dirname(candidate_path[0])
    filename = (
        f"{name}_{since.strftime('%Y%m')}-{until.strftime('%Y%m')}.ecsv"
        if oname is None
        else oname
    )
    path = os.path.join(dirname, filename)
    log.info("[%s] Saving combined Time Series to ECSV file: %s", name, path)
    acc_table.write(
        path, format="ascii.ecsv", delimiter=",", fast_writer=True, overwrite=True
    )


# ================================
# COMMAND LINE INTERFACE FUNCTIONS
# ================================


def cli_to_ecsv_single(args: Namespace) -> None:
    to_ecsv_single(
        base_dir=args.in_dir,
        name=args.name,
        month=args.month,
        exact=args.exact,
        out_dir=args.out_dir,
        fix=True if args.fix else False,
    )


def cli_to_ecsv_range(args: Namespace) -> None:
    to_ecsv_range(
        base_dir=args.in_dir,
        name=args.name,
        out_dir=args.out_dir,
        since=args.since,
        until=args.until,
        fix=True if args.fix else False,
    )


def cli_to_ecsv_combine(args: Namespace) -> None:
    to_ecsv_combine(
        base_dir=args.in_dir,
        name=args.name,
        since=args.since,
        until=args.until,
        oname=args.out_filename,
    )


def add_args(parser: ArgumentParser) -> None:
    # Now parse the application specific parts
    subparser = parser.add_subparsers(dest="command")
    parser_single = subparser.add_parser(
        "single",
        parents=[
            prs.name(),
            prs.mon_single(),
            prs.inout_dirs("IDA", "ECSV"),
            prs.fix(),
        ],
        help="Convert to ECSV a single monthly file from a photometer",
    )
    parser_single.set_defaults(func=cli_to_ecsv_single)

    parser_range = subparser.add_parser(
        "range",
        parents=[prs.name(), prs.mon_range(), prs.inout_dirs("IDA", "ECSV"), prs.fix()],
        help="Convert to ECSV a range of IDA monthly files from a photometer",
    )
    parser_range.set_defaults(func=cli_to_ecsv_range)

    parser_comb = subparser.add_parser(
        "combine",
        parents=[prs.name(), prs.mon_range(), prs.inout_file("ECSV", "combined")],
        help="Combines a range of monthly ECSV files into a single ECSV",
    )
    parser_comb.set_defaults(func=cli_to_ecsv_combine)


def cli_to_ecsv(args: Namespace) -> None:
    """The main entry point specified by pyprojectable.toml"""
    aux_dbase_load()
    try:
        args.func(args)
    except NoCoordinatesError:
        pass
    aux_dbase_save()
    log.info("done!")


def main() -> None:
    execute(
        main_func=cli_to_ecsv,
        add_args_func=add_args,
        name="tess-ida-ecsv",
        version=__version__,
        description=DESCRIPTION,
    )


if __name__ == "__main__":
    main()
