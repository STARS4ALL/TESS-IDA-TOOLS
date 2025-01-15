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
from .download import download_ida_single, download_ida_range
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
    timeout,
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
    oname: bool,
    fix: bool,
    concurrent: int,
    timeout,
) -> None:
    if not skip_download:
        await download_ida_range(
            base_url, ida_base_dir, name, since, until, concurrent, timeout
        )
    await asyncio.to_thread(
        to_ecsv_range, ida_base_dir, name, ecsv_base_dir, since, until, fix
    )
    await asyncio.to_thread(to_ecsv_combine, ecsv_base_dir, name, since, until, oname)


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


def add_args(parser: ArgumentParser) -> ArgumentParser:
    # Now parse the application specific parts
    subparser = parser.add_subparsers(dest="command")
    parser_single = subparser.add_parser(
        "single",
        parents=[
            prs.name(),
            prs.inout_file("IDA", "combined ECSV"),
            prs.mon_single(),
            prs.timeout(),
            prs.fix(),
        ],
        help="Download single monthly file from a photometer",
    )
    parser_single.set_defaults(func=cli_pipe_single)

    parser_range = subparser.add_parser(
        "range",
        parents=[
            prs.name(),
            prs.inout_file("IDA", "combined ECSV"),
            prs.mon_range(),
            prs.concurrent(),
            prs.fix(),
        ],
        help="Download a month range from a photometer",
    )
    parser_range.add_argument(
        "-sd", "--skip-download", action="store_true", help="Skip download step"
    )
    parser_range.set_defaults(func=cli_pipe_range)
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
        name=__name__,
        version=__version__,
        description=DESCRIPTION,
    )


if __name__ == "__main__":
    main()
