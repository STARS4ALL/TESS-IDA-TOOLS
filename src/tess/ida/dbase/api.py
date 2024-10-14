# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# -----------------------
# Standard Python imports
# ----------------------

import logging
import sqlite3

from typing import Union, Iterator
from collections.abc import Sequence


# -------------------
# Third party imports
# -------------------

import decouple


# --------------
# local imports
# -------------


# ----------------
# Module constants
# ----------------

DESCRIPTION = "Database utility to speed up pipeline processing"

OptRow = Union[tuple, None]

# -----------------------
# Module global variables
# -----------------------

# get the module logger
log = logging.getLogger(__name__.split(".")[-2])

try:
    theDatabaseFile = decouple.config("DATABASE_FILE")

    def aux_dbase_load() -> None:
        global theDatabaseFile
        log.info("Opening auxiliar database from %s", theDatabaseFile)
        _ = sqlite3.connect(theDatabaseFile)

    def aux_dbase_save() -> None:
        pass

    def aux_table_hashes_insert(data: Sequence[str, str]) -> None:
        global theDatabaseFile
        with sqlite3.connect(theDatabaseFile) as conn:
            conn.execute("INSERT INTO ecsv_t(filename, hash) VALUES(?,?)", data)
        conn.close()

    def aux_table_hashes_update(data: Sequence[str, str]) -> None:
        global theDatabaseFile
        with sqlite3.connect(theDatabaseFile) as conn:
            conn.execute(
                "UPDATE ecsv_t SET hash = ? WHERE filename = ?", (data[1], data[0])
            )
        conn.close()

    def aux_table_hashes_lookup(filename: str) -> Iterator[OptRow]:
        global theDatabaseFile
        with sqlite3.connect(theDatabaseFile) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT filename, hash FROM ecsv_t WHERE filename = ?", (filename,)
            )
        yield cursor.fetchone()
        conn.close()

    def aux_table_coords_lookup(name: str) -> Iterator[OptRow]:
        global theDatabaseFile
        with sqlite3.connect(theDatabaseFile) as conn:
            cursor = conn.cursor()
        cursor.execute(
            "SELECT phot_name, latitude, longitude, height FROM coords_t WHERE phot_name = ?",
            (name,),
        )
        yield cursor.fetchone()
        conn.close()

except decouple.UndefinedValueError:

    def aux_dbase_load() -> None:
        log.warning(
            "No Auxiliar database was configured. Check 'DATABASE_FILE' environment variable"
        )

    def aux_dbase_save() -> None:
        log.warning(
            "No Auxiliar database was configured. Check 'DATABASE_FILE' environment variable"
        )

    def aux_table_hashes_lookup(filename: str) -> Iterator[OptRow]:
        yield None

    def aux_table_hashes_insert(data: Sequence[str, str]) -> None:
        pass

    def aux_table_hashes_update(data: Sequence[str, str]) -> None:
        pass

    def aux_table_coords_lookup(name) -> Iterator[OptRow]:
        yield None
