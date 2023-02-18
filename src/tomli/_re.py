# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# Licensed to PSF under a Contributor Agreement.

from datetime import date, datetime, time, timedelta, timezone, tzinfo
from functools import lru_cache
import re

RE_NUMBER = re.compile(
    r"""0(x[0-9A-Fa-f](_?[0-9A-Fa-f])*|b[01](_?[01])*|o[0-7](_?[0-7])*)|[+-]?(0|[1-9](_?[0-9])*)((\.[0-9](_?[0-9])*)?([eE][+-]?[0-9](_?[0-9])*)?)"""

)
RE_LOCALTIME = re.compile(r"([01][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])(?:\.([0-9]{1,6})[0-9]*)?")

RE_DATETIME_YMD = re.compile(r"""([\d][\d][\d][\d])-(0[1-9]|1[0-2])-(0[1-9]|[12][\d]|3[01])""")
RE_DATETIME_TIME = re.compile(
    r"""([Tt ]([01][\d]|2[0-3]):([0-5][\d]):([0-5][\d])(\.([\d][\d]?[\d]?[\d]?[\d]?[\d]?)[\d]*)?)?"""
)
RE_DATETIME_ZONE = re.compile(r"(([Zz])|([+-])([01][\d]|2[0-3]):([0-5][\d]))?")


def match_to_datetime(ymd_match, time_match, zone_match):
    """Convert a `RE_DATETIME` match to `datetime.datetime` or `datetime.date`.

    Raises ValueError if the match does not correspond to a valid date
    or datetime.
    """
    (
        year_str,
        month_str,
        day_str,
    ) = ymd_match.groups()

    if time_match:
        (
            _,
            hour_str,
            minute_str,
            sec_str,
            _,
            micros_str,
        ) = time_match.groups()
    else:
        hour_str = None
        minute_str = None
        sec_str = None
        micros_str = None

    if zone_match:
        (
            _,
            zulu_time,
            offset_sign_str,
            offset_hour_str,
            offset_minute_str,
        ) = zone_match.groups()
    else:
        zulu_time = None
        offset_sign_str = None
        offset_hour_str = None
        offset_minute_str = None

    year, month, day = int(year_str), int(month_str), int(day_str)
    if hour_str is None:
        return date(year, month, day)
    hour, minute, sec = int(hour_str), int(minute_str), int(sec_str)
    micros = int(micros_str.ljust(6, "0")) if micros_str else 0
    if offset_sign_str:
        tz: tzinfo | None = cached_tz(
            offset_hour_str, offset_minute_str, offset_sign_str
        )
    elif zulu_time:
        tz = timezone.utc
    else:  # local date-time
        tz = None
    return datetime(year, month, day, hour, minute, sec, micros, tzinfo=tz)


@lru_cache(maxsize=None)
def cached_tz(hour_str, minute_str, sign_str):
    sign = 1 if sign_str == "+" else -1
    return timezone(
        timedelta(
            hours=sign * int(hour_str),
            minutes=sign * int(minute_str),
        )
    )


def match_to_localtime(match):
    hour_str, minute_str, sec_str, micros_str = match.groups()
    micros = int(micros_str.ljust(6, "0")) if micros_str else 0
    return time(int(hour_str), int(minute_str), int(sec_str), micros)


def match_to_number(match, parse_float):
    if match.group(7):
        return parse_float(match.group())
    return int(match.group(), 0)
