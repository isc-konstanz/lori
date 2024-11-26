# -*- coding: utf-8 -*-
"""
lori.converters.converter
~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import datetime as dt
from abc import abstractmethod
from typing import Any, Generic, Type, TypeVar, overload

import pandas as pd
from lori.core import Registrator, ResourceException
from lori.util import to_bool, to_date, to_float, to_int

T = TypeVar("T", bound=Any)


class Converter(Registrator, Generic[T]):
    SECTION: str = "converter"

    @property
    @abstractmethod
    def dtype(self) -> Type[T]:
        pass

    @overload
    def convert(self, value: str | T) -> T: ...

    @overload
    def convert(self, value: pd.Series) -> pd.Series: ...

    @abstractmethod
    def convert(self, value: str | T | pd.Series) -> T | pd.Series:
        pass

    @overload
    def revert(self, value: str | T) -> T: ...

    @overload
    def revert(self, value: pd.Series) -> pd.Series: ...

    @abstractmethod
    def revert(self, value: T | pd.Series) -> str | pd.Series:
        pass


class ConversionException(ResourceException, TypeError):
    """
    Raise if a conversion failed
    """


class GenericConverter(Converter, Generic[T]):
    def convert(self, value: str | float | pd.Series) -> T | pd.Series:
        try:
            if issubclass(type(value), pd.Series):
                return value.apply(self._convert)  # .astype(self.dtype)
            elif isinstance(value, (str, float)):
                return self._convert(value)
        except TypeError:
            pass
        raise ConversionException(f"Expected str or {self.dtype}, not: {type(value)}")

    @abstractmethod
    def _convert(self, value: str | T) -> T:
        pass

    def revert(self, value: T | pd.Series) -> str | pd.Series:
        if issubclass(type(value), pd.Series):
            return value.apply(lambda v: str(v)).astype(str)
        return str(value)


class DatetimeConverter(GenericConverter[dt.datetime]):
    dtype: Type[dt.datetime] = dt.datetime

    def _convert(self, value: str | pd.Timestamp | dt.datetime) -> pd.Timestamp | dt.datetime:
        return to_date(value)


class TimestampConverter(DatetimeConverter):
    dtype: Type[pd.Timestamp] = pd.Timestamp


class StringConverter(GenericConverter[str]):
    dtype: Type[str] = str

    def _convert(self, value: Any) -> str:
        return str(value)


class FloatConverter(GenericConverter[float]):
    dtype: Type[float] = float

    def _convert(self, value: str | float) -> float:
        return to_float(value)


class IntConverter(GenericConverter[int]):
    dtype: Type[int] = int

    def _convert(self, value: str | int) -> int:
        return to_int(value)


class BoolConverter(GenericConverter[bool]):
    dtype: Type[bool] = bool

    def _convert(self, value: str | bool) -> bool:
        return to_bool(value)