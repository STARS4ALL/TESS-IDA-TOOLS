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

from astropy.table import Table

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

DESCRIPTION = "Database utility to speed up pipleline processinf"
MARKER = None

# -----------------------
# Module global variables
# -----------------------

# get the module logger
log = logging.getLogger(__name__.split('.')[-1])

try:
    theTable = None
    theFile = decouple.config('DATABASE_FILE')
    from astropy.table import SortedArray, SCEngine

    # =============
    # Work Routines
    # =============

    def adm_table_load():
        global theTable, theFile
        log.info("Loading administrative Table from %s", theFile)
        theTable = Table.read(theFile, format='ascii.ecsv', delimiter=',')
        theTable.add_index('filename', engine=SCEngine)
      
    def adm_table_save():
        global theTable, theFile
        log.info("Saving administrative Table to %s", theFile)
        theTable.write(theFile, format='ascii.ecsv', delimiter=',', fast_writer=True, overwrite=True)

    def adm_table_insert(data):
        theTable.add_row(data)

    def adm_table_update(data):
        theTable.loc[data[0]] = data

    def adm_table_lookup(filename):
        try:
            result = theTable.loc[filename]
        except KeyError:
            result = None
        return result

    pub.subscribe(adm_table_load,'load_database')
    pub.subscribe(adm_table_save,'save_database')
    pub.subscribe(adm_table_update,'update_database')
    pub.subscribe(adm_table_insert,'insert_database')

except:

    def adm_table_lookup(filename):
        return None
    


# ================================
# COMMAND LINE INTERFACE FUNCTIONS
# ================================

def cli_schema_create(dbase_path: str, args: Namespace):
    log.info("Deleting administrative Table file: %s", dbase_path)
    os.remove(dbase_path)
    log.info("Creating an empty administrative Table: %s", dbase_path)
    table = Table([tuple(), tuple()], names=('filename', 'hash'), dtype=['str', 'str'])
  
    table.write(dbase_path, format='ascii.ecsv', delimiter=',', fast_writer=True, overwrite=True)


def add_args(parser: ArgumentParser) -> ArgumentParser:
    # Now parse the application specific parts
    subparser = parser.add_subparsers(dest='command')
    parser_single = subparser.add_parser('create', help='Create an AstroPy Table seving as administrative database')
    return parser


CMD_TABLE = {
    'create': cli_schema_create,
}

def cli_schema(args: Namespace) -> None:
    '''Create an empty able serializable to ECSV file'''
    dbase_path = decouple.config('DATABASE_FILE')
    func = CMD_TABLE[args.command]
    func(dbase_path, args)
    log.info("done!")


def main() -> None:
    execute(main_func=cli_schema, 
        add_args_func=add_args, 
        name=__name__, 
        version=__version__,
        description = DESCRIPTION
    )

if __name__ == '__main__':
    main()
