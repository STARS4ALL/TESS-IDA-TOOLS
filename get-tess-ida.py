#!/bin/env python3
# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# -----------------------
# Standard Python imports
# ----------------------

import os
import sys
import logging
import logging.handlers
from datetime import datetime
import argparse
from argparse import Namespace
from typing import Union

# -------------------
# Third party imports
# -------------------

import decouple
import requests
from dateutil.relativedelta import relativedelta

# ----------------
# Module constants
# ----------------

DESCRIPTION = "Get TESS-W IDA monthly files from NextCloud server"
__version__ = "1.0.1"

OptStr = Union[str, None]

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger(__name__.split('.')[-1])

# -------------------
# Auxiliary functions
# -------------------


def vmonth(datestr: str) -> datetime:
    return datetime.strptime(datestr, '%Y-%m')


def vyear(datestr: str) -> datetime:
    return datetime.strptime(datestr, '%Y')


def cur_month() -> datetime:
    return datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def prev_month() -> datetime:
    month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return month - relativedelta(months=1)


def to_phot_dir(base_dir: str | None, name: str) -> str:
    cwd = os.getcwd()
    base_dir = cwd if base_dir is None else base_dir
    base_dir = os.path.join(cwd, base_dir) if not os.path.isabs(
        base_dir) else base_dir
    full_dir_path = os.path.join(base_dir, name)
    return full_dir_path


def makedirs(base_dir: OptStr, name: str) -> str:
    full_dir_path = to_phot_dir(base_dir, name)
    if not os.path.isdir(full_dir_path):
        os.makedirs(full_dir_path)
    return full_dir_path


def name_month(ida_file_path: str) -> tuple:
    name = os.path.basename(os.path.dirname(ida_file_path))
    month = os.path.splitext(os.path.basename(ida_file_path))[0].split('_')[1]
    return name, month

# --------------
# Work functions
# --------------


def do_ida_single_month(base_url: str, ida_base_dir: str, name: str, month: OptStr, exact: OptStr, timeout: int) -> None:
    url = base_url + '/download'
    target_file = name + '_' + month + '.dat' if not exact else exact
    _, month1 = name_month(target_file)
    params = {'path': '/' + name, 'files': target_file}
    resp = requests.get(url, params=params, timeout=timeout)
    if resp.status_code == 404:
        log.warning("[%s] [%s] No monthly file exits: %s",
                    name, month1, target_file)
        return
    resp.raise_for_status()  # catch other unexpected return code
    log.info("[%s] [%s] GET %s [%d OK]", name,
             month1, resp.url, resp.status_code)
    contents = resp.text
    full_dir_path = makedirs(ida_base_dir, name)
    file_path = os.path.join(full_dir_path, target_file)
    with open(file_path, mode='w') as f:
        log.info("[%s] [%s] Writing %s", name, month1, file_path)
        f.write(contents)

# ================================
# COMMAND LINE INTERFACE FUNCTIONS
# ================================


def cli_ida_single(base_url: str, args: Namespace) -> None:
    month = args.month.strftime('%Y-%m') if not args.exact else None
    do_ida_single_month(
        base_url=base_url,
        ida_base_dir=args.out_dir,
        name=args.name,
        month=month,
        exact=args.exact,
        timeout=4
    )


def cli_ida_range(base_url: str, args: Namespace) -> None:
    month = args.since
    while month <= args.until:
        do_ida_single_month(
            base_url=base_url,
            ida_base_dir=args.out_dir,
            name=args.name,
            month=month.strftime('%Y-%m'),
            exact=None,
            timeout=4
        )
        month += relativedelta(months=1)


def cli_ida_photometers(base_url: str, args: Namespace) -> None:
    rang = sorted(args.range) if args.range is not None else None
    seq = sorted(args.list) if args.list is not None else None
    if rang:
        for i in range(rang[0],  rang[1]+1):
            args.name = 'stars' + str(i)
            cli_ida_range(base_url, args)
    else:
        for i in seq:
            args.name = 'stars' + str(i)
            cli_ida_range(base_url, args)

# =================
# LOGGER AND PARSER
# =================


def configure_log(args: Namespace):
    '''Configure the root logger'''
    if args.verbose:
        level = logging.DEBUG
    elif args.quiet:
        level = logging.WARNING
    else:
        level = logging.INFO
    # set the root logger level
    log = logging.getLogger()
    log.setLevel(level)
    # Log formatter
    fmt = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)-4s] %(message)s')
    # create console handler and set level to debug
    if args.console:
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        ch.setLevel(logging.DEBUG)
        log.addHandler(ch)
    # Create a file handler suitable for logrotate usage
    if args.log_file:
        fh = logging.handlers.WatchedFileHandler(args.log_file)
        #fh = logging.handlers.TimedRotatingFileHandler(args.log_file, when='midnight', interval=1, backupCount=365)
        fh.setFormatter(fmt)
        fh.setLevel(logging.DEBUG)
        log.addHandler(fh)


def args_parser(name: str, version: str, description: str) -> None:
    # create the top-level parser with generic options
    parser = argparse.ArgumentParser(prog=name, description=description)
    parser.add_argument('--version', action='version',
                        version='{0} {1}'.format(name, version))
    parser.add_argument('--console', action='store_true',
                        help='Log to vanilla console.')
    parser.add_argument('--log-file', type=str,
                        metavar="<FILE>", default=None, help='Log to file.')
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('--verbose', action='store_true',
                        help='Verbose output.')
    group1.add_argument('--quiet',   action='store_true', help='Quiet output.')
    # Now parse the application specific parts
    subparser = parser.add_subparsers(dest='command')
    parser_single = subparser.add_parser(
        'single', help='Download single monthly file from a photometer')
    parser_single.add_argument(
        '-n', '--name', type=str, required=True, help='Photometer name')
    parser_single.add_argument(
        '-o', '--out-dir', type=str, default=None, help='Output base directory')
    group1 = parser_single.add_mutually_exclusive_group(required=True)
    group1.add_argument('-e', '--exact', type=str,
                        default=None, help='Specific monthly file name')
    group1.add_argument('-m', '--month',  type=vmonth,
                        default=None, metavar='<YYYY-MM>', help='Year and Month')
    parser_range = subparser.add_parser(
        'range', help='Download a month range from a photometer')
    parser_range.add_argument('-n', '--name', type=str,
                              required=True, help='Photometer name')
    parser_range.add_argument('-s', '--since',  type=vmonth, default=prev_month(
    ), metavar='<YYYY-MM>', help='Year and Month (defaults to %(default)s')
    parser_range.add_argument('-u', '--until',  type=vmonth, default=cur_month(
    ), metavar='<YYYY-MM>', help='Year and Month (defaults to %(default)s')
    parser_range.add_argument(
        '-o', '--out-dir', type=str, default=None, help='Output IDA base directory')
    parser_phot = subparser.add_parser(
        'photometers', help='Download a month range from selected photometers')
    group2 = parser_phot.add_mutually_exclusive_group(required=True)
    group2.add_argument('-l', '--list', type=int, default=None,
                        nargs='+', metavar='<N>', help='Photometer number list')
    group2.add_argument('-r', '--range', type=int, default=None,
                        metavar='<N>', nargs=2, help='Photometer number range')
    parser_phot.add_argument('-s', '--since',  type=vmonth, default=prev_month(
    ), metavar='<YYYY-MM>', help='Year and Month (defaults to %(default)s')
    parser_phot.add_argument('-u', '--until',  type=vmonth, default=cur_month(),
                             metavar='<YYYY-MM>', help='Year and Month (defaults to %(default)s')
    parser_phot.add_argument('-o', '--out-dir', type=str,
                             default=None, help='Output IDA base directory')
    return parser

# =============
# MAIN FUNCTION
# =============


CMD_TABLE = {
    'single': cli_ida_single,
    'range': cli_ida_range,
    'photometers': cli_ida_photometers,
}


def main() -> None:
    '''The main entry point specified by pyproject.toml'''
    parser = args_parser(
        name=__name__,
        version=__version__,
        description=DESCRIPTION
    )
    args = parser.parse_args(sys.argv[1:])
    configure_log(args)
    try:
        base_url = decouple.config('IDA_URL')
        func = CMD_TABLE[args.command]
        func(base_url, args)
        log.info("done!")
    except KeyboardInterrupt:
        log.warn("Application quits by user request")


if __name__ == '__main__':
    main()
