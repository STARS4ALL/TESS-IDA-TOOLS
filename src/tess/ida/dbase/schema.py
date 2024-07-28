# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#-----------------------
# Standard Python imports
# ----------------------

import os
import logging
import sqlite

from typing import Any, Union
from argparse import Namespace, ArgumentParser
from collections.abc import Sequence

from importlib.resources import files

# -------------------
# Third party imports
# -------------------

import decouple

from lica.cli import execute
from lica.validators import vfile, vdir, vmonth
from lica.sqlite import open_database


#--------------
# local imports
# -------------

from ... import __version__

# ----------------
# Module constants
# ----------------

DESCRIPTION = "Database utility to speed up pipeline processing"

# get the module logger
log = logging.getLogger(__name__.split('.')[-1])


def execute_script(dbase_path, sql_path_obj):
    log.info("Applying updates to data model from {path}", path=sql_path_obj)
    try:
        connection = sqlite3.connect(dbase_path)
        connection.executescript(sql_path_obj.read_text())
    except sqlite3.OperationalError as e:
        connection.close()
        log.error("Error using the Python API. Trying with sqlite3 CLI")
        sqlite_cli = shutil.which("sqlite3");
        output = subprocess.check_call([sqlite_cli, dbase_path, "-init", sql_path_obj])
    else:
        connection.close()
      


def create_database_file() -> bool:
    '''Creates a Database file if not exists and returns a connection'''
    dbase_path = decouple.config('COORDS_TABLE')
    new_database = False
    output_dir = os.path.dirname(dbase_path)
    output_dir = os.getcwd() if not output_dir else output_dir
    os.makedirs(output_dir, exist_ok=True)
    if not os.path.exists(dbase_path):
        with open(dbase_path, 'w') as f:
            pass
        new_database = True
    sqlite3.connect(dbase_path).close()
    return new_database



def create_schema(dbase_path, schema_resource, initial_data_dir_path, updates_data_dir, query=VERSION_QUERY):
    f = files('tess.ida.dbase.sql').joinpath('schema.sql')
    with f.open('r') as sqlfile:
        lines = sqlfile.readlines()

    created = True
    connection = sqlite3.connect(dbase_path)
    cursor = connection.cursor()
    try:
        cursor.execute(query)
    except Exception:
        created = False
    if not created:
        connection.executescript(schema_resource.read_text())
        log.debug("Created data model from {url}", url=os.path.basename(schema_resource))
        # the filtering part is because Python 3.9 resource folders cannot exists without __init__.py
        file_list = [sql_file for sql_file in initial_data_dir_path.iterdir() if not sql_file.name.startswith('__') and not sql_file.is_dir()]
        for sql_file in file_list:
            log.debug("Populating data model from {path}", path=os.path.basename(sql_file))
            connection.executescript(sql_file.read_text())
    elif updates_data_dir is not None:
        filter_func = _filter_factory(connection)
        # the filtering part is beacuse Python 3.9 resource folders cannot exists without __init__.py
        file_list = sorted([sql_file for sql_file in updates_data_dir.iterdir() if not sql_file.name.startswith('__') and not sql_file.is_dir()])
        file_list = list(filter(filter_func, file_list))
        connection.close()
        for sql_file in file_list:
            _execute_script(dbase_path, sql_file)
    else:
        file_list = list()
    return not created, file_list

# ================================
# COMMAND LINE INTERFACE FUNCTIONS
# ================================





def cli_schema_create(args: Namespace) -> None:
    connection, path = open_database(env_var='DATABASE_FILE')



def cli_coords_add(args: Namespace) -> None:
    coords_file = decouple.config('COORDS_TABLE')
    log.info("Loading administrative Table from %s", coords_file)
    table = Table.read(coords_file, format='ascii.ecsv', delimiter=',')
    table.add_index('phot_name', unique=True)
    log.info("[%s] Adding coordinates entry: Lat = %s, Long = %s, Height = %s", 
        args.name, args.latitude, args.longitude, args.height)
    try:
        table.add_row((args.name, args.latitude,args.longitude,args.height))
    except ValueError:
        log.error("[%s] Coordinates entry already exists. Try subcommand 'update' instead", args.name)
    table.write(coords_file, format='ascii.ecsv', delimiter=',', fast_writer=True, overwrite=True)


def cli_coords_update(args: Namespace) -> None:
    coords_file = decouple.config('COORDS_TABLE')
    log.info("Loading administrative Table from %s", coords_file)
    table = Table.read(coords_file, format='ascii.ecsv', delimiter=',')
    table.add_index('phot_name', unique=True)
    try:
        res = table.loc[args.name]
        log.info("[%s] Found coordinates entry", args.name)
    except KeyError:
        log.warning("[%s] Coordnates entry not found", args.name)
    else:
        if args.latitude is not None:
            table['latitude'][res.index] = args.latitude
        if args.longitude is not None:
            table['longitude'][res.index] = args.longitude
        if args.height is not None:
            table['height'][res.index] = args.height
        log.info("[%s] Modified coordinates entry", args.name)
        log.warning("[%s] Sun/Moon data no longer valid. Delete your %s ECSV files and re-run the pipeline", args.name, args.name)
    table.write(coords_file, format='ascii.ecsv', delimiter=',', fast_writer=True, overwrite=True)


def cli_coords_delete(args: Namespace) -> None:
    coords_file = decouple.config('COORDS_TABLE')
    log.info("Loading administrative Table from %s", coords_file)
    table = Table.read(coords_file, format='ascii.ecsv', delimiter=',')
    table.add_index('phot_name', unique=True)
    try:
        res = table.loc[args.name]
        log.info("[%s] Found coordinates entry %s", args.name)
    except KeyError:
        log.warning("[%s] Coordinates entry not found", args.name)
    else:
        table.remove_rows(res.index)
        log.info("[%s] Deleted coordinates entry", args.name)
    table.write(coords_file, format='ascii.ecsv', delimiter=',', fast_writer=True, overwrite=True)


def add_args(parser: ArgumentParser) -> ArgumentParser:
    # Now parse the application specific parts
    subparser = parser.add_subparsers(dest='command')
    parser_schema = subparser.add_parser('schema', help='Administrative database schema')
    parser_coords = subparser.add_parser('coords', help='Coordinates Table management')

    subparser = parser_schema.add_subparsers(dest='subcommand')
    sch_cre = subparser.add_parser('create',  help="Create AstroPy tables and serialize to ECSV files")

    subparser = parser_coords.add_subparsers(dest='subcommand')
    loc_add = subparser.add_parser('add',  help="Add coordinates to a photometer")
    loc_add.add_argument('-n', '--name', type=str, required=True, help='Photometer name')
    loc_add.add_argument('-la', '--latitude', type=float, required=True, help='Latitude [degrees]')
    loc_add.add_argument('-lo', '--longitude', type=float, required=True, help='Longitude [degrees]')
    loc_add.add_argument('-he', '--height', type=float, default=0.0, help='Height above sea level [m] (default: %(default)s)')
    loc_del= subparser.add_parser('delete',  help="Remove coordinates from photometer")
    loc_del.add_argument('-n', '--name', type=str, required=True, help='Photometer name')
    loc_upd= subparser.add_parser('update',  help="Update coordinates to photometer")
    loc_upd.add_argument('-n', '--name', type=str, required=True, help='Photometer name')
    loc_upd.add_argument('-la', '--latitude', type=float, default=None, help='Latitude [degrees]')
    loc_upd.add_argument('-lo', '--longitude', type=float, default=None, help='Longitude [degrees]')
    loc_upd.add_argument('-he', '--height', type=float, default=None, help='Height above sea level [m] (default: %(default)s)')
    return parser


CMD_TABLE = {
    'schema_create': cli_schema_create,
    'coords_add': cli_coords_add,
    'coords_delete': cli_coords_delete,
    'coords_update': cli_coords_update,
}

def cli_schema(args: Namespace) -> None:
    '''Create an empty able serializable to ECSV file'''
    try:
        args.subcommand
    except AttributeError:
        log.error("Missing subcommand fro command (%s)", args.command)
    else:
        func = CMD_TABLE[f'{args.command}_{args.subcommand}']
        func(args)


def main() -> None:
    execute(main_func=cli_schema, 
        add_args_func=add_args, 
        name=__name__, 
        version=__version__,
        description = DESCRIPTION
    )

if __name__ == '__main__':
    main()
