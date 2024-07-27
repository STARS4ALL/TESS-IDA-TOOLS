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

from argparse import Namespace, ArgumentParser


# -------------------
# Third party imports
# -------------------

import decouple

from pubsub import pub

from astropy.table import Table, QTable
import astropy.units as u

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

# -----------------------
# Module global variables
# -----------------------

# get the module logger
log = logging.getLogger(__name__.split('.')[-1])

try:
    theHashesTable = None
    theHashesFile = decouple.config('ADM_HASHES_TABLE')
    theLocationsTable = None
    theLocationsFile = decouple.config('ADM_LOCATIONS_TABLE')

    from astropy.table import SortedArray, SCEngine

    # =============
    # Work Routines
    # =============

    def adm_table_hashes_load():
        global theHashesTable, theHashesFile
        log.info("Loading administrative Table from %s", theHashesFile)
        theHashesTable = Table.read(theHashesFile, format='ascii.ecsv', delimiter=',')
        theHashesTable.add_index('filename',  unique=True, engine=SCEngine)

    def adm_table_locations_load():
        global theLocationsTable, theLocationsFile
        log.info("Loading administrative Table from %s", theLocationsFile)
        theLocationsTable = QTable.read(theLocationsFile, format='ascii.ecsv', delimiter=',')

    def adm_table_load():
        adm_table_hashes_load()
        adm_table_locations_load()
        
    def adm_table_hashes_save():
        global theHashesTable, theHashesFile
        log.info("Saving administrative Table to %s", theHashesFile)
        theHashesTable.write(theHashesFile, format='ascii.ecsv', delimiter=',', fast_writer=True, overwrite=True)

    def adm_table_locations_save():
        global theLocationsTable, theLocationsFile
        log.info("Saving administrative Table to %s", theLocationsFile)
        theLocationsTable.write(theLocationsFile, format='ascii.ecsv', delimiter=',', fast_writer=True, overwrite=True)

    def adm_table_save():
         adm_table_hashes_save()
         adm_table_locations_save()

    def adm_table_hashes_insert(data):
        global theHashesTable
        theHashesTable.add_row(data)

    def adm_table_hashes_update(data):
        global theHashesTable
        theHashesTable.loc[data[0]] = data

    def adm_table_hashes_lookup(filename):
        global theHashesTable
        try:
            result = theHashesTable.loc[filename]
        except KeyError:
            result = None
        return result

    def adm_table_location_lookup(phot_name):
        global theLocationsTable
        try:
            result = theLocationsTable.loc[phot_name]
        except KeyError:
            result = None
        return result

    pub.subscribe(adm_table_load,'admdb_load')
    pub.subscribe(adm_table_save,'admdb_save')
    pub.subscribe(adm_table_update,'admdb_update_hashes')
    pub.subscribe(adm_table_hashes_insert,'admdb_insert_hashes')

except:

    def adm_table_hashes_lookup(filename):
        return None

    def adm_table_location_lookup(name):
        return None
    


# ================================
# COMMAND LINE INTERFACE FUNCTIONS
# ================================

def cli_schema_create(args: Namespace) -> None:
    error = False
    for env_var in ('ADM_HASHES_TABLE', 'ADM_LOCATIONS_TABLE'):
        try:
            table_file = decouple.config(env_var)
            if os.path.isfile(table_file):
                log.info("Deleting administrative Table: %s", table_file)
                os.remove(table_file)
            dirname = os.path.dirname(table_file)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
        except decouple.UndefinedValueError as e:
            log.error("environment variable %s not found in .env file", env_var)
            error = error or True
            continue
    if error:
        return
    hashes_file = decouple.config('ADM_HASHES_TABLE')
    log.info("Creating an empty administrative Table file: %s", hashes_file)
    table = Table([tuple(), tuple()], 
        names=('filename', 'hash'), 
        dtype=['str', 'str']
    )
    table.write(hashes_file, format='ascii.ecsv', delimiter=',', fast_writer=True, overwrite=True)
    locations_file = decouple.config('ADM_LOCATIONS_TABLE')
    log.info("Creating an empty administrative Table file: %s", locations_file)
    table = QTable([tuple(), tuple(), tuple(), tuple()], 
        names=('phot_name', 'latitude', 'longitude', 'height'), 
        dtype=('str', 'float','float','float'),
        units=(None, u.deg, u.deg, u.m)
    )
    table.write(locations_file, format='ascii.ecsv', delimiter=',', fast_writer=True, overwrite=True)

def cli_location(args: Namespace) -> None:
    locations_file = decouple.config('ADM_LOCATIONS_TABLE')
    log.info("Loading administrative Table from %s", locations_file)
    table = QTable.read(locations_file, format='ascii.ecsv', delimiter=',')
    table.add_index('phot_name', unique=True)
    if args.subcommand == 'add':
        name = args.name
        lati = args.latitude*u.deg
        longi = args.longitude*u.deg
        h =  args.height*u.m
        log.info("[%s] Adding location entry: Lat = %s, Long = %s, Height = %s", args.name, lati, longi, h)
        try:
            table.add_row((name, lati,longi,h))
        except ValueError:
            log.error("[%s] location entry already exists. Try update", name)
    elif args.subcommand == 'delete':
        try:
            r = table.loc[args.name]
            log.info("[%s] Found location entry %s", args.name)
        except KeyError:
            log.warning("[%s] Location entry not found", args.name)
        else:
            table.remove_rows(r.index)
            log.info("[%s] Deleted location entry", args.name)
    else:
        name = args.name
        lati = args.latitude
        longi = args.longitude
        h =  args.height
        try:
            r = table.loc[args.name]
            log.info("[%s] Found location entry", args.name)
        except KeyError:
            log.warning("[%s] Location entry not found deleted", args.name)
        else:
            if lati is not None:
                table['latitude'][r.index] = lati * u.deg
            if longi is not None:
                table['longitude'][r.index] = longi * u.deg
            if h is not None:
                table['height'][r.index] = h *u.m
            log.info("[%s] Modified location entry", args.name)
            log.warning("[%s] Sun/Moon data no longer valid. Delete your %s ECSV files and re-run the pipeline", name, name)
    table.write(locations_file, format='ascii.ecsv', delimiter=',', fast_writer=True, overwrite=True)

def add_args(parser: ArgumentParser) -> ArgumentParser:
    # Now parse the application specific parts
    subparser = parser.add_subparsers(dest='command')
    parser_create = subparser.add_parser('create', help='Create administrative AstroPy Tables')
    parser_location = subparser.add_parser('location', help='Location Table management')
    
    subparser = parser_location.add_subparsers(dest='subcommand')
    loc_add = subparser.add_parser('add',  help="Add a location for photometer")
    loc_add.add_argument('-n', '--name', type=str, required=True, help='Photometer name')
    loc_add.add_argument('-la', '--latitude', type=float, required=True, help='Latitude [degrees]')
    loc_add.add_argument('-lo', '--longitude', type=float, required=True, help='Longitude [degrees]')
    loc_add.add_argument('-he', '--height', type=float, default=0.0, help='Height above sea level [m] (default: %(default)s)')

    loc_del= subparser.add_parser('delete',  help="Remove location for photometer")
    loc_del.add_argument('-n', '--name', type=str, required=True, help='Photometer name')
    
    loc_upd= subparser.add_parser('update',  help="Update location for photometer")
    loc_upd.add_argument('-n', '--name', type=str, required=True, help='Photometer name')
    loc_upd.add_argument('-la', '--latitude', type=float, default=None, help='Latitude [degrees]')
    loc_upd.add_argument('-lo', '--longitude', type=float, default=None, help='Longitude [degrees]')
    loc_upd.add_argument('-he', '--height', type=float, default=None, help='Height above sea level [m] (default: %(default)s)')

    return parser


CMD_TABLE = {
    'create': cli_schema_create,
    'location': cli_location,
}

def cli_schema(args: Namespace) -> None:
    '''Create an empty able serializable to ECSV file'''
    func = CMD_TABLE[args.command]
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
