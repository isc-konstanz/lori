# -*- coding: utf-8 -*-
"""
loris.util
~~~~~~~~~~


"""

import datetime as dt
import re
from copy import copy
from dateutil.relativedelta import relativedelta
from typing import List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import pytz as tz
from pandas.tseries.frequencies import to_offset

# noinspection SpellCheckingInspection
INVALID_CHARS = "'!@#$%^&?*;:,./\\|`´+~=- "


# noinspection PyUnresolvedReferences, PyShadowingBuiltins, PyShadowingNames
def is_type(series: pd.Series, *type: str) -> bool:
    series_name = series.name.split("_")
    series_suffix = series_name[(-1 if len(series_name) < 3 else -2) :]
    return any(t in series_suffix for t in type)


def infer_resample_method(series: pd.Series) -> str:
    if is_type(series, "state", "state", "mode", "code"):
        return "max"
    elif is_type(series, "timestamp", "time", "progress", "energy"):
        return "last"
    else:
        return "mean"


# noinspection PyUnresolvedReferences
def resample(data: Union[pd.DataFrame, pd.Series], resolution: int) -> pd.DataFrame:
    resampled = []

    for column, series in (data if isinstance(data, pd.DataFrame) else data.to_frame()).items():
        series = series.dropna()
        series = resample_series(series, resolution, infer_resample_method(series))

        resampled.append(series)

    resampled = pd.concat(resampled, axis="columns")
    resampled.index.name = data.index.name
    return resampled.dropna(how="all")


# noinspection PyUnresolvedReferences
def resample_series(
    data: pd.Series,
    resolution: int,
    method: str,
    offset: pd.Timedelta = None
) -> pd.Series:
    kwargs = {}
    if offset is not None:
        kwargs["offset"] = offset
    index = copy(data.index)
    freq = index.freq
    if freq is None and len(index) > 2:
        freq = pd.tseries.frequencies.to_offset(pd.infer_freq(index))
    if freq is None or freq.delta < pd.Timedelta(seconds=resolution):
        # FIXME: AttributeError: 'NoneType' object has no attribute 'delta'
        resampled = data.resample(f"{int(resolution)}s", closed="right", **kwargs)
        if method == "mean":
            data = resampled.mean()
        elif method == "max":
            # The max method is commonly used vor integer state/state/code values
            data = resampled.max().astype(int)
        elif method == "sum":
            data = resampled.sum()
        elif method == "last":
            data = resampled.last()
        else:
            raise ValueError(f"Unknown resampling method: {method}")

        data.index += to_offset(f"{int(resolution)}s")
    return data[(data.index >= index[0]) & (data.index <= index[-1])]


def derive_by_hours(data: pd.Series) -> pd.Series:
    """
    Derive a data series by hours.

    Parameters
    ----------
    data : pd.Series
        Series with the data to be derived

    Returns
    ----------
    fixed: pd.Series
        Series with the derived data

    """
    delta_value = data.iloc[:].astype("float64").diff()

    delta_index = pd.Series(delta_value.index, index=delta_value.index)
    delta_index = (delta_index - delta_index.shift(1)) / np.timedelta64(1, "h")

    return pd.Series(delta_value / delta_index, index=data.index).dropna()


def convert_timezone(
    date: Union[dt.datetime, pd.Timestamp, str],
    timezone: dt.tzinfo = tz.UTC
) -> Optional[pd.Timestamp]:
    if date is None:
        return None
    if isinstance(date, str):
        import dateutil.parser

        date = dateutil.parser.parse(date)
    if isinstance(date, dt.datetime):
        date = pd.Timestamp(date)

    if isinstance(date, pd.Timestamp):
        if date.tzinfo is None or date.tzinfo.utcoffset(date) is None:
            return date.tz_localize(timezone)
        else:
            return date.tz_convert(timezone)
    else:
        raise ConversionException(f"Unable to convert date of type {type(date)}")


def slice_range(
    start: Union[dt.datetime, pd.Timestamp, str],
    end: Union[dt.datetime, pd.Timestamp, str],
    timezone: dt.tzinfo = None,
    freq: str = "D",
    **kwargs,
) -> List[Tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]]]:
    start = to_date(start, timezone, **kwargs)
    end = to_date(end, timezone, **kwargs)

    if start is None or end is None:
        return [(start, end)]

    freq_delta = to_timedelta(freq)

    ranges = []
    range_start = start
    range_end = min(ceil_date(range_start, freq=freq), end)
    ranges.append((range_start, range_end))

    while range_end < end:
        range_start = floor_date(range_start + freq_delta, freq=freq)
        range_end = min(ceil_date(range_start, freq=freq), end)
        ranges.append((range_start, range_end))
    return ranges


def floor_date(
    date: Union[dt.datetime, pd.Timestamp, str],
    timezone: dt.tzinfo = None,
    freq: str = "D"
) -> Optional[pd.Timestamp]:
    if date is None:
        return None
    if timezone is None:
        timezone = date.tzinfo
    date = convert_timezone(date, timezone)
    freq = _parse_freq(freq)
    if freq in ["Y", "M"]:
        return date.tz_localize(None).to_period(freq).to_timestamp().tz_localize(timezone)
    elif any([freq.endswith(f) for f in ["D", "h", "min", "s"]]):
        return date.tz_localize(None).floor(freq).tz_localize(timezone)
    else:
        raise ValueError(f"Invalid frequency: {freq}")


def ceil_date(
    date: Union[dt.datetime, pd.Timestamp, str],
    timezone: dt.tzinfo = None,
    freq: str = "D"
) -> Optional[pd.Timestamp]:
    date = floor_date(date, timezone, freq)
    if date is None:
        return None

    return date + to_timedelta(freq) - dt.timedelta(microseconds=1)


# noinspection PyShadowingBuiltins
def to_date(
    date: Union[str, int, dt.datetime, pd.Timestamp],
    timezone: dt.tzinfo = None,
    format: str = "%d.%m.%Y"
) -> Optional[pd.Timestamp]:
    if date is None:
        return None

    if isinstance(date, str):
        date = pd.Timestamp(dt.datetime.strptime(date, format))
    if isinstance(date, int):
        date = pd.Timestamp(dt.datetime.fromtimestamp(date))
    if timezone is not None:
        date = convert_timezone(date, timezone)
    return date


def to_timedelta(freq: str) -> Union[relativedelta, pd.Timedelta]:
    freq_val = "".join(s for s in freq if s.isnumeric())
    freq_val = int(freq_val) if len(freq_val) > 0 else 1
    freq = _parse_freq(freq)
    if freq == "Y":
        return relativedelta(years=freq_val)
    elif freq == "M":
        return relativedelta(months=freq_val)
    elif freq.endswith("D"):
        return pd.Timedelta(days=freq_val)
    elif freq.endswith("h"):
        return pd.Timedelta(hours=freq_val)
    elif freq.endswith("min"):
        return pd.Timedelta(minutes=freq_val)
    elif freq.endswith("s"):
        return pd.Timedelta(seconds=freq_val)
    else:
        raise ValueError(f"Invalid frequency: {freq}")


def to_float(value: Union[str, float]) -> float:
    if isinstance(value, str):
        return float(value)
    return value


def to_int(value: Union[str, int]) -> int:
    if isinstance(value, str):
        return int(value)
    return value


def to_bool(value: Union[str, bool]) -> bool:
    if isinstance(value, str):
        return value.lower() in ["true", "yes", "y"]
    return value


# noinspection SpellCheckingInspection
def _parse_freq(f: str) -> str:
    v = "".join(s for s in f if s.isnumeric())
    v = int(v) if len(v) > 0 else 1
    if f.upper() == "Y":
        return "Y"
    elif f.upper() == "M":
        return "M"
    elif f.lower().endswith(("d", "day", "days")):
        return f"{v}D"
    elif f.lower().endswith(("h", "hour", "hours")):
        return f"{v}h"
    elif f.lower().endswith(("t", "min", "mins")):
        return f"{v}min"
    elif f.lower().endswith(("s", "sec", "secs")):
        return f"{v}s"
    else:
        raise ValueError(f"Invalid frequency: {f}")


def parse_id(s: str) -> str:
    for c in INVALID_CHARS:
        s = s.replace(c, "_")
    return re.sub("[^\\w]+", "", s).lower()


class ConversionException(Exception):
    """
    Raise if a conversion failed

    """
