# -*- coding: utf-8 -*-
"""
lori.data.channels.channel
~~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Collection, Dict, List, Mapping, Optional, Type

import pandas as pd
import pytz as tz
from lori.core import Resource
from lori.core.configs import ConfigurationException, Configurations
from lori.data.channels import ChannelConnector, ChannelState
from lori.util import parse_freq, to_timedelta


class Channel(Resource):
    logger: ChannelConnector
    connector: ChannelConnector

    _timestamp: pd.Timestamp = pd.NaT
    _value: Optional[Any] = None
    _state: str | ChannelState = ChannelState.DISABLED

    # noinspection PyShadowingBuiltins
    def __init__(
        self,
        id: str = None,
        key: str = None,
        name: str = None,
        type: str | Type = None,
        connector: Optional[ChannelConnector] = None,
        logger: Optional[ChannelConnector] = None,
        **configs: Any,
    ) -> None:
        super().__init__(id=id, key=key, name=name, type=type, **configs)
        self.connector = self._assert_connector(connector)
        self.logger = self._assert_connector(logger)

    # noinspection PyMethodMayBeStatic
    def _assert_connector(self, connector: Optional[ChannelConnector]) -> ChannelConnector:
        if connector is None:
            connector = ChannelConnector(None)
        return connector

    def _get_attrs(self) -> List[str]:
        return [
            *super()._get_attrs(),
            "connector",
            "logger",
            "value",
            "state",
            "timestamp",
        ]

    # noinspection PyShadowingBuiltins
    def _get_vars(self) -> Dict[str, Any]:
        vars = super()._get_vars()
        vars["value"] = self.value
        vars["state"] = self.state
        vars["timestamp"] = self.timestamp
        return vars

    # noinspection PyShadowingBuiltins
    def __repr__(self) -> str:
        vars = OrderedDict(key=self.id)
        if self.is_valid():
            vars["value"] = str(self.value)
        else:
            vars["state"] = str(self.state)
        vars["timestamp"] = str(self.timestamp)
        return f"{type(self).__name__}({', '.join(f'{k}={v}' for k, v in vars.items())})"

    @property
    def freq(self) -> Optional[str]:
        freq = self.get(next((k for k in ["freq", "frequency", "resolution"] if k in self), None), default=None)
        if freq is not None:
            freq = parse_freq(freq)
        return freq

    @property
    def timedelta(self) -> Optional[pd.Timedelta]:
        return to_timedelta(self.freq)

    @property
    def timestamp(self) -> pd.Timestamp | pd.NaT:
        return self._timestamp

    @property
    def value(self) -> Optional[Any]:
        return self._value

    @value.setter
    def value(self, value) -> None:
        self._set(pd.Timestamp.now(tz.UTC).floor(freq="s"), value, ChannelState.VALID)

    @property
    def state(self) -> ChannelState | str:
        return self._state

    @state.setter
    def state(self, state) -> None:
        self._set(pd.Timestamp.now(tz.UTC).floor(freq="s"), None, state)

    def is_valid(self) -> bool:
        return self.state == ChannelState.VALID and self._is_valid(self.value)

    @staticmethod
    def _is_valid(value: Any) -> bool:
        if isinstance(value, Collection) and not isinstance(value, str):
            return not any(pd.isna(value))
        return not pd.isna(value)

    def set(
        self,
        timestamp: pd.Timestamp,
        value: Any,
        state: Optional[str | ChannelState] = ChannelState.VALID,
    ) -> None:
        self._set(timestamp, value, state)

    def _set(
        self,
        timestamp: pd.Timestamp,
        value: Optional[Any],
        state: str | ChannelState,
    ) -> None:
        self._timestamp = timestamp
        self._value = value
        self._state = state

    # noinspection PyProtectedMember
    def from_logger(self) -> Channel:
        channel = self.copy()
        channel._update(**self.logger._copy_configs())
        return channel

    # noinspection PyShadowingBuiltins
    def has_logger(self, *ids: Optional[str]) -> bool:
        return self.logger.enabled and any(self.logger.id == id for id in ids) if len(ids) > 0 else True

    # noinspection PyShadowingBuiltins
    def has_connector(self, id: Optional[str] = None) -> bool:
        return self.connector.enabled and self.connector.id == id if id is not None else True

    def to_series(self, state: bool = False) -> pd.Series:
        if isinstance(self.value, pd.Series):
            return self.value
        else:
            if state and pd.isna(self.value):
                data = self.state
            else:
                data = self.value
            return pd.Series(index=[self.timestamp], data=[data], name=self.key)

    def copy(self) -> Channel:
        channel = Channel(
            id=self.id,
            key=self.key,
            name=self.name,
            type=self.type,
            connector=self.connector.copy(),
            logger=self.logger.copy(),
            **self._copy_configs(),
        )
        channel.set(self._timestamp, self._value, self._state)
        return channel

    # noinspection PyShadowingBuiltins, PyProtectedMember
    def _update(
        self,
        connector: Optional[Dict[str, Any] | str] = None,
        logger: Optional[Dict[str, Any] | str] = None,
        **configs: Any,
    ) -> None:
        if connector is not None:
            connector = Channel._build_section(connector, "connector")
            self.connector._update(**connector)
        if logger is not None:
            logger = Channel._build_section(logger, "connector")
            self.logger._update(**logger)
        super()._update(**configs)

    @staticmethod
    def _build_defaults(configs: Configurations) -> Dict[str, Any]:
        return Channel._build_configs(
            {k: v for k, v in configs.items() if not isinstance(v, Mapping) or k in ["logger", "connector"]}
        )

    @staticmethod
    # noinspection PyShadowingNames
    def _build_configs(configs: Dict[str, Any]) -> Dict[str, Any]:
        def _build_registrator(section: str, key: Optional[str] = None) -> None:
            if section not in configs:
                return
            if key is None:
                key = section
            configs[section] = Channel._build_section(configs[section], key)

        _build_registrator("connector")
        _build_registrator("connector", "logger")
        return configs

    @staticmethod
    # noinspection PyShadowingNames
    def _build_section(section: Optional[Dict[str, Any] | str], key: str) -> Optional[Dict[str, Any]]:
        if section is None:
            return None
        if isinstance(section, str):
            return {key: section}
        elif not isinstance(section, Mapping):
            raise ConfigurationException(f"Invalid channel {key} type: " + str(section))
        return dict(section)
