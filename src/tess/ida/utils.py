# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#------------------------
# Standard Python imports
# -----------------------

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

def grouper(n: int, iterable):
    iterable = iter(iterable)
    return iter(lambda: list(itertools.islice(iterable, n)), [])


def daterange(from_month: datetime, to_month: datetime) -> str:
    month = from_month
    while month <=  to_month:
        yield month.strftime('%Y-%m')
        month += relativedelta(months=1)