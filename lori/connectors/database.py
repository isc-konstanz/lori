# -*- coding: utf-8 -*-
"""
lori.data.database
~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import datetime as dt
from abc import abstractmethod
from functools import wraps
from typing import Any, Optional, overload

import tzlocal

import pandas as pd
import pytz as tz
from lori.connectors import (
    ConnectionException,
    Connector,
    ConnectorException,
    ConnectorMeta,
    ConnectorUnavailableException,
)
from lori.core import Configurations, Resources
from lori.data.util import hash_data
from lori.util import convert_timezone, to_date, to_timezone

# FIXME: Remove this once Python >= 3.9 is a requirement
try:
    from typing import Literal

except ImportError:
    from typing_extensions import Literal


class DatabaseMeta(ConnectorMeta):
    # noinspection PyProtectedMember
    def __call__(cls, *args, **kwargs):
        database = super().__call__(*args, **kwargs)

        database._Database__hash = database.hash
        database.hash = database._do_hash

        database._Database__exists = database.exists
        database.exists = database._do_exists

        database._Database__read = database._Connector__read
        del database._Connector__read

        database._Database__read_first = database.read_first
        database.read_first = database._do_read_first

        database._Database__read_first_index = database.read_first_index
        database.read_first_index = database._do_read_first_index

        database._Database__read_last = database.read_last
        database.read_last = database._do_read_last

        database._Database__read_last_index = database.read_last_index
        database.read_last_index = database._do_read_last_index

        database._Database__delete = database.delete
        database.delete = database._do_delete

        return database


# noinspection PyUnresolvedReferences
class Database(Connector, metaclass=DatabaseMeta):
    timezone: tz.BaseTzInfo

    def configure(self, configs: Configurations) -> None:
        super().configure(configs)

        timezone = configs.get("timezone", None)
        if timezone is None:
            timezone = tzlocal.get_localzone_name()
        self.timezone = to_timezone(timezone)

    # noinspection PyShadowingBuiltins
    def hash(
        self,
        resources: Resources,
        start: Optional[pd.Timestamp | dt.datetime] = None,
        end: Optional[pd.Timestamp | dt.datetime] = None,
        method: Literal["MD5", "SHA1", "SHA256", "SHA512"] = "MD5",
        encoding: str = "UTF-8",
    ) -> Optional[str]:
        data = self.__read(resources, start, end)
        data = self._validate_timezone(resources, data)
        data = self._get_range(data, start, end)
        if data is None or data.empty:
            return None
        columns = [
            data.index.name,
            *[r.id for r in resources if r.id in data.columns],
        ]
        return hash_data(data.loc[:, columns], method, encoding)

    @wraps(hash, updated=())
    def _do_hash(
        self,
        resources: Resources,
        start: Optional[pd.Timestamp | dt.datetime] = None,
        end: Optional[pd.Timestamp | dt.datetime] = None,
        method: Literal["MD5", "SHA1", "SHA256", "SHA512"] = "MD5",
        encoding: str = "UTF-8",
        *args,
        **kwargs,
    ) -> Optional[str]:
        with self._lock:
            if not self._is_connected():
                raise ConnectionException(self, f"Database '{self.id}' not connected")

            return self.__hash(resources, start=start, end=end, method=method, encoding=encoding, *args, **kwargs)

    def exists(
        self,
        resources: Resources,
        start: Optional[pd.Timestamp | dt.datetime] = None,
        end: Optional[pd.Timestamp | dt.datetime] = None,
    ) -> bool:
        # TODO: Replace this placeholder more resource efficient
        data = self.__read(resources, start, end)
        data = self._validate_timezone(resources, data)
        data = self._get_range(data, start, end)
        return not data.empty

    @wraps(exists, updated=())
    def _do_exists(
        self,
        resources: Resources,
        start: Optional[pd.Timestamp | dt.datetime] = None,
        end: Optional[pd.Timestamp | dt.datetime] = None,
        *args,
        **kwargs,
    ) -> bool:
        with self._lock:
            if not self._is_connected():
                raise ConnectionException(self, f"Database '{self.id}' not connected")

            return self.__exists(resources, start=start, end=end, *args, **kwargs)

    @overload
    def read(self, resources: Resources) -> pd.DataFrame: ...

    @overload
    def read(
        self,
        resources: Resources,
        start: Optional[pd.Timestamp | dt.datetime] = None,
        end: Optional[pd.Timestamp | dt.datetime] = None,
    ) -> pd.DataFrame: ...

    @abstractmethod
    def read(
        self,
        resources: Resources,
        start: Optional[pd.Timestamp | dt.datetime] = None,
        end: Optional[pd.Timestamp | dt.datetime] = None,
    ) -> pd.DataFrame:
        pass

    @wraps(read, updated=())
    def _do_read(
        self,
        resources: Resources,
        start: Optional[pd.Timestamp | dt.datetime] = None,
        end: Optional[pd.Timestamp | dt.datetime] = None,
        *args,
        **kwargs,
    ) -> pd.DataFrame:
        with self._lock:
            if not self._is_connected():
                raise ConnectionException(self, f"Database '{self.id}' not connected")

            data = self.__read(resources, start=start, end=end, *args, **kwargs)
            data = self._validate_timezone(resources, data)
            return self._get_range(data, start, end)

    @abstractmethod
    def read_first(self, resources: Resources) -> Optional[pd.DataFrame]:
        pass

    @wraps(read_first, updated=())
    def _do_read_first(self, resources: Resources, *args, **kwargs) -> Optional[pd.DataFrame]:
        with self._lock:
            if not self._is_connected():
                raise ConnectionException(self, f"Database '{self.id}' not connected")

            data = self.__read_first(resources, *args, **kwargs)
            data = self._validate_timezone(resources, data)
            return data

    def read_first_index(self, resources: Resources) -> Optional[Any]:
        data = self.__read_first(resources)
        data = self._validate_timezone(resources, data)
        if data is None or data.empty:
            return None
        return min(data.index)

    @wraps(read_first_index, updated=())
    def _do_read_first_index(self, resources: Resources, *args, **kwargs) -> Optional[Any]:
        with self._lock:
            if not self._is_connected():
                raise ConnectionException(self, f"Database '{self.id}' not connected")

            index = self.__read_first_index(resources, *args, **kwargs)
            if isinstance(index, dt.datetime):
                index = convert_timezone(index, timezone=self.timezone)
            return index

    @abstractmethod
    def read_last(self, resources: Resources) -> Optional[pd.DataFrame]:
        pass

    @wraps(read_last, updated=())
    def _do_read_last(self, resources: Resources, *args, **kwargs) -> Optional[pd.DataFrame]:
        with self._lock:
            if not self._is_connected():
                raise ConnectionException(self, f"Database '{self.id}' not connected")

            data = self.__read_last(resources, *args, **kwargs)
            data = self._validate_timezone(resources, data)
            return data

    def read_last_index(self, resources: Resources) -> Optional[pd.Index]:
        data = self.__read_last(resources)
        data = self._validate_timezone(resources, data)
        if data is None or data.empty:
            return None
        return max(data.index)

    @wraps(read_last_index, updated=())
    def _do_read_last_index(self, resources: Resources, *args, **kwargs) -> Optional[Any]:
        with self._lock:
            if not self._is_connected():
                raise ConnectionException(self, f"Database '{self.id}' not connected")

            index = self.__read_last_index(resources, *args, **kwargs)
            if isinstance(index, dt.datetime):
                index = convert_timezone(index, timezone=self.timezone)
            return index

    def _validate_timezone(self, resources: Resources, data: pd.DataFrame) -> pd.DataFrame:
        # noinspection PyShadowingNames
        def _validate_series(series: pd.Series) -> pd.Series:
            if isinstance(series, pd.DatetimeIndex):
                series = series.tz_convert(self.timezone)
            elif pd.api.types.is_datetime64_dtype(series.values):
                series = series.dt.tz_convert(self.timezone)
            elif series.map(lambda i: isinstance(i, (pd.Timestamp, dt.datetime))).all():
                series = series.map(lambda i: i.astimezone(self.timezone))
            return series

        if not data.empty:
            data.index = _validate_series(data.index)
            for resource in resources:
                if resource.id not in data:
                    continue
                if resource.type in [pd.Timestamp, dt.datetime]:
                    resource_data = data[resource.id]
                    if pd.api.types.is_string_dtype(resource_data.values):
                        resource_data = pd.to_datetime(resource_data)
                    data[resource.id] = _validate_series(resource_data)
        return data

    @staticmethod
    def _get_range(
        data: pd.DataFrame,
        start: Optional[pd.Timestamp, dt.datetime, str] = None,
        end: Optional[pd.Timestamp, dt.datetime, str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        if data.empty:
            return data
        if start is not None:
            start = to_date(start, **kwargs)
            data = data[data.index >= start]
        if end is not None:
            end = to_date(end, **kwargs)
            data = data[data.index <= end]
        return data

    @overload
    def delete(self, resources: Resources) -> None: ...

    @overload
    def delete(
        self,
        resources: Resources,
        start: Optional[pd.Timestamp | dt.datetime] = None,
        end: Optional[pd.Timestamp | dt.datetime] = None,
    ) -> None: ...

    def delete(
        self,
        resources: Resources,
        start: Optional[pd.Timestamp | dt.datetime] = None,
        end: Optional[pd.Timestamp | dt.datetime] = None,
    ) -> None:
        raise NotImplementedError(f"Unable to delete values for database '{self.id}'")

    @wraps(delete, updated=())
    def _do_delete(
        self,
        resources: Resources,
        start: Optional[pd.Timestamp | dt.datetime] = None,
        end: Optional[pd.Timestamp | dt.datetime] = None,
        *args,
        **kwargs,
    ) -> None:
        with self._lock:
            if not self._is_connected():
                raise ConnectionException(self, f"Database '{self.id}' not connected")

            self.__delete(resources, start=start, end=end, *args, **kwargs)


class DatabaseException(ConnectorException):
    """
    Raise if an error occurred accessing the database.

    """


class DatabaseUnavailableException(ConnectorUnavailableException):
    """
    Raise if an accessed database can not be found.

    """
