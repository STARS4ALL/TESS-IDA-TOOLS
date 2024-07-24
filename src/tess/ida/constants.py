# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#------------------------
# Standard Python imports
# -----------------------

from enum import Enum

class BaseEnum(Enum):
    @classmethod
    def values(cls):
        return [member.name for _, member in cls.__members__.items()]

class TW(BaseEnum):
    TIME = 'UTC Date & Time'
    LOCAL_TIME = 'Local Date & Time'
    BOX_TEMP = 'Enclosure Temperature'
    SKY_TEMP = 'Sky Temperature'
    FREQ1 = 'Frequency'
    MAG1 = 'MSAS'
    ZP1 = 'ZP'
    SEQ = 'Sequence Number'


IDA_EXCLUDE =(TESSCol.LOCAL_TIME,)
