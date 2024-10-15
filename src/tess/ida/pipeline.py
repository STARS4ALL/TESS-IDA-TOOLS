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
from lica.validators import vmonth
from lica.typing import OptStr

# --------------
# local imports
# -------------

from . import __version__
from .dbase import aux_dbase_load, aux_dbase_save
from .utils import cur_month, prev_month
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


async def cli_pipe_single(base_url: str, args: Namespace) -> None:
    await pipe_single(
        base_url=base_url,
        ida_base_dir=args.in_dir,
        ecsv_base_dir=args.out_dir,
        name=args.name,
        month=args.month,
        exact=args.exact,
        fix=True if args.fix else False,
        timeout=args.timeout,
    )


async def cli_pipe_range(base_url: str, args: Namespace) -> None:
    await pipe_range(
        base_url=base_url,
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
        "single", help="Download single monthly file from a photometer"
    )
    parser_single.add_argument(
        "-n", "--name", type=str, required=True, help="Photometer name"
    )
    parser_single.add_argument(
        "-i",
        "--in-dir",
        type=str,
        default=None,
        help="IDA download files base directory",
    )
    parser_single.add_argument(
        "-o", "--out-dir", type=str, default=None, help="Output ECSV base directory"
    )
    parser_single.add_argument(
        "-f", "--fix", action="store_true", help="Fix unknown location"
    )
    parser_single.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="HTTP timeout in seconds (defaults to %(default)s) sec.",
    )
    group1 = parser_single.add_mutually_exclusive_group(required=True)
    group1.add_argument(
        "-e", "--exact", type=str, default=None, help="Specific monthly file name"
    )
    group1.add_argument(
        "-m",
        "--month",
        type=vmonth,
        default=None,
        metavar="<YYYY-MM>",
        help="Year and Month",
    )
    parser_range = subparser.add_parser(
        "range", help="Download a month range from a photometer"
    )
    parser_range.add_argument(
        "-n", "--name", type=str, required=True, help="Photometer name"
    )
    parser_range.add_argument(
        "-s",
        "--since",
        type=vmonth,
        default=prev_month(),
        metavar="<YYYY-MM>",
        help="Year and Month (defaults to %(default)s",
    )
    parser_range.add_argument(
        "-u",
        "--until",
        type=vmonth,
        default=cur_month(),
        metavar="<YYYY-MM>",
        help="Year and Month (defaults to %(default)s",
    )
    parser_range.add_argument(
        "-i",
        "--in-dir",
        type=str,
        default=None,
        help="IDA download files base directory",
    )
    parser_range.add_argument(
        "-o", "--out-dir", type=str, default=None, help="Output IDA base directory"
    )
    parser_range.add_argument(
        "-sd", "--skip-download", action="store_true", help="Skip download step"
    )
    parser_range.add_argument(
        "-on",
        "--out-filename",
        type=str,
        default=None,
        help="Optional output combined file name",
    )
    parser_range.add_argument(
        "-f", "--fix", action="store_true", help="Fix unknown location"
    )
    parser_range.add_argument(
        "-c",
        "--concurrent",
        type=int,
        metavar="<N>",
        choices=[1, 2, 4, 6, 8],
        default=4,
        help="Number of concurrent downloads (defaults to %(default)s)",
    )
    parser_range.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="HTTP timeout in seconds (defaults to %(default)s) sec.",
    )
    return parser


CMD_TABLE = {
    "single": cli_pipe_single,
    "range": cli_pipe_range,
}


async def cli_pipeline(args: Namespace) -> None:
    """The main entry point specified by pyproject.toml"""
    base_url = decouple.config("IDA_URL")
    func = CMD_TABLE[args.command]
    aux_dbase_load()
    try:
        await func(base_url, args)
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
