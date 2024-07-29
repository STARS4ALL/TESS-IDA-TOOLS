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
from typing import Any, Union
from argparse import Namespace, ArgumentParser
from collections.abc import Sequence


# -------------------
# Third party imports
# -------------------

import decouple

from astropy.table import Table, Row

from lica.cli import execute
from lica.validators import vfile, vdir, vmonth
from lica.typing import OptStr


#--------------
# local imports
# -------------

from .. import __version__

# ----------------
# Module constants
# ----------------

DESCRIPTION = "Database utility to speed up pipeline processing"
MARKER = None

OptRow = Union[Row, None]

# -----------------------
# Module global variables
# -----------------------

# get the module logger
log = logging.getLogger(__name__.split('.')[-1])

try:
    theHashesTable = None
    theHashesFile = decouple.config('HASHES_TABLE')
    from astropy.table import SCEngine

    def adm_table_hashes_load() -> None:
        global theHashesTable, theHashesFile
        log.info("Loading auxiliar Table from %s", theHashesFile)
        theHashesTable = Table.read(theHashesFile, format='ascii.ecsv', delimiter=',')
        theHashesTable.add_index('filename',  unique=True, engine=SCEngine)
        
    def adm_table_hashes_save():
        global theHashesTable, theHashesFile
        log.info("Saving auxiliar Table to %s", theHashesFile)
        theHashesTable.write(theHashesFile, format='ascii.ecsv', delimiter=',', fast_writer=True, overwrite=True)

    def adm_table_hashes_insert(data: Sequence[str, str]) -> None:
        global theHashesTable
        theHashesTable.add_row(data)

    def adm_table_hashes_update(data: Sequence[str, str]) -> None:
        global theHashesTable
        theHashesTable.loc[data[0]] = data

    def adm_table_hashes_lookup(filename: str) -> OptRow:
        global theHashesTable
        try:
            result = theHashesTable.loc[filename]
        except KeyError:
            result = None
        return result

except decouple.UndefinedValueError:
    def adm_table_hashes_load() -> None:
        log.warning("No Auxiliar table for IDA files' hashes")
    def adm_table_hashes_save() -> None:
        log.warning("No Auxiliar table for IDA files' hashes")
    def adm_table_hashes_lookup(filename: str) -> OptRow:
        return None
    def adm_table_hashes_insert(data: Sequence[str, str]) -> None:
        pass
    def adm_table_hashes_update(data: Sequence[str, str]) -> None:
        pass

  
try:
    theLocationsTable = None
    theLocationsFile = decouple.config('COORDS_TABLE')
    from astropy.table import SCEngine

    def adm_table_coords_load() -> None:
        global theLocationsTable, theLocationsFile
        log.info("Loading auxiliar Table from %s", theLocationsFile)
        theLocationsTable = Table.read(theLocationsFile, format='ascii.ecsv', delimiter=',')
        theLocationsTable.add_index('phot_name', unique=True, engine=SCEngine)

    def adm_table_coords_save() -> None:
        global theLocationsTable, theLocationsFile
        log.info("Saving auxiliar Table to %s", theLocationsFile)
        theLocationsTable.write(theLocationsFile, format='ascii.ecsv', delimiter=',', fast_writer=True, overwrite=True)

    def adm_table_coords_lookup(phot_name: str) -> OptRow:
        global theLocationsTable
        try:
            result = theLocationsTable.loc[phot_name]
        except KeyError:
            result = None
        return result

except decouple.UndefinedValueError:
    def adm_table_coords_load() -> None:
        log.warning("No Auxiliar table for photometers' coordinates")
    def adm_table_coords_save() -> None:
        log.warning("No Auxiliar table for photometers' coordinates")
    def adm_table_coords_lookup(name) -> OptRow:
        return None

def adm_dbase_load():
    adm_table_hashes_load()
    adm_table_coords_load()

def adm_dbase_save():
    adm_table_hashes_save()
    adm_table_coords_save()

# ================================
# COMMAND LINE INTERFACE FUNCTIONS
# ================================

def cli_schema_create(args: Namespace) -> None:
    table_files = list()
    for env_var in ('HASHES_TABLE', 'COORDS_TABLE'):
        try:
            table_file = decouple.config(env_var)
            table_files.append(table_file)
            if os.path.isfile(table_file):
                log.info("Deleting auxiliar Table: %s", table_file)
                os.remove(table_file)
            dirname = os.path.dirname(table_file)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
        except decouple.UndefinedValueError as e:
            table_files.append(None)
            log.warning("environment variable %s not found in .env file", env_var)
    if table_files[0]:
        log.info("Creating an empty auxiliar Table file: %s", table_files[0])
        table = Table([tuple(), tuple()], 
            names=('filename', 'hash'), 
            dtype=('str', 'str')
        )
        table.write(table_files[0], format='ascii.ecsv', delimiter=',', fast_writer=True, overwrite=True)
    if table_files[1]:
        log.info("Creating an empty auxiliar Table file: %s", table_files[1])
        table = Table([tuple(), tuple(), tuple(), tuple()], 
            names=('phot_name', 'latitude', 'longitude', 'height'), 
            dtype=('str', 'float','float','float')
        )
        table.write(table_files[1], format='ascii.ecsv', delimiter=',', fast_writer=True, overwrite=True)


def cli_coords_add(args: Namespace) -> None:
    coords_file = decouple.config('COORDS_TABLE')
    log.info("Loading auxiliar Table from %s", coords_file)
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
    log.info("Loading auxiliar Table from %s", coords_file)
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
    log.info("Loading auxiliar Table from %s", coords_file)
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
    parser_schema = subparser.add_parser('schema', help='Administrative AstroPy Tables schema')
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
