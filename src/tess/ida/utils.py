# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#------------------------
# Standard Python imports
# -----------------------

import os
import itertools

from datetime import datetime

# -------------------
# Third party imports
# -------------------

from dateutil.relativedelta import relativedelta

# -------------------
# Auxiliary functions
# -------------------

def cur_month() -> datetime:
    return datetime.now().replace(day=1,hour=0,minute=0,second=0,microsecond=0)

def prev_month() -> datetime:
    month = datetime.now().replace(day=1,hour=0,minute=0,second=0,microsecond=0)
    return month - relativedelta(months=1)

def group(n: int, iterable):
    iterable = iter(iterable)
    return iter(lambda: list(itertools.islice(iterable, n)), [])


def month_range(from_month: datetime, to_month: datetime) -> str:
    month = from_month
    while month <=  to_month:
        yield month.strftime('%Y-%m')
        month += relativedelta(months=1)

def name_month(ida_file_path: str) -> tuple:
    name = os.path.basename(os.path.dirname(ida_file_path))
    month = os.path.splitext(os.path.basename(ida_file_path))[0].split('_')[1]
    return name, month

def to_phot_dir(base_dir: str | None, name: str) -> str:
    cwd = os.getcwd() 
    base_dir = cwd if base_dir is None else base_dir
    base_dir = os.path.join(cwd, base_dir) if not os.path.isabs(base_dir) else base_dir
    full_dir_path = os.path.join(base_dir, name)
    return full_dir_path
   

def makedirs(base_dir: str | None, name: str) -> str:
    full_dir_path = to_phot_dir(base_dir, name)
    if not os.path.isdir(full_dir_path):
        os.makedirs(full_dir_path)
    return full_dir_path

def v_or_n(value: str) -> str | None:
    '''Value or None function'''
    value = value.strip()
    lvalue = value.lower()
    return None if lvalue == 'none' or lvalue == 'unknown' or lvalue == '' else value
