# -*- coding: utf-8 -*-
"""
lori.connectors.connector
~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from abc import abstractmethod
from collections import OrderedDict
from enum import Enum
from functools import wraps
from threading import Lock
from typing import Any, Dict, List, Optional

import pandas as pd
import pytz as tz
from lori import Channel, Channels, ChannelState
from lori.core import Context, Registrator, Resource, ResourceException, Resources, ResourceUnavailableException
from lori.core.configs import ConfigurationException, Configurations, Configurator, ConfiguratorMeta


class ConnectorMeta(ConfiguratorMeta):
    # noinspection PyProtectedMember
    def __call__(cls, *args, **kwargs):
        connector = super().__call__(*args, **kwargs)

        connector._Connector__connect = connector.connect
        connector.connect = connector._do_connect

        connector._Connector__disconnect = connector.disconnect
        connector.disconnect = connector._do_disconnect

        connector._Connector__read = connector.read
        connector.read = connector._do_read

        connector._Connector__write = connector.write
        connector.write = connector._do_write

        return connector


class ConnectType(Enum):
    NONE = "NONE"
    AUTO = "AUTO"

    @classmethod
    def  get(cls, value: str | bool) -> ConnectType:
        if isinstance(value, str):
            value = value.lower()
            if value.upper() in ["auto", "true"]:
                return ConnectType.AUTO
            if value.upper() == ["none", "false"]:
                return ConnectType.NONE
        if isinstance(value, bool):
            if value:
                return ConnectType.AUTO
            else:
                return ConnectType.NONE
        raise ValueError("Unknown ConnectType: " + str(value))

    def __str__(self):
        return str(self.value)


class Connector(Registrator, metaclass=ConnectorMeta):
    SECTION: str = "connector"
    INCLUDES: List[str] = []

    _connected: bool = False
    _connect_type: ConnectType = ConnectType.AUTO
    _connect_timestamp: pd.Timestamp = pd.NaT
    _disconnect_timestamp: pd.Timestamp = pd.NaT
    _reconnect_interval: pd.Timedelta = pd.Timedelta(minutes=1)

    __resources: Resources

    _lock: Lock

    def __init__(
        self,
        context: Registrator | Context,
        configs: Optional[Configurations] = None,
        **kwargs,
    ) -> None:
        super().__init__(context=context, configs=configs, **kwargs)
        self.__resources = Resources()
        self._lock = Lock()

    def __enter__(self) -> Connector:
        self.connect(self.__resources)
        return self

    # noinspection PyShadowingBuiltins
    def __exit__(self, type, value, traceback):
        self.disconnect()

    @classmethod
    def _assert_context(cls, context: Registrator | Context) -> Context:
        if context is None:
            raise ResourceException(f"Invalid '{cls.__name__}' context: {type(context)}")
        return super()._assert_context(context)

    # noinspection PyShadowingBuiltins, PyProtectedMember
    def _get_vars(self) -> Dict[str, Any]:
        vars = super()._get_vars()

        # Channels are a subset of resources, hence omit them from printing
        vars.pop("channels", None)
        return vars

    # noinspection PyShadowingBuiltins
    def _convert_vars(self, convert: callable = str) -> Dict[str, str]:
        vars = self._get_vars()
        values = OrderedDict()
        try:
            id = vars.pop("id", self.id)
            key = vars.pop("key", self.key)
            if id != key:
                values["id"] = id
            values["key"] = key
        except (ResourceException, AttributeError):
            # Abstract properties are not yet instanced
            pass

        if "name" in vars:
            values["name"] = vars.pop("name")

        values.update(
            {
                k: str(v) if not isinstance(v, (Resource, Resources, Configurator, Context)) else convert(v)
                for k, v in vars.items()
            }
        )
        values["context"] = convert(self.context)
        values["configurations"] = convert(self.configs)
        values["configured"] = str(self.is_configured())
        values["connected"] = str(self._is_connected())
        values["enabled"] = str(self.is_enabled())
        return values

    @property
    def resources(self) -> Resources:
        return self.__resources

    @property
    def channels(self) -> Channels:
        return Channels([resource for resource in self.__resources if isinstance(resource, Channel)])

    def set_channels(self, state: ChannelState) -> None:
        # Set only channel states for channels, that actively are getting read or written by this connector.
        # Local channels may be logging channels as well, which need to be skipped.
        for channel in self.channels.filter(lambda c: c.has_connector(self.id)):
            channel.state = state

    def configure(self, configs: Configurations) -> None:
        super().configure(configs)
        self._connect_type = ConnectType.get(configs.get("connect", default=True))

    def _is_disconnected(self) -> bool:
        return not self._is_connected()

    def _is_reconnectable(self) -> bool:
        return (
            self.is_enabled()
            and self.is_configured()
            and self._is_connectable()
            and (
                pd.isna(self._disconnect_timestamp)
                or pd.Timestamp.now(tz.UTC) >= self._disconnect_timestamp + self._reconnect_interval
            )
        )

    def _is_connectable(self) -> bool:
        return self._is_disconnected() and self._connect_type == ConnectType.AUTO

    def _is_connected(self) -> bool:
        return self.is_connected() and self._connected

    def is_connected(self) -> bool:
        return True

    def connect(self, resources: Resources) -> None:
        pass

    # noinspection PyUnresolvedReferences, PyTypeChecker
    @wraps(connect, updated=())
    def _do_connect(self, resources: Resources, *args, **kwargs) -> None:
        with self._lock:
            if not self.is_enabled():
                raise ConfigurationException(f"Trying to connect disabled {type(self).__name__}: {self.id}")
            if not self.is_configured():
                raise ConfigurationException(f"Trying to connect unconfigured {type(self).__name__}: {self.id}")
            if self._is_connected():
                self._logger.warning(f"{type(self).__name__} '{self.id}' already connected")
                return

            self.__connect(resources, *args, **kwargs)
            self._on_connect(resources)
            self._disconnect_timestamp = pd.NaT
            self._connect_timestamp = pd.Timestamp.now(tz.UTC)
            self._connected = True
            self.__resources = resources

    def _on_connect(self, resources: Resources) -> None:
        pass

    def disconnect(self) -> None:
        pass

    # noinspection PyUnresolvedReferences, PyTypeChecker
    @wraps(disconnect, updated=())
    def _do_disconnect(self) -> None:
        with self._lock:
            if self._is_connected():
                return

            self.__disconnect()
            self._on_disconnect()
            self._disconnect_timestamp = pd.Timestamp.now(tz.UTC)
            self._connect_timestamp = pd.NaT
            self._connected = False

    def _on_disconnect(self) -> None:
        pass

    @abstractmethod
    def read(self, resources: Resources) -> pd.DataFrame:
        pass

    # noinspection PyUnresolvedReferences, PyTypeChecker
    @wraps(read, updated=())
    def _do_read(self, resources: Resources, *args, **kwargs) -> pd.DataFrame:
        with self._lock:
            if not self._is_connected():
                raise ConnectorException(self, f"Trying to read from unconnected {type(self).__name__}: {self.id}")

            return self.__read(resources, *args, **kwargs)

    @abstractmethod
    def write(self, data: pd.DataFrame) -> None:
        pass

    # noinspection PyUnresolvedReferences, PyTypeChecker
    @wraps(write, updated=())
    def _do_write(self, data: pd.DataFrame, *args, **kwargs) -> None:
        with self._lock:
            if not self._is_connected():
                raise ConnectorException(self, f"Trying to write to unconnected {type(self).__name__}: {self.id}")
            unknown = [c for c in data.columns if c not in self.resources]
            if len(unknown) > 0:
                raise ConnectorException(
                    self,
                    f"Trying to read unknown resource{'s' if len(unknown) > 0 else ''} '{', '.join(unknown)}' for "
                    f"{type(self).__name__}: {self.id}",
                )

            self.__write(data, *args, **kwargs)


class ConnectorException(ResourceException):
    """
    Raise if an error occurred accessing the connector.

    """

    # noinspection PyArgumentList
    def __init__(self, connector: Connector, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.connector = connector


class ConnectorUnavailableException(ResourceUnavailableException, ConnectorException):
    """
    Raise if an accessed connector can not be found.

    """


class ConnectionException(ConnectorException):
    """
    Raise if an error occurred with the connection.

    """
