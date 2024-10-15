# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# -----------------------
# Standard Python imports
# ----------------------

import os
import asyncio
import logging


from datetime import datetime
from argparse import Namespace, ArgumentParser

# -------------------
# Third party imports
# -------------------

import decouple
import aiohttp
import aiofiles


from lica.cli import async_execute
from lica.validators import vmonth
from lica.misc import group
from lica.typing import OptStr

# --------------
# local imports
# -------------

from . import __version__
from .utils import cur_month, prev_month, month_range, makedirs, name_month

# ----------------
# Module constants
# ----------------

DESCRIPTION = "Get TESS-W IDA monthly files from NextCloud server"

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger(__name__.split(".")[-1])

# -------------------
# Auxiliary functions
# -------------------


async def do_ida_single(
    session, base_url: str, ida_base_dir: str, name: str, month: OptStr, exact: OptStr
) -> None:
    url = base_url + "/download"
    target_file = name + "_" + month + ".dat" if not exact else exact
    params = {"path": "/" + name, "files": target_file}
    _, month1 = name_month(target_file)
    async with session.get(url, params=params) as resp:
        if resp.status == 404:
            log.warn("[%s] No monthly file exits: %s", name, target_file)
            return
        log.info("[%s] [%s] GET %s [%d OK]", name, month1, resp.url, resp.status)
        contents = await resp.text()
    full_dir_path = await asyncio.to_thread(makedirs, ida_base_dir, name)
    file_path = os.path.join(full_dir_path, target_file)
    async with aiofiles.open(file_path, mode="w") as f:
        log.info("[%s] [%s] Writing %s", name, month1, file_path)
        await f.write(contents)


async def do_ida_range(
    session,
    base_url: str,
    ida_base_dir: str,
    name: str,
    since: datetime,
    until: datetime,
    N: int,
) -> None:
    for grp in group(N, month_range(since, until)):
        tasks = [
            asyncio.create_task(
                do_ida_single(session, base_url, ida_base_dir, name, m, None)
            )
            for m in grp
        ]
        await asyncio.gather(*tasks)


# ===========
# Generic API
# ===========


async def download_ida_single(
    base_url: str,
    ida_base_dir: str,
    name: str,
    month: OptStr,
    exact: OptStr,
    timeout: int,
) -> None:
    timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        if not exact:
            month = month.strftime("%Y-%m")
        await do_ida_single(session, base_url, ida_base_dir, name, month, exact)


async def download_ida_range(
    base_url: str,
    ida_base_dir: str,
    name: str,
    since: datetime,
    until: datetime,
    concurrent: int,
    timeout: int,
) -> None:
    timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        await do_ida_range(
            session, base_url, ida_base_dir, name, since, until, concurrent
        )


async def ida_photometers(
    base_url: str,
    ida_base_dir: str,
    rang: list[int],
    seq: list[int],
    since: datetime,
    until: datetime,
    concurrent: int,
    timeout: int,
) -> None:
    timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        rang = sorted(rang) if rang is not None else None
        seq = sorted(seq) if seq is not None else None
        if rang:
            for i in range(rang[0], rang[1] + 1):
                name = "stars" + str(i)
                await do_ida_range(
                    session, base_url, ida_base_dir, name, since, until, concurrent
                )
        else:
            for i in seq:
                name = "stars" + str(i)
                await do_ida_range(
                    session, base_url, ida_base_dir, name, since, until, concurrent
                )


# ================================
# COMMAND LINE INTERFACE FUNCTIONS
# ================================


async def cli_ida_single(base_url: str, args: Namespace) -> None:
    await download_ida_single(
        base_url=base_url,
        ida_base_dir=args.out_dir,
        name=args.name,
        month=args.month,
        exact=args.exact,
        timeout=args.timeout,
    )


async def cli_ida_range(base_url: str, args: Namespace) -> None:
    await download_ida_range(
        base_url=base_url,
        ida_base_dir=args.out_dir,
        name=args.name,
        since=args.since,
        until=args.until,
        concurrent=args.concurrent,
        timeout=args.timeout,
    )


async def cli_ida_photometers(base_url: str, args: Namespace) -> None:
    await ida_photometers(
        base_url=base_url,
        ida_base_dir=args.out_dir,
        seq=args.list,
        rang=args.range,
        since=args.since,
        until=args.until,
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
        "-o", "--out-dir", type=str, default=None, help="Output base directory"
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
        "-o", "--out-dir", type=str, default=None, help="Output IDA base directory"
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
    parser_phot = subparser.add_parser(
        "photometers", help="Download a month range for selected photometers"
    )
    group2 = parser_phot.add_mutually_exclusive_group(required=True)
    group2.add_argument(
        "-l",
        "--list",
        type=int,
        default=None,
        nargs="+",
        metavar="<N>",
        help="Photometer number list",
    )
    group2.add_argument(
        "-r",
        "--range",
        type=int,
        default=None,
        metavar="<N>",
        nargs=2,
        help="Photometer number range",
    )
    parser_phot.add_argument(
        "-s",
        "--since",
        type=vmonth,
        default=prev_month(),
        metavar="<YYYY-MM>",
        help="Year and Month (defaults to %(default)s",
    )
    parser_phot.add_argument(
        "-u",
        "--until",
        type=vmonth,
        default=cur_month(),
        metavar="<YYYY-MM>",
        help="Year and Month (defaults to %(default)s",
    )
    parser_phot.add_argument(
        "-o", "--out-dir", type=str, default=None, help="Output IDA base directory"
    )
    parser_phot.add_argument(
        "-c",
        "--concurrent",
        type=int,
        metavar="<N>",
        choices=[1, 2, 3, 4],
        default=4,
        help="Number of concurrent downloads (defaults to %(default)s)",
    )
    parser_phot.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="HTTP timeout in seconds (defaults to %(default)s) sec.",
    )
    return parser


CMD_TABLE = {
    "single": cli_ida_single,
    "range": cli_ida_range,
    "photometers": cli_ida_photometers,
}


async def cli_get_ida(args: Namespace) -> None:
    """The main entry point specified by pyproject.toml"""
    base_url = decouple.config("IDA_URL")
    func = CMD_TABLE[args.command]
    await func(base_url, args)
    log.info("done!")


def main() -> None:
    async_execute(
        main_func=cli_get_ida,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description=DESCRIPTION,
    )


if __name__ == "__main__":
    main()
