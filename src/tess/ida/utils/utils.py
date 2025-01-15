# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# ------------------------
# Standard Python imports
# -----------------------

import os
import hashlib

from datetime import datetime

# -------------------
# Third party imports
# -------------------

from dateutil.relativedelta import relativedelta
from lica.typing import OptStr

# -------------------
# Auxiliary functions
# -------------------


def month_range(from_month: datetime, to_month: datetime) -> str:
    month = from_month
    while month <= to_month:
        yield month.strftime("%Y-%m")
        month += relativedelta(months=1)


def name_month(ida_file_path: str) -> tuple:
    name = os.path.basename(os.path.dirname(ida_file_path))
    month = os.path.splitext(os.path.basename(ida_file_path))[0].split("_")[1]
    return name, month


def to_phot_dir(base_dir: OptStr, name: str) -> str:
    cwd = os.getcwd()
    base_dir = cwd if base_dir is None else base_dir
    base_dir = os.path.join(cwd, base_dir) if not os.path.isabs(base_dir) else base_dir
    full_dir_path = os.path.join(base_dir, name)
    return full_dir_path


def makedirs(base_dir: OptStr, name: str) -> str:
    full_dir_path = to_phot_dir(base_dir, name)
    os.makedirs(full_dir_path, exist_ok=True)
    return full_dir_path


def v_or_n(value: str) -> OptStr:
    """Value or None function"""
    value = value.strip()
    return None if value.lower() in ["none", "unknown", ""] else value


def hash_func(file_path: str) -> str:
    """Compute a hash from the image"""
    BLOCK_SIZE = 1048576  # 1MByte, the size of each read from the file
    # md5() was the fastest algorithm I've tried
    file_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        block = f.read(BLOCK_SIZE)
        while len(block) > 0:
            file_hash.update(block)
            block = f.read(BLOCK_SIZE)
    return file_hash.hexdigest()
