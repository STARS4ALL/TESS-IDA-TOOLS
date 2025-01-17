# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# -----------------------
# Standard Python imports
# ----------------------

import os
import io
import csv
import math
import asyncio
import logging
import functools

from datetime import datetime
from argparse import Namespace, ArgumentParser
from typing import Dict, Tuple, Sequence, Optional, Any

# -------------------
# Third party imports
# -------------------

import decouple
import aiohttp
import aiofiles


from lica.cli import async_execute
from lica.misc import group
from lica.typing import OptStr

# --------------
# local imports
# -------------

from . import __version__
from .utils import parser as prs
from .utils.utils import month_range, makedirs, name_month

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


def distance(
    coords_A: Tuple[float, float], coords_B: Tuple[float, float]
) -> Optional[float]:
    """
    Compute approximate geographical distance (arc) [meters] between two points on Earth
    Coods_A and Coords_B are tuples (longitude, latitude)
    Accurate for small distances only
    """
    EARTH_RADIUS = 6371009.0  # in meters

    long_A = coords_A[0]
    long_B = coords_B[0]
    lat_A = coords_A[1]
    lat_B = coords_B[1]
    try:
        delta_long = math.radians(long_A - long_B)
        delta_lat = math.radians(lat_A - lat_B)
        mean_lat = math.radians((lat_A + lat_B) / 2)
        result = round(
            EARTH_RADIUS
            * math.sqrt(delta_lat**2 + (math.cos(mean_lat) * delta_long) ** 2),
            0,
        )
    except TypeError:
        log.error("Algo malo pasṕ")
        result = None
    return result


def filter_by_distance(
    longitude: float, latitude: float, radius: float, item: Dict[str, Sequence[int]]
) -> bool:
    d = distance((item["longitude"], item["latitude"]), (longitude, latitude))
    return True if d <= radius else False


def float_coords(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts coordinates in items read by CSV reader into floating values
    """
    item["longitude"] = float(item["longitude"])
    item["latitude"] = float(item["latitude"])
    return item


async def do_get_location_list(base_url: str, ida_base_dir: str, timeout: int) -> Sequence:
    target_file = "geolist.csv"
    url = base_url + "/download"
    params = {"path": "/", "files": target_file}
    result = []
    timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as resp:
            if resp.status == 404:
                log.warn("No such file exits: %s", target_file)
                return result
            log.info("[%s] GET %s [%d OK]", target_file, resp.url, resp.status)
            contents = await resp.text()
            with io.StringIO(contents) as fd:
                # reader = csv.reader(fd, delimiter=';')
                reader = csv.DictReader(fd, delimiter=";")
                result = list(map(float_coords, reader))
    return result


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


async def ida_names_by_location(
    base_url: str,
    ida_base_dir: str,
    lon: float,
    lat: float,
    radius: float,
    timeout: int,
) -> Tuple[str]:
    by_distance = functools.partial(filter_by_distance, lon, lat, 1000 * radius)
    result = await do_get_location_list(base_url, ida_base_dir, timeout)
    return tuple(item["name"] for item in filter(by_distance, result))


def ida_names_by_seq_or_range(seq: Sequence[int], rang: Sequence[int]) -> Tuple[str]:
    if seq is not None:
        result = tuple("stars" + str(i) for i in sorted(seq))
    else:
        rang = sorted(rang)
        result = tuple("stars" + str(i) for i in range(rang[0], rang[1] + 1))
    return result


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
    rang: Sequence[int],
    seq: Sequence[int],
    since: datetime,
    until: datetime,
    concurrent: int,
    timeout: int,
) -> None:
    for name in ida_names_by_seq_or_range(seq, rang):
        await download_ida_range(base_url, ida_base_dir, name, since, until, concurrent, timeout)


async def ida_location(
    base_url: str,
    ida_base_dir: str,
    lon: float,
    lat: float,
    radius: float,
    since: datetime,
    until: datetime,
    concurrent: int,
    timeout: int,
) -> None:
    names = await ida_names_by_location(
        base_url, ida_base_dir, lon, lat, radius, timeout
    )
    for name in names:
        await download_ida_range(base_url, ida_base_dir, name, since, until, concurrent, timeout)


# ================================
# COMMAND LINE INTERFACE FUNCTIONS
# ================================


async def cli_ida_single(args: Namespace) -> None:
    await download_ida_single(
        base_url=args.base_url,
        ida_base_dir=args.out_dir,
        name=args.name,
        month=args.month,
        exact=args.exact,
        timeout=args.timeout,
    )


async def cli_ida_range(args: Namespace) -> None:
    await download_ida_range(
        base_url=args.base_url,
        ida_base_dir=args.out_dir,
        name=args.name,
        since=args.since,
        until=args.until,
        concurrent=args.concurrent,
        timeout=args.timeout,
    )


async def cli_ida_photometers(args: Namespace) -> None:
    await ida_photometers(
        base_url=args.base_url,
        ida_base_dir=args.out_dir,
        seq=args.list,
        rang=args.range,
        since=args.since,
        until=args.until,
        concurrent=args.concurrent,
        timeout=args.timeout,
    )


async def cli_ida_location(args: Namespace) -> None:
    await ida_location(
        base_url=args.base_url,
        ida_base_dir=args.out_dir,
        lon=args.longitude,
        lat=args.latitude,
        radius=args.radius,
        since=args.since,
        until=args.until,
        concurrent=args.concurrent,
        timeout=args.timeout,
    )


def add_args(parser: ArgumentParser) -> ArgumentParser:
    # Now parse the application specific parts
    subparser = parser.add_subparsers(dest="command")
    parser_single = subparser.add_parser(
        "single",
        parents=[prs.name(), prs.out_dir("IDA"), prs.mon_single(), prs.timeout()],
        help="Download single monthly file from a photometer",
    )
    parser_single.set_defaults(func=cli_ida_single)
    parser_range = subparser.add_parser(
        "range",
        parents=[prs.name(), prs.out_dir("IDA"), prs.mon_range(), prs.concurrent()],
        help="Download a month range from a photometer",
    )
    parser_range.set_defaults(func=cli_ida_range)
    parser_phots = subparser.add_parser(
        "photometers",
        parents=[
            prs.phot_range(),
            prs.out_dir("IDA"),
            prs.mon_range(),
            prs.concurrent(),
        ],
        help="Download a month range for selected photometers",
    )
    parser_phots.set_defaults(func=cli_ida_photometers)
    parser_location = subparser.add_parser(
        "near",
        parents=[prs.location(), prs.out_dir("IDA"), prs.mon_range(), prs.concurrent()],
        help="Download a month range from photometers near a given location",
    )
    parser_location.set_defaults(func=cli_ida_location)
    return parser


async def cli_get_ida(args: Namespace) -> None:
    """The main entry point specified by pyproject.toml"""
    args.base_url = decouple.config("IDA_URL")
    await args.func(args)
    log.info("done!")


def main() -> None:
    async_execute(
        main_func=cli_get_ida,
        add_args_func=add_args,
        name="tess-ida-get",
        version=__version__,
        description=DESCRIPTION,
    )


if __name__ == "__main__":
    main()
