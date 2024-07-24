# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#------------------------
# Standard Python imports
# -----------------------

from strenum import StrEnum

IDA_HEADER_LEN = 35

class BaseEnum(StrEnum):
    @classmethod
    def values(cls):
        return [member.value for _, member in cls.__members__.items()]

class TW(BaseEnum):
    UTC_TIME   = 'time'
    LOCAL_TIME = 'Local Date & Time'
    BOX_TEMP   = 'Enclosure Temperature'
    SKY_TEMP   = 'Sky Temperature'
    FREQ1      = 'Frequency'
    MAG1       = 'MSAS'
    ZP1        = 'ZP'
    SEQ        = 'Sequence Number'

class T4C(BaseEnum):
    UTC_TIME   = 'time'
    LOCAL_TIME = 'Local Date & Time'
    BOX_TEMP   = 'Enclosure Temperature'
    SKY_TEMP   = 'Sky Temperature'
    FREQ1      = 'Freq2'
    MAG1       = 'MSAS1'
    ZP1        = 'ZP1'
    FREQ2      = 'Freq2'
    MAG2       = 'MSAS2'
    ZP2        = 'ZP2'
    FREQ3      = 'Freq3'
    MAG3       = 'MSAS3'
    ZP3        = 'ZP3'
    FREQ4      = 'Freq4'
    MAG4       = 'MSAS4'
    ZP4        = 'ZP4'
    SEQ        = 'Sequence Number'

