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
import logging
import datetime
import itertools

# -------------------
# Third party imports
# -------------------

from lica.cli import execute
from lica.validators import vdir
#--------------
# local imports
# -------------

from .. import __version__

# ----------------
# Module constants
# ----------------

DESCRIPTION = "Transform IDA files in ECSV files with added data/metadata"

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger(__name__.split('.')[-1])

# -------------------
# Auxiliary functions
# -------------------



# ===================================
# MAIN ENTRY POINT SPECIFIC ARGUMENTS
# ===================================


def add_args(parser):
     # Now parse the application specific parts
    subparser = parser.add_subparsers(dest='command')
    parser_month = subparser.add_parser('month', help='Download single monthly file')
    parser_month.add_argument('-n', '--name', type=str, required=True, help='Photometer name')
    parser_month.add_argument('-o', '--out-dir', type=str, default=None, help='Output base directory')
    return parser

# ================    
# MAIN ENTRY POINT
# ================

def to_ecsv(args):
    '''The main entry point specified by pyproject.toml'''
    log.info("done!")


def main():
    execute(main_func=to_ecsv, 
        add_args_func=add_args, 
        name=__name__, 
        version=__version__,
        description = DESCRIPTION
    )

if __name__ == '__main__':
    main()
