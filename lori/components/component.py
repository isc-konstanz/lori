# -*- coding: utf-8 -*-
"""
lori.components.component
~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, Optional

import pandas as pd
from lori.components import ComponentAccess
from lori.components.core import _Component
from lori.connectors import ConnectorAccess
from lori.converters import ConverterAccess
from lori.core import Configurations, Context, Registrator
from lori.data import DataAccess
from lori.util import to_date


# noinspection PyAbstractClass
class Component(_Component):
    __converters: ConverterAccess
    __connectors: ConnectorAccess
    __components: ComponentAccess
    __data: DataAccess

    def __init__(
        self,
        context: Context | Registrator,
        configs: Optional[Configurations] = None,
        **kwargs,
    ) -> None:
        super().__init__(context=context, configs=configs, **kwargs)
        self.__converters = ConverterAccess(self, configs=configs.get_section("converters", ensure_exists=True))
        self.__connectors = ConnectorAccess(self, configs=configs.get_section("connectors", ensure_exists=True))
        self.__components = ComponentAccess(self, configs=configs.get_section("components", ensure_exists=True))
        self.__data = DataAccess(self, configs=configs.get_section(DataAccess.SECTION, ensure_exists=True))

    def _at_configure(self, configs: Configurations) -> None:
        self.__converters.configure(configs.get_section("converters", ensure_exists=True))
        self.__connectors.configure(configs.get_section("connectors", ensure_exists=True))
        self.__components.configure(configs.get_section("components", ensure_exists=True))
        self.__data.configure(configs.get_section(DataAccess.SECTION, ensure_exists=True))

    def _on_configure(self, configs: Configurations) -> None:
        self.__converters.load()
        self.__connectors.load()
        self.__components.load()
        self.__data.load()

    @property
    def components(self) -> ComponentAccess:
        return self.__components

    @property
    def converters(self) -> ConverterAccess:
        return self.__converters

    @property
    def connectors(self) -> ConnectorAccess:
        return self.__connectors

    @property
    def data(self):
        return self.__data

    def get(
        self,
        start: Optional[pd.Timestamp, dt.datetime, str] = None,
        end: Optional[pd.Timestamp, dt.datetime, str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        data = self.__data.to_frame(unique=False)
        if data.empty or start < data.index[0] or end > data.index[-1]:
            logged = self.__data.from_logger(start=start, end=end, unique=False)
            if not logged.empty:
                data = logged if data.empty else data.combine_first(logged)
        return self._get_range(data, start, end, **kwargs)

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

    # noinspection PyShadowingBuiltins
    def _get_vars(self) -> Dict[str, Any]:
        vars = super()._get_vars()
        vars.pop("type", None)
        return vars
