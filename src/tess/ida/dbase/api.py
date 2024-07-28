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
import sqlite3

from typing import Any, Union
from argparse import Namespace, ArgumentParser
from collections.abc import Sequence


# -------------------
# Third party imports
# -------------------

import decouple

from lica.typing import OptStr


#--------------
# local imports
# -------------

from ... import __version__

# ----------------
# Module constants
# ----------------

DESCRIPTION = "Database utility to speed up pipeline processing"

OptRow = Union[tuple, None]

# -----------------------
# Module global variables
# -----------------------

# get the module logger
log = logging.getLogger(__name__.split('.')[-1])

try:
    theConnection = None
    theDatabaseFile = decouple.config('DATABASE_FILE')

    def adm_dbase_load() -> None:
        global theConnection, theDatabaseFile
        log.info("Opening administrative database from %s", theDatabaseFile)
        theConnection = sqlite3.connect(theDatabaseFile)
      
    def adm_dbase_save():
        global theConnection, theDatabaseFile
        log.info("Commiting changes to administrative database %s", theDatabaseFile)
        theConnection.commit()
        theConnection.close()

    def adm_table_hashes_insert(data: Sequence[str, str]) -> None:
        global theConnection
        theConnection.execute('INSERT INTO ecsv_t(filename, hash) VALUES(?,?)', data)

    def adm_table_hashes_update(data: Sequence[str, str]) -> None:
        global theConnection
        theConnection.execute('UPDATE ecsv_t SET hash = ? WHERE filename = ?', (data[1], data[0]))

    def adm_table_hashes_lookup(filename: str) -> OptRow:
        global theConnection
        cursor = theConnection.cursor()
        cursor.execute('SELECT filename, hash FROM ecsv_t WHERE filename = ?', (filename,))
        return cursor.fetchone()

    def adm_table_coords_lookup(name: str) -> OptRow:
        global theConnection
        cursor = theConnection.cursor()
        cursor.execute('SELECT phot_name, latitude, longitude, elevation FROM coords_t WHERE name = ?', (name,))
        return cursor.fetchone()

except decouple.UndefinedValueError:
    def adm_dbase_load() -> None:
        log.warning("No Adminsitrative database was configured")
    def adm_dbase_load() -> None:
        log.warning("No Adminsitrative database was configured")
    def adm_table_hashes_lookup(filename: str) -> OptRow:
        return None
    def adm_table_hashes_insert(data: Sequence[str, str]) -> None:
        pass
    def adm_table_hashes_update(data: Sequence[str, str]) -> None:
        pass
    def adm_table_coords_lookup(name) -> OptRow:
        return None


