# -*- coding: utf-8 -*-
"""
loris.data.channels.connector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, Optional

import pandas as pd
from loris.core import ResourceException


class ChannelConnector:
    __configs: OrderedDict[str, Any]

    enabled: bool = False

    timestamp: pd.Timestamp = pd.NaT

    # noinspection PyShadowingBuiltins
    def __init__(self, connector, **configs: Any) -> None:
        self.__configs = OrderedDict(configs)
        self._connector = self._assert_connector(connector)

        self.enabled = self.__configs.pop("enabled", connector is not None and connector.is_enabled())

    # noinspection PyMethodMayBeStatic
    def _assert_connector(self, connector):
        from loris.connectors import Connector

        if connector is None:
            return None
        if not isinstance(connector, Connector):
            raise ResourceException(f"Invalid connector: {None if connector is None else type(connector)}")
        return connector

    # noinspection PyShadowingBuiltins
    def _get_vars(self) -> Dict[str, Any]:
        vars = self._copy_configs()
        vars["timestamp"] = self.timestamp
        vars["enabled"] = self.enabled
        return vars

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.id})"

    def __str__(self) -> str:
        return f"{type(self).__name__}:\n\tid={self.id}\n\t" + "\n\t".join(
            f"{k}={v}" for k, v in self._get_vars().items()
        )

    def __getattr__(self, attr):
        # __getattr__ gets called when the item is not found via __getattribute__
        # To avoid recursion, call __getattribute__ directly to get components dict
        configs = ChannelConnector.__getattribute__(self, f"_{ChannelConnector.__name__}__configs")
        if attr in configs.keys():
            return configs[attr]
        raise AttributeError(f"'{type(self).__name__}' object has no configuration '{attr}'")

    @property
    def id(self) -> Optional[str]:
        return self._connector.id if self._connector is not None else None

    @property
    def key(self) -> str:
        return self._connector.key if self._connector is not None else None

    def copy(self) -> ChannelConnector:
        configs = self._copy_configs()
        configs["enabled"] = self.enabled
        return type(self)(self._connector, **configs)

    # noinspection PyShadowingBuiltins
    def _copy_configs(self) -> Dict[str, Any]:
        return OrderedDict(**self.__configs)
