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
import itertools

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

def now() -> datetime:
    return datetime.now().replace(day=1,hour=0,minute=0,second=0,microsecond=0)


def grouper(n: int, iterable):
    iterable = iter(iterable)
    return iter(lambda: list(itertools.islice(iterable, n)), [])


def mkdir(name: str, filename: str, base_dir: str | None) -> str:
    base_dir = os.getcwd() if base_dir is None else base_dir
    dir_path = os.path.join(base_dir, name)
    if not os.path.isdir(dir_path):
        log.debug("new directory: %s", dir_path)
        os.makedirs(dir_path)
    return os.path.join(dir_path, filename)


def daterange(from_month: datetime, to_month: datetime) -> str:
    month = from_month
    while month <=  to_month:
        yield month.strftime('%Y-%m')
        month += relativedelta(months=1)


async def do_ida_single_month(session, base_url: str, base_dir: str, name: str, month: str|None, exact: str|None) -> None:
    url = base_url + '/download'
    target_file = name + '_' + month + '.dat' if not exact else exact
    params = {'path': '/' + name, 'files': target_file}
    async with session.get(url, params=params) as resp:
        if resp.status == 404:
            log.warn("No monthly file exits: %s", target_file)
            return
        log.info("GET %s [%d OK]", resp.url, resp.status)
        contents = await resp.text()
    file_path = await asyncio.to_thread(mkdir, name, target_file, base_dir)
    async with aiofiles.open(file_path, mode='w') as f:
        log.info("writing %s", file_path)
        await f.write(contents)

async def do_ida_since(session, base_url: str, base_dir: str, name: str, since: datetime, until: datetime, N: int) -> None:
    for grp in grouper(N, daterange(since, until)):
        tasks = [asyncio.create_task(do_ida_single_month(session, base_url, base_dir, name, m, None)) for m in grp]
        await asyncio.gather(*tasks)

# ===========
# Generic API
# ===========

async def ida_single_month(base_url: str, base_dir: str, name: str, month: str|None, exact:str|None) -> None:
    async with aiohttp.ClientSession() as session:
        if not exact:
            month = month.strftime('%Y-%m')
        await do_ida_single_month(session, base_url, base_dir, name, month, exact)


async def ida_year(base_url: str, base_dir: str, name: str, year: datetime, concurrent: int) -> None:
    year = year.replace(month=1, day=1)
    async with aiohttp.ClientSession() as session:
        for grp in grouper(concurrent, range(0,12)):
            tasks = [asyncio.create_task(do_ida_single_month(session, base_url, base_dir, name, 
                (year + relativedelta(months=m)).strftime('%Y-%m'), None)) for m in grp]
            await asyncio.gather(*tasks)


async def ida_since(base_url: str, base_dir: str, name: str, since: datetime, until: datetime, concurrent: int) -> None:
    async with aiohttp.ClientSession() as session:
        await do_ida_since(session, base_url, base_dir, name, since, until, concurrent)


async def ida_all(base_url: str, base_dir: str, from_phot: int, to_phot: int, since: datetime, until: datetime, concurrent: int) -> None:
    async with aiohttp.ClientSession() as session:
        for i in range(from_phot,  to_phot+1):
            name = 'stars' + str(i)
            await do_ida_since(session, base_url, base_dir, name, since, until, concurrent)


# ================================
# COMMAND LINE INTERFACE FUNCTIONS
# ================================

async def cli_ida_single_month(base_url: str, args: Namespace) -> None:
    await ida_single_month(
        base_url = base_url,
        base_dir = args.out_dir,
        name = args.name,
        month = args.month,
        exact = args.exact
    )


async def cli_ida_year(base_url: str, args: Namespace) -> None:
    await ida_year(
        base_url = base_url,
        base_dir = args.out_dir,
        name = args.name,
        year = args.year,
        concurrent = args.concurrent,
    )


async def cli_ida_since(base_url: str, args: Namespace) -> None:
    await ida_since(
        base_url = base_url,
        base_dir = args.out_dir, 
        name = args.name, 
        since = args.since, 
        until = args.until, 
        concurrent = args.concurrent
    )


async def cli_ida_all(base_url: str, args: Namespace) -> None:
    await ida_all(
        base_url = base_url,
        base_dir = args.out_dir,
        from_phot = args.from_var,
        to_phot = args.to,
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
    group2 = parser_month.add_mutually_exclusive_group(required=True)
    group2.add_argument('-e', '--exact', type=str, default=None, help='Specific monthly file name')
    group2.add_argument('-m', '--month',  type=vmonth, default=None, metavar='<YYYY-MM>', help='Year and Month')
    parser_year = subparser.add_parser('year', help='Download a year of monthly files')
    parser_year.add_argument('-n', '--name', type=str, required=True, help='Photometer name')
    parser_year.add_argument('-y', '--year', type=vyear, metavar='<YYYY>', required=True, help='Year')
    parser_year.add_argument('-o', '--out-dir', type=str, default=None, help='Output base directory')
    parser_year.add_argument('-c', '--concurrent', type=int, metavar='<N>', choices=[1,2,3,4], default=4, help='Number of concurrent downloads (defaults to %(default)s)')
    parser_since = subparser.add_parser('since', help='Download since a given month until another')
    parser_since.add_argument('-n', '--name', type=str, required=True, help='Photometer name')
    parser_since.add_argument('-s', '--since',  type=vmonth, required=True, metavar='<YYYY-MM>', help='Year and Month')
    parser_since.add_argument('-u', '--until',  type=vmonth, default=now(), metavar='<YYYY-MM>', help='Year and Month (defaults to %(default)s')
    parser_since.add_argument('-o', '--out-dir', type=str, default=None, help='Output base directory')
    parser_since.add_argument('-c', '--concurrent', type=int, metavar='<N>', choices=[1,2,4,6,8], default=4, help='Number of concurrent downloads (defaults to %(default)s)')
    parser_all = subparser.add_parser('all', help='Download all photometers from a given month until another')
    parser_all.add_argument('-f', '--from', dest='from_var', type=int, required=True, help='From photometer number')
    parser_all.add_argument('-t', '--to', type=int, required=True, help='To photometer number')
    parser_all.add_argument('-s', '--since',  type=vmonth, required=True, metavar='<YYYY-MM>', help='Year and Month')
    parser_all.add_argument('-u', '--until',  type=vmonth, default=now(), metavar='<YYYY-MM>', help='Year and Month (defaults to %(default)s')
    parser_all.add_argument('-o', '--out-dir', type=str, default=None, help='Output base directory')
    parser_all.add_argument('-c', '--concurrent', type=int, metavar='<N>', choices=[1,2,3,4], default=4, help='Number of concurrent downloads (defaults to %(default)s)')
    return parser


CMD_TABLE = {
    'month': cli_ida_single_month,
    'year': cli_ida_year,
    'since': cli_ida_since,
    'all': cli_ida_all,
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
