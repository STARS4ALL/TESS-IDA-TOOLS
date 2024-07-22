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
import datetime
import itertools

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

def grouper(n, iterable):
    iterable = iter(iterable)
    return iter(lambda: list(itertools.islice(iterable, n)), [])


def mkdir(name: str, filename: str, base_dir: str | None) -> str:
    base_dir = os.getcwd() if base_dir is None else base_dir
    dir_path = os.path.join(os.getcwd(), name)
    if not os.path.isdir(dir_path):
        log.debug("new directory: %s", dir_path)
        os.mkdir(dir_path)
    return os.path.join(dir_path, filename)


def daterange(from_month: datetime.datetime, to_month: datetime.datetime) -> str:
    month = from_month
    while month <=  to_month:
        yield month.strftime('%Y-%m')
        month += relativedelta(months=1)


async def do_ida_single_month(session, base_url: str, name: str, month: str, specific: bool = False) -> None:
    url = base_url + '/download'
    target_file = name + '_' + month + '.dat' if not specific else month
    params = {'path': '/' + name, 'files': target_file}
    async with session.get(url, params=params) as resp:
        if resp.status == 404:
            log.warn("No monthly file exits: %s", target_file)
            return
        log.info("GET %s [%d OK]", resp.url, resp.status)
        contents = await resp.text()
    file_path = await asyncio.to_thread(mkdir, name, target_file, base_dir=None)
    async with aiofiles.open(file_path, mode='w') as f:
        log.info("writing %s", file_path)
        await f.write(contents)


async def ida_single_month(base_url: str, args) -> None:
    name = args.name
    async with aiohttp.ClientSession() as session:
        if args.exact:
            await do_ida_single_month(session, base_url, name, args.exact, specific=True)
        else:
            month = args.month.strftime('%Y-%m')
            await do_ida_single_month(session, base_url, name, month)


async def ida_year(base_url: str, args) -> None:
    year = args.year.replace(month=1, day=1)
    name = args.name
    async with aiohttp.ClientSession() as session:
        for grp in grouper(4, range(0,12)):
            tasks = [asyncio.create_task(do_ida_single_month(session, base_url, name, 
                (year + relativedelta(months=m)).strftime('%Y-%m'))) for m in grp]
            await asyncio.gather(*tasks)


async def ida_since(base_url: str, args) -> None:
    name = args.name
    log.info("month_list %s", month_list)
    async with aiohttp.ClientSession() as session:
        for grp in grouper(4, daterange(args.since, args.until)):
            tasks = [asyncio.create_task(do_ida_single_month(session, base_url, name, m)) for m in grp]
            await asyncio.gather(*tasks)


def ida_all(base_url: str, args) -> None:
    S1 = args.from_var
    S2 = args.to
    M2 = args.until
    for i in range(S1,S2+1):
        name = 'stars' + str(i)
        M1 = args.since
        while M1 <=  M2:
            cur_month = M1.strftime('%Y-%m')
            do_ida_single_month(base_url, name, cur_month)
            M1 += relativedelta(months=1)

# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================

def now():
    return datetime.datetime.now().replace(day=1,hour=0,minute=0,second=0,microsecond=0)

def add_args(parser):
     # Now parse the application specific parts
    subparser = parser.add_subparsers(dest='command')
    parser_month = subparser.add_parser('month', help='Download single monthly file')
    parser_month.add_argument('-n', '--name', type=str, required=True, help='Photometer name')
    group2 = parser_month.add_mutually_exclusive_group(required=True)
    group2.add_argument('-e', '--exact', type=str, help='Specific monthly file name')
    group2.add_argument('-m', '--month',  type=vmonth, metavar='<YYYY-MM>', help='Year and Month')
    parser_year = subparser.add_parser('year', help='Download a year of monthly files')
    parser_year.add_argument('-n', '--name', type=str, required=True, help='Photometer name')
    parser_year.add_argument('-y', '--year', type=vyear, metavar='<YYYY>', required=True, help='Year')
    parser_from = subparser.add_parser('since', help='Download since a given month until another')
    parser_from.add_argument('-n', '--name', type=str, required=True, help='Photometer name')
    parser_from.add_argument('-s', '--since',  type=vmonth, required=True, metavar='<YYYY-MM>', help='Year and Month')
    parser_from.add_argument('-u', '--until',  type=vmonth, default=now(), metavar='<YYYY-MM>', help='Year and Month (defaults to current month)')
    parser_all = subparser.add_parser('all', help='Download all photometers from a given month until another')
    parser_all.add_argument('-f', '--from', dest='from_var', type=int, required=True, help='From photometer number')
    parser_all.add_argument('-t', '--to', type=int, required=True, help='To photometer number')
    parser_all.add_argument('-s', '--since',  type=vmonth, required=True, metavar='<YYYY-MM>', help='Year and Month')
    parser_all.add_argument('-u', '--until',  type=vmonth, default=now(), metavar='<YYYY-MM>', help='Year and Month (defaults to current month)')
    return parser

# ================    
# MAIN ENTRY POINT
# ================


CMD_TABLE = {
    'month': ida_single_month,
    'year': ida_year,
    'since': ida_since,
    'all': ida_all,
}

async def get_ida(args):
    '''The main entry point specified by pyproject.toml'''
    base_url = decouple.config('IDA_URL')
    func = CMD_TABLE[args.command]
    await func(base_url, args)
    log.info("done!")


def main():
    async_execute(main_func=get_ida, 
        add_args_func=add_args, 
        name=__name__, 
        version=__version__,
        description = DESCRIPTION
    )

if __name__ == '__main__':
    main()
