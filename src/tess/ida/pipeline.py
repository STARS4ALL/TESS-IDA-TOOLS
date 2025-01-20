# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# -----------------------
# Standard Python imports
# ----------------------

import asyncio
import logging


from datetime import datetime
from argparse import Namespace, ArgumentParser
from typing import Sequence

# -------------------
# Third party imports
# -------------------

import decouple

from lica.cli import async_execute
from lica.typing import OptStr

# --------------
# local imports
# -------------

from . import __version__
from .utils import parser as prs
from .dbase import aux_dbase_load, aux_dbase_save
from .download import (
    download_ida_single, 
    download_ida_range, 
    ida_names_by_seq_or_range, 
    ida_names_by_location
)
from .timeseries import (
    to_ecsv_single,
    to_ecsv_range,
    to_ecsv_combine,
    NoCoordinatesError,
)

# ----------------
# Module constants
# ----------------

DESCRIPTION = "Full Download, Tranform and Combine IDA data from NextCloud Server"

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger(__name__.split(".")[-1])

# -------------------
# Auxiliary functions
# -------------------


# ===========
# Generic API
# ===========


async def pipe_single(
    base_url: str,
    ida_base_dir: OptStr,
    ecsv_base_dir: OptStr,
    name: str,
    month: OptStr,
    exact: OptStr,
    fix: bool,
    timeout: int,
) -> None:
    await download_ida_single(base_url, ida_base_dir, name, month, exact, timeout)
    await asyncio.to_thread(
        to_ecsv_single, ida_base_dir, name, month, exact, ecsv_base_dir, fix
    )


async def pipe_range(
    base_url: str,
    ida_base_dir: OptStr,
    ecsv_base_dir: OptStr,
    name: str,
    since: datetime,
    until: datetime,
    skip_download: bool,
    oname: str,
    fix: bool,
    concurrent: int,
    timeout: int,
) -> None:
    if not skip_download:
        await download_ida_range(
            base_url, ida_base_dir, name, since, until, concurrent, timeout
        )
    await asyncio.to_thread(
        to_ecsv_range, ida_base_dir, name, ecsv_base_dir, since, until, fix
    )
    await asyncio.to_thread(to_ecsv_combine, ecsv_base_dir, name, since, until, oname)


async def pipe_photometers(
    base_url: str,
    ida_base_dir: OptStr,
    ecsv_base_dir: OptStr,
    rang: Sequence[int],
    seq: Sequence[int],
    since: datetime,
    until: datetime,
    skip_download: bool,
    oname: str,
    fix: bool,
    concurrent: int,
    timeout: int,
) -> None:
    names = ida_names_by_seq_or_range(seq, rang)
    if not skip_download:
        for name in names:
            await download_ida_range(base_url, ida_base_dir, name, since, until, concurrent, timeout)
    for name in names:
        await asyncio.to_thread(
            to_ecsv_range, ida_base_dir, name, ecsv_base_dir, since, until, fix
        )
        await asyncio.to_thread(
            to_ecsv_combine, ecsv_base_dir, name, since, until, oname
        )

async def pipe_location(
    base_url: str,
    ida_base_dir: OptStr,
    ecsv_base_dir: OptStr,
    lon: float,
    lat: float,
    radius: float,
    since: datetime,
    until: datetime,
    skip_download: bool,
    oname: str,
    fix: bool,
    concurrent: int,
    timeout: int,
) -> None:
    names = await ida_names_by_location(
        base_url, ida_base_dir, lon, lat, radius, timeout
    )
    if not skip_download:
        for name in names:
            await download_ida_range(base_url, ida_base_dir, name, since, until, concurrent, timeout)
    for name in names:
        await asyncio.to_thread(
            to_ecsv_range, ida_base_dir, name, ecsv_base_dir, since, until, fix
        )
        await asyncio.to_thread(
            to_ecsv_combine, ecsv_base_dir, name, since, until, oname
        )

# ================================
# COMMAND LINE INTERFACE FUNCTIONS
# ================================

async def cli_pipe_single(args: Namespace) -> None:
    await pipe_single(
        base_url=args.base_url,
        ida_base_dir=args.in_dir,
        ecsv_base_dir=args.out_dir,
        name=args.name,
        month=args.month,
        exact=args.exact,
        fix=True if args.fix else False,
        timeout=args.timeout,
    )


async def cli_pipe_range(args: Namespace) -> None:
    await pipe_range(
        base_url=args.base_url,
        ida_base_dir=args.in_dir,
        ecsv_base_dir=args.out_dir,
        name=args.name,
        since=args.since,
        until=args.until,
        skip_download=args.skip_download,
        oname=args.out_filename,
        fix=True if args.fix else False,
        concurrent=args.concurrent,
        timeout=args.timeout,
    )


async def cli_pipe_photometers(args: Namespace) -> None:
    await pipe_photometers(
        base_url=args.base_url,
        ida_base_dir=args.in_dir,
        ecsv_base_dir=args.out_dir,
        seq=args.list,
        rang=args.range,
        since=args.since,
        until=args.until,
        skip_download=args.skip_download,
        oname=args.out_filename,
        fix=True if args.fix else False,
        concurrent=args.concurrent,
        timeout=args.timeout,
    )


async def cli_pipe_location(args: Namespace) -> None:
    await pipe_location(
        base_url=args.base_url,
        ida_base_dir=args.in_dir,
        ecsv_base_dir=args.out_dir,
        lon=args.longitude,
        lat=args.latitude,
        radius=args.radius,
        since=args.since,
        until=args.until,
        skip_download=args.skip_download,
        oname=args.out_filename,
        fix=True if args.fix else False,
        concurrent=args.concurrent,
        timeout=args.timeout,
    )


def add_args(parser: ArgumentParser) -> ArgumentParser:
    # Now parse the application specific parts
    subparser = parser.add_subparsers(dest="command")
    parser_single = subparser.add_parser(
        "single",
        parents=[
            prs.name(),
            prs.out_dir("ECSV"),
            prs.inout_file("IDA", "combined ECSV", in_dir_exists=False),
            prs.mon_single(),
            prs.timeout(),
            prs.fix(),
        ],
        help="Process single monthly file from a photometer",
    )
    parser_single.set_defaults(func=cli_pipe_single)
    parser_range = subparser.add_parser(
        "range",
        parents=[
            prs.name(),
            prs.out_dir("ECSV"),
            prs.inout_file("IDA", "combined ECSV", in_dir_exists=False),
            prs.mon_range(),
            prs.concurrent(),
            prs.fix(),
            prs.skip(),
        ],
        help="Process a month range from a photometer",
    )
    parser_range.set_defaults(func=cli_pipe_range)
    parser_phots = subparser.add_parser(
        "photometers",
        parents=[
            prs.phot_range(),
            prs.out_dir("ECSV"),
            prs.inout_file("IDA", "combined ECSV", in_dir_exists=False),
            prs.mon_range(),
            prs.concurrent(),
            prs.fix(),
            prs.skip(),
        ],
        help="Download a month range for selected photometers",
    )
    parser_phots.set_defaults(func=cli_pipe_photometers)
    parser_location = subparser.add_parser(
        "near",
        parents=[
            prs.location(),
            prs.out_dir("ECSV"),
            prs.inout_file("IDA", "combined ECSV", in_dir_exists=False),
            prs.mon_range(),
            prs.concurrent(),
            prs.fix(),
            prs.skip(),
        ],
        help="Process a month range from photometers near a given location",
    )
    parser_location.set_defaults(func=cli_pipe_location)
    return parser


async def cli_pipeline(args: Namespace) -> None:
    """The main entry point specified by pyproject.toml"""
    args.base_url = decouple.config("IDA_URL")
    aux_dbase_load()
    try:
        await args.func(args)
    except NoCoordinatesError:
        pass
    aux_dbase_save()
    log.info("done!")


def main() -> None:
    async_execute(
        main_func=cli_pipeline,
        add_args_func=add_args,
        name="tess-ida-pipe",
        version=__version__,
        description=DESCRIPTION,
    )


if __name__ == "__main__":
    main()
