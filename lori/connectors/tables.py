# -*- coding: utf-8 -*-
"""
lori.connectors.tables
~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import datetime as dt
import os
import re
from typing import Optional

import pandas as pd
from lori.connectors import ConnectionException, Database, register_connector_type
from lori.core import Configurations, Resources
from pandas import HDFStore


@register_connector_type("tables", "hdfstore")
class HDFDatabase(Database):
    __store: HDFStore = None

    _store_dir: str
    _store_path: str

    _mode: str = "a"

    _compression_level: int | None = None
    _compression_lib = None

    # noinspection PyTypeChecker
    def configure(self, configs: Configurations) -> None:
        super().configure(configs)

        store_dir = configs.get("path", default=None)
        if store_dir is not None:
            if "~" in store_dir:
                store_dir = os.path.expanduser(store_dir)
            if not os.path.isabs(store_dir):
                store_dir = os.path.join(configs.dirs.data, store_dir)
        else:
            store_dir = configs.dirs.data

        store_path = configs.get("path", default=None)
        if store_path is not None:
            if not os.path.isabs(store_path):
                store_path = os.path.join(store_dir, store_path)
            else:
                store_dir = os.path.dirname(store_path)
        else:
            store_file = configs.get("file", default=".store.h5")
            store_path = os.path.join(store_dir, store_file)
        self._store_dir = store_dir
        self._store_path = store_path

        self._mode = configs.get("mode", default="a")
        self._compression_level = configs.get_int("compression_level", None)
        self._compression_lib = configs.get("compression_lib", None)

    def is_connected(self) -> bool:
        return self.__store is not None and self.__store.is_open

    def connect(self, resources: Resources) -> None:
        super().connect(resources)
        if not os.path.isdir(self._store_dir):
            os.makedirs(self._store_dir, exist_ok=True)
        try:
            self.__store = HDFStore(
                self._store_path,
                mode=self._mode,
                complevel=self._compression_level,
                complib=self._compression_lib,
            )
            self.__store.open()

        except IOError as e:
            raise ConnectionException(self, str(e))

    def disconnect(self) -> None:
        super().disconnect()
        if self.__store is not None:
            self.__store.close()

    # noinspection PyTypeChecker
    def read(
        self,
        resources: Resources,
        start: Optional[pd.Timestamp | dt.datetime] = None,
        end: Optional[pd.Timestamp | dt.datetime] = None,
    ) -> pd.DataFrame:
        data = []
        try:
            for group, group_resources in resources.groupby("group"):
                group_key = _format_key(group)
                if group_key not in self.__store:
                    continue

                data.append(self.__store.select(group_key, where=_build_where(start, end), columns=group_resources.ids))
        except IOError as e:
            raise ConnectionException(self, str(e))

        if len(data) == 0:
            return pd.DataFrame()
        return pd.concat(data, axis="columns")

    # noinspection PyTypeChecker
    def read_first(self, resources: Resources) -> Optional[pd.DataFrame]:
        data = []
        try:
            for group, group_resources in resources.groupby("group"):
                group_key = _format_key(group)
                if group_key not in self.__store:
                    continue

                data.append(self.__store.select(group_key, stop=0, columns=group_resources.ids))
        except IOError as e:
            raise ConnectionException(self, str(e))

        if len(data) == 0:
            return pd.DataFrame()
        return pd.concat(data, axis="columns")

    # noinspection PyTypeChecker
    def read_last(self, resources: Resources) -> Optional[pd.DataFrame]:
        data = []
        try:
            for group, group_resources in resources.groupby("group"):
                group_key = _format_key(group)
                if group_key not in self.__store:
                    continue

                data.append(self.__store.select(group_key, start=0, columns=group_resources.ids))
        except IOError as e:
            raise ConnectionException(self, str(e))

        if len(data) == 0:
            return pd.DataFrame()
        return pd.concat(data, axis="columns")

    def delete(
        self,
        resources: Resources,
        start: Optional[pd.Timestamp | dt.datetime] = None,
        end: Optional[pd.Timestamp | dt.datetime] = None,
    ) -> None:
        try:
            for group, group_resources in resources.groupby("group"):
                group_key = _format_key(group)
                if group_key not in self.__store:
                    continue

                self.__store.remove(_format_key(group_key))

        except IOError as e:
            raise ConnectionException(self, str(e))

    def write(self, data: pd.DataFrame) -> None:
        try:
            for group, group_resources in self.resources.filter(lambda c: c.id in data.columns).groupby("group"):
                group_key = _format_key(group)
                group_data = data[group_resources.ids]
                if group_key not in self.__store:
                    self.__store.put(group_key, group_data, format="table", encoding="UTF-8")
                else:
                    self.__store.append(group_key, group_data, format="table", encoding="UTF-8")

        except IOError as e:
            raise ConnectionException(self, str(e))


def _format_key(key: str) -> str:
    key = re.sub(r"\W", "/", key).replace("_", "/").lower()
    return f"/{key}"


def _build_where(
    start: Optional[pd.Timestamp | dt.datetime] = None,
    end: Optional[pd.Timestamp | dt.datetime] = None,
) -> Optional[str]:
    where = []
    if start is not None:
        where.append(f'index>=Timestamp("{start.isoformat()}")')
    if end is not None:
        where.append(f'index<=Timestamp("{end.isoformat()}")')
    return " & ".join(where) if len(where) > 0 else None
