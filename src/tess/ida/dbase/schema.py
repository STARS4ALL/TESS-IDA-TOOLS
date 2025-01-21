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
import sqlite3

from importlib.resources import files
from argparse import Namespace, ArgumentParser

# -------------------
# Third party imports
# -------------------

import decouple

from lica.cli import execute
from lica.tabulate import paging


# --------------
# local imports
# -------------

from .. import __version__

# ----------------
# Module constants
# ----------------

DESCRIPTION = "Database utility to speed up pipeline processing"

_SQL_PKG = "tess.ida.dbase.sql"
_SQL_RES = "schema.sql"
SCHEMA_SQL_TEXT = files(_SQL_PKG).joinpath(_SQL_RES).read_text()

# get the module logger
log = logging.getLogger(__name__.split(".")[-1])


# ================================
# COMMAND LINE INTERFACE FUNCTIONS
# ================================


def cli_schema_create(args: Namespace) -> None:
    dbase_path = decouple.config("DATABASE_FILE")
    if os.path.isfile(dbase_path):
        log.info("Deleting auxiliar database: %s", dbase_path)
        os.remove(dbase_path)
    output_dir = os.path.dirname(dbase_path)
    output_dir = os.getcwd() if not output_dir else output_dir
    os.makedirs(output_dir, exist_ok=True)
    log.info("Creating SQLite Schema on %s", dbase_path)
    try:
        with sqlite3.connect(dbase_path) as connection:
            connection.executescript(SCHEMA_SQL_TEXT)
    except sqlite3.OperationalError as e:
        log.error("Error creating the database: %s", e)
    finally:
        connection.close()


def cli_coords_add(args: Namespace) -> None:
    data = (args.name, args.latitude, args.longitude, args.height)
    dbase_path = decouple.config("DATABASE_FILE")
    try:
        with sqlite3.connect(dbase_path) as connection:
            connection.execute(
                "INSERT OR IGNORE INTO coords_t(phot_name, latitude, longitude, height) VALUES(?,?,?,?)",
                data,
            )
    except Exception as e:
        log.error(e)
    connection.close()
    log.info(
        "[%s] Added coordinates entry: Lat = %s, Long = %s, Height = %s",
        args.name,
        args.latitude,
        args.longitude,
        args.height,
    )


def cli_coords_update(args: Namespace) -> None:
    dbase_path = decouple.config("DATABASE_FILE")
    setters = list()
    data = {"name": args.name}
    if args.latitude is not None:
        setters.append("latitude = :latitude")
        data["latitude"] = args.latitude
    if args.longitude is not None:
        setters.append("longitude = :longitude")
        data["longitude"] = args.longitude
    if args.height is not None:
        setters.append("height = :height")
        data["height"] = args.height
    if not setters:
        log.error("at least one argument must be given")
        return
    sql = "UPDATE coords_t SET " + ", ".join(setters) + " WHERE phot_name = :name"
    try:
        with sqlite3.connect(dbase_path) as connection:
            connection.execute(sql, data)
    except Exception as e:
        log.error(e)
    connection.close()
    log.info("[%s] Modified coordinates entry", args.name)
    log.warning(
        "[%s] Sun/Moon data no longer valid. Delete your %s ECSV files and re-run the pipeline",
        args.name,
        args.name,
    )


def cli_coords_delete(args: Namespace) -> None:
    dbase_path = decouple.config("DATABASE_FILE")
    data = (args.name,)
    try:
        with sqlite3.connect(dbase_path) as connection:
            connection.execute("DELETE FROM coords_t WHERE phot_name = ?", data)
    except Exception as e:
        log.error(e)
    connection.close()
    log.info("[%s] Deleted coordinates entry", args.name)


def cli_coords_list(args: Namespace) -> None:
    dbase_path = decouple.config("DATABASE_FILE")
    data = (args.name,)
    try:
        with sqlite3.connect(dbase_path) as connection:
            cursor = connection.cursor()
            if args.name:
                sql = "SELECT phot_name, latitude, longitude, height FROM coords_t WHERE phot_name = ?"
                cursor.execute(sql, data)
            else:
                sql = "SELECT phot_name, latitude, longitude, height FROM coords_t ORDER BY phot_name"
                cursor.execute(sql)
            print("\n")
            paging(cursor, ("NAME", "LATITUDE", "LONGITUDE",  "HEIGHT"))
    except Exception as e:
        log.error(e)
    connection.close()


def add_args(parser: ArgumentParser) -> ArgumentParser:
    # Now parse the application specific parts
    subparser = parser.add_subparsers(dest="command")
    parser_schema = subparser.add_parser(
        "schema", help="Administrative database schema"
    )
    parser_coords = subparser.add_parser("coords", help="Coordinates Table management")

    subparser = parser_schema.add_subparsers(dest="subcommand")
    sch_cre = subparser.add_parser(  # noqa: F841
        "create", help="Create AstroPy tables and serialize to ECSV files"
    )

    subparser = parser_coords.add_subparsers(dest="subcommand")
    loc_add = subparser.add_parser("add", help="Add coordinates to a photometer")
    loc_add.add_argument(
        "-n", "--name", type=str, required=True, help="Photometer name"
    )
    loc_add.add_argument(
        "-la", "--latitude", type=float, required=True, help="Latitude [degrees]"
    )
    loc_add.add_argument(
        "-lo", "--longitude", type=float, required=True, help="Longitude [degrees]"
    )
    loc_add.add_argument(
        "-he",
        "--height",
        type=float,
        default=0.0,
        help="Height above sea level [m] (default: %(default)s)",
    )
    loc_del = subparser.add_parser("delete", help="Remove coordinates from photometer")
    loc_del.add_argument(
        "-n", "--name", type=str, required=True, help="Photometer name"
    )
    loc_del = subparser.add_parser("list", help="List photometer coordinates")
    loc_del.add_argument(
        "-n", "--name", type=str, default=None, help="Optional photometer name"
    )
    loc_upd = subparser.add_parser("update", help="Update coordinates to photometer")
    loc_upd.add_argument(
        "-n", "--name", type=str, required=True, help="Photometer name"
    )
    loc_upd.add_argument(
        "-la", "--latitude", type=float, default=None, help="Latitude [degrees]"
    )
    loc_upd.add_argument(
        "-lo", "--longitude", type=float, default=None, help="Longitude [degrees]"
    )
    loc_upd.add_argument(
        "-he",
        "--height",
        type=float,
        default=None,
        help="Height above sea level [m] (default: %(default)s)",
    )
    return parser


CMD_TABLE = {
    "schema_create": cli_schema_create,
    "coords_add": cli_coords_add,
    "coords_delete": cli_coords_delete,
    "coords_update": cli_coords_update,
    "coords_list": cli_coords_list,
}


def cli_schema(args: Namespace) -> None:
    """Create an empty able serializable to ECSV file"""
    try:
        args.subcommand
    except AttributeError:
        log.error("Missing subcommand fro command (%s)", args.command)
    else:
        func = CMD_TABLE[f"{args.command}_{args.subcommand}"]
        func(args)


def main() -> None:
    execute(
        main_func=cli_schema,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description=DESCRIPTION,
    )


if __name__ == "__main__":
    main()
