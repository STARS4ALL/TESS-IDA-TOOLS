# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#-----------------------
# Standard Python imports
# ----------------------

import os
import asyncio
import logging


from datetime import datetime
from argparse import Namespace

# -------------------
# Third party imports
# -------------------

import decouple
import aiohttp
import aiofiles

from dateutil.relativedelta import relativedelta

from lica.cli import async_execute
from lica.validators import vmonth, vyear

#--------------
# local imports
# -------------

from .. import __version__
from .utils import cur_month, prev_month, group, month_range, makedirs

# ----------------
# Module constants
# ----------------

DESCRIPTION = "Get TESS-W IDA monthly files from NextCloud server"

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger(__name__.split('.')[-1])

# -------------------
# Auxiliary functions
# -------------------


async def do_ida_single_month(session, base_url: str, ida_base_dir: str, name: str, month: str|None, exact: str|None, timeout: int) -> None:
    url = base_url + '/download'
    target_file = name + '_' + month + '.dat' if not exact else exact
    params = {'path': '/' + name, 'files': target_file}
    async with session.get(url, params=params, timeout=timeout) as resp:
        if resp.status == 404:
            log.warn("No monthly file exits: %s", target_file)
            return
        log.info("GET %s [%d OK]", resp.url, resp.status)
        contents = await resp.text()
    full_dir_path = await asyncio.to_thread(makedirs, ida_base_dir, name)
    file_path = os.path.join(full_dir_path, target_file)
    async with aiofiles.open(file_path, mode='w') as f:
        log.info("writing %s", file_path)
        await f.write(contents)

async def do_ida_range(session, base_url: str, ida_base_dir: str, name: str, since: datetime, until: datetime, N: int, timeout: int) -> None:
    for grp in group(N, month_range(since, until)):
        tasks = [asyncio.create_task(do_ida_single_month(session, base_url, ida_base_dir, name, m, None, timeout)) for m in grp]
        await asyncio.gather(*tasks)

# ===========
# Generic API
# ===========

async def ida_single_month(base_url: str, ida_base_dir: str, name: str, month: str|None, exact:str|None, timeout:int = 4) -> None:
    async with aiohttp.ClientSession() as session:
        if not exact:
            month = month.strftime('%Y-%m')
        await do_ida_single_month(session, base_url, ida_base_dir, name, month, exact, timeout)


async def ida_year(base_url: str, ida_base_dir: str, name: str, year: datetime, concurrent: int, timeout:int = 4) -> None:
    year = year.replace(month=1, day=1)
    async with aiohttp.ClientSession() as session:
        for grp in group(concurrent, range(0,12)):
            tasks = [asyncio.create_task(do_ida_single_month(session, base_url, ida_base_dir, name, 
                (year + relativedelta(months=m)).strftime('%Y-%m'), None, timeout)) for m in grp]
            await asyncio.gather(*tasks)


async def ida_range(base_url: str, ida_base_dir: str, name: str, since: datetime, until: datetime, concurrent: int, timeout:int = 4) -> None:
    async with aiohttp.ClientSession() as session:
        await do_ida_range(session, base_url, ida_base_dir, name, since, until, concurrent, timeout)


async def ida_selected(base_url: str, ida_base_dir: str, rang: list[int], seq: list[int], since: datetime, until: datetime, concurrent: int, timeout:int = 4) -> None:
    async with aiohttp.ClientSession() as session:
        rang = sorted(rang) if rang is not None else None
        seq = sorted(seq) if seq is not None else None
        if rang:
            for i in range(rang[0],  rang[1]+1):
                name = 'stars' + str(i)
                await do_ida_range(session, base_url, ida_base_dir, name, since, until, concurrent, timeout)
        else:
            for i in seq:
                name = 'stars' + str(i)
                await do_ida_range(session, base_url, ida_base_dir, name, since, until, concurrent, timeout)

# ================================
# COMMAND LINE INTERFACE FUNCTIONS
# ================================

async def cli_ida_single_month(base_url: str, args: Namespace) -> None:
    await ida_single_month(
        base_url = base_url,
        ida_base_dir = args.out_dir,
        name = args.name,
        month = args.month,
        exact = args.exact
    )


async def cli_ida_year(base_url: str, args: Namespace) -> None:
    await ida_year(
        base_url = base_url,
        ida_base_dir = args.out_dir,
        name = args.name,
        year = args.year,
        concurrent = args.concurrent,
    )


async def cli_ida_range(base_url: str, args: Namespace) -> None:
    await ida_range(
        base_url = base_url,
        ida_base_dir = args.out_dir, 
        name = args.name, 
        since = args.since, 
        until = args.until, 
        concurrent = args.concurrent
    )


async def cli_ida_selected(base_url: str, args: Namespace) -> None:
    await ida_selected(
        base_url = base_url,
        ida_base_dir = args.out_dir,
        seq = args.list,
        rang = args.range,
        since = args.since,
        until = args.until,
        concurrent = args.concurrent
    )


def add_args(parser):
     # Now parse the application specific parts
    subparser = parser.add_subparsers(dest='command')
    parser_month = subparser.add_parser('month', help='Download single monthly file')
    parser_month.add_argument('-n', '--name', type=str, required=True, help='Photometer name')
    parser_month.add_argument('-o', '--out-dir', type=str, default=None, help='Output base directory')
    group1 = parser_month.add_mutually_exclusive_group(required=True)
    group1.add_argument('-e', '--exact', type=str, default=None, help='Specific monthly file name')
    group1.add_argument('-m', '--month',  type=vmonth, default=None, metavar='<YYYY-MM>', help='Year and Month')
    parser_year = subparser.add_parser('year', help='Download a year of monthly files')
    parser_year.add_argument('-n', '--name', type=str, required=True, help='Photometer name')
    parser_year.add_argument('-y', '--year', type=vyear, metavar='<YYYY>', required=True, help='Year')
    parser_year.add_argument('-o', '--out-dir', type=str, default=None, help='Output IDA base directory')
    parser_year.add_argument('-c', '--concurrent', type=int, metavar='<N>', choices=[1,2,3,4], default=4, help='Number of concurrent downloads (defaults to %(default)s)')
    parser_since = subparser.add_parser('range', help='Download from a month range')
    parser_since.add_argument('-n', '--name', type=str, required=True, help='Photometer name')
    parser_since.add_argument('-s', '--since',  type=vmonth, default=prev_month(), metavar='<YYYY-MM>', help='Year and Month (defaults to %(default)s')
    parser_since.add_argument('-u', '--until',  type=vmonth, default=cur_month(), metavar='<YYYY-MM>', help='Year and Month (defaults to %(default)s')
    parser_since.add_argument('-o', '--out-dir', type=str, default=None, help='Output IDA base directory')
    parser_since.add_argument('-c', '--concurrent', type=int, metavar='<N>', choices=[1,2,4,6,8], default=4, help='Number of concurrent downloads (defaults to %(default)s)')
    parser_sel = subparser.add_parser('selected', help='Download selected photometers in a month range')
    group2 = parser_sel.add_mutually_exclusive_group(required=True)
    group2.add_argument('-l', '--list', type=int, default=None, nargs='+', metavar='<N>', help='Photometer number list')
    group2.add_argument('-r', '--range', type=int, default=None, metavar='<N>', nargs=2, help='Photometer number range')
    parser_sel.add_argument('-s', '--since',  type=vmonth, default=prev_month(), metavar='<YYYY-MM>', help='Year and Month (defaults to %(default)s')
    parser_sel.add_argument('-u', '--until',  type=vmonth, default=cur_month(), metavar='<YYYY-MM>', help='Year and Month (defaults to %(default)s')
    parser_sel.add_argument('-o', '--out-dir', type=str, default=None, help='Output IDA base directory')
    parser_sel.add_argument('-c', '--concurrent', type=int, metavar='<N>', choices=[1,2,3,4], default=4, help='Number of concurrent downloads (defaults to %(default)s)')
    return parser


CMD_TABLE = {
    'month': cli_ida_single_month,
    'year': cli_ida_year,
    'range': cli_ida_range,
    'selected': cli_ida_selected,
}

async def cli_get_ida(args: Namespace) -> None:
    '''The main entry point specified by pyproject.toml'''
    base_url = decouple.config('IDA_URL')
    func = CMD_TABLE[args.command]
    await func(base_url, args)
    log.info("done!")


def main() -> None:
    async_execute(main_func=cli_get_ida, 
        add_args_func=add_args, 
        name=__name__, 
        version=__version__,
        description = DESCRIPTION
    )

if __name__ == '__main__':
    main()
