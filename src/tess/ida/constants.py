# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# ------------------------
# Standard Python imports
# -----------------------

from lica import StrEnum

# -------------------------
# Constant and Enumerations
# -------------------------

IDA_HEADER_LEN = 35


class StringEnum(StrEnum):
    @classmethod
    def names(cls):
        """Get the values in the order defined"""
        return [member.name for _, member in cls.__members__.items()]

    @classmethod
    def values(cls):
        """Get the values in the order defined"""
        return [member.value for _, member in cls.__members__.items()]


# IDA keywords in the comments section of the IDA file
class IDA_KEYWORDS(StringEnum):
    LICENSE = "License"
    NUM_HEADERS = "Number of header lines"
    NUM_CHANNELS = "Number of channels"
    OBSERVER = "Data supplier"
    LOCATION = "Location name"
    TIMEZONE = "Local timezone"
    POSITION = "Position"
    FOV = "Field of view"
    COVER_OFFSET = "TESS cover offset value"
    NUM_COLS = "Number of fields per line"
    ZP = "TESS zero point"
    AIM = "Measurement direction per channel"
    FILTERS = "Filters per channel"
    PHOT_NAME = "Instrument ID"


# TESS-W Data column names
# order is imporant: it is the oroder in the IDA file


class TESSW_COLS(StringEnum):
    UTC_TIME = "time"  # always 'time' for TimeSeries Astropy Class
    LOCAL_TIME = "Local Date & Time"
    BOX_TEMP = "Enclosure Temperature"
    SKY_TEMP = "Sky Temperature"
    FREQ = "Frequency"
    MAG = "MSAS"
    ZP = "ZP"
    SEQ_NUM = "Sequence Number"


# TESS-4C data column names
# order is imporant: it is the order in the IDA file


class TESS4C_COLS(StringEnum):
    UTC_TIME = "time"  # always 'time' for TimeSeries Astropy Class
    LOCAL_TIME = "Local Date & Time"
    BOX_TEMP = "Enclosure Temperature"
    SKY_TEMP = "Sky Temperature"
    FREQ1 = "Freq1"
    MAG1 = "MSAS1"
    ZP1 = "ZP1"
    FREQ2 = "Freq2"
    MAG2 = "MSAS2"
    ZP2 = "ZP2"
    FREQ3 = "Freq3"
    MAG3 = "MSAS3"
    ZP3 = "ZP3"
    FREQ4 = "Freq4"
    MAG4 = "MSAS4"
    ZP4 = "ZP4"
    SEQ_NUM = "Sequence Number"


# Additional data column names  that can appear in the Time Series


class TIMESERIES_COLS(StringEnum):
    SUN_ALT = "Sun Alt"
    SUN_AZ = "Sun Az"
    MOON_AZ = "Moon Az"
    MOON_ALT = "Moon Alt"
    MOON_ILLUM = "Moon Illumination"
