# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Copyright (c) 2021
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

from datetime import datetime
from argparse import ArgumentParser

# ---------------------
# Thrid-party libraries
# ---------------------

from dateutil.relativedelta import relativedelta
from lica.validators import vmonth, vdir, vfloat


# ------------------------
# Own modules and packages
# ------------------------


def cur_month() -> datetime:
    return datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def prev_month() -> datetime:
    month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return month - relativedelta(months=1)


# -----------------
# Auxiliary parsers
# -----------------


def name() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument("-n", "--name", type=str, required=True, help="Photometer name")
    return parser


def fix() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument("-f", "--fix", action="store_true", help="Fix unknown location")
    return parser


def skip() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-sd", "--skip-download", action="store_true", help="Skip download step"
    )
    return parser


def timeout() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="HTTP timeout in seconds (defaults to %(default)s) sec.",
    )
    return parser


def inout_dirs(
    tag_in: str = "", tag_out: str = "", in_dir_exists: bool = True
) -> ArgumentParser:
    validator = vdir if in_dir_exists else str
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-i",
        "--in-dir",
        type=validator,
        default=None,
        help=f"Input {tag_in} base directory",
    )
    parser.add_argument(
        "-o",
        "--out-dir",
        type=str,
        default=None,
        help=f"Output {tag_out} base directory",
    )
    return parser


def out_dir(tag: str = "") -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-o", "--out-dir", type=str, default=None, help=f"Output {tag} base directory"
    )
    return parser


def inout_file(
    tag_in: str = "", tag_out: str = "", in_dir_exists: bool = True
) -> ArgumentParser:
    validator = vdir if in_dir_exists else str
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-i",
        "--in-dir",
        type=validator,
        default=None,
        help=f"Input {tag_in} base directory",
    )
    parser.add_argument(
        "-on",
        "--out-filename",
        type=str,
        default=None,
        help=f"Optional output {tag_out} file name",
    )
    return parser


def concurrent() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-c",
        "--concurrent",
        type=int,
        metavar="<N>",
        choices=[1, 2, 4, 6, 8],
        default=4,
        help="Number of concurrent downloads (defaults to %(default)s)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="HTTP timeout in seconds (defaults to %(default)s sec.)",
    )
    return parser


def mon_single() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-e", "--exact", type=str, default=None, help="Specific monthly file name"
    )
    group.add_argument(
        "-m",
        "--month",
        type=vmonth,
        default=None,
        metavar="<YYYY-MM>",
        help="Year and Month",
    )
    return parser


def mon_range() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-s",
        "--since",
        type=vmonth,
        default=prev_month(),
        metavar="<YYYY-MM>",
        help="Year and Month (defaults to %(default)s)",
    )
    parser.add_argument(
        "-u",
        "--until",
        type=vmonth,
        default=cur_month(),
        metavar="<YYYY-MM>",
        help="Year and Month (defaults to %(default)s)",
    )
    return parser


def phot_range() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-l",
        "--list",
        type=int,
        default=None,
        nargs="+",
        metavar="<N>",
        help="Photometer number list",
    )
    group.add_argument(
        "-r",
        "--range",
        type=int,
        default=None,
        metavar="<N>",
        nargs=2,
        help="Photometer number range",
    )
    return parser


def location() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-lo",
        "--longitude",
        type=vfloat,
        required=True,
        metavar="<LON>",
        help="Longitude (decimal degrees)",
    )
    parser.add_argument(
        "-la",
        "--latitude",
        type=vfloat,
        required=True,
        metavar="<LAT>",
        help="Latitude (decimal degrees)",
    )
    parser.add_argument(
        "-ra",
        "--radius",
        type=vfloat,
        default=10,
        metavar="<R>",
        help="Search radius (Km) (defaults to %(default)s Km)",
    )
    return parser
