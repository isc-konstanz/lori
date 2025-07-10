# -*- coding: utf-8 -*-
"""
lori.forecast.connector
~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import datetime as dt
from abc import abstractmethod
from collections import OrderedDict
from functools import wraps
from threading import Lock
from typing import Any, Dict, Optional

import pandas as pd
import pytz as tz
from lori.forecast.core import ForecastException, _Forecast
from lori.core import Context, Registrator, Resource, ResourceException, Resources
from lori.core.configs import ConfigurationException, Configurations
from lori.core.configs.configurator import Configurator, ConfiguratorMeta
from lori.data.channels import Channel, Channels, ChannelState
from lori.data.validation import validate_index


class ForecastMeta(ConfiguratorMeta):
    # noinspection PyProtectedMember
    def __call__(cls, *args, **kwargs):
        forecast = super().__call__(*args, **kwargs)
        cls._wrap_method(forecast, "connect")
        cls._wrap_method(forecast, "disconnect")
        cls._wrap_method(forecast, "read")
        cls._wrap_method(forecast, "write")

        return forecast


class Forecast(_Forecast, metaclass=ForecastMeta):

    __resources: Resources

    _lock: Lock

    def __init__(
        self,
        context: Context | Registrator,
        configs: Optional[Configurations] = None,
        **kwargs,
    ) -> None:
        super().__init__(context=context, configs=configs, **kwargs)
        self.__resources = Resources()
        self._lock = Lock()

    def __enter__(self) -> Forecast:
        return self

    # noinspection PyShadowingBuiltins
    def __exit__(self, type, value, traceback):
        pass

    @classmethod
    def _assert_context(cls, context: Context | Registrator) -> Context:
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

    @abstractmethod
    def forecast(self, resources: Resources) -> pd.DataFrame:
        pass

    # noinspection PyUnresolvedReferences, PyTypeChecker
    @wraps(read, updated=())
    def _do_forecast(self, resources: Resources, *args, **kwargs) -> pd.DataFrame:
        with self._lock:
            data = self._run_read(resources, *args, **kwargs)
            data = self._validate(resources, data)
            return data

    # noinspection PyMethodMayBeStatic
    def _validate(self, resources: Resources, data: pd.DataFrame) -> pd.DataFrame:
        if not data.empty:
            data = validate_index(data)
            for resource in resources:
                if resource.id not in data:
                    continue
                if resource.type in [pd.Timestamp, dt.datetime]:
                    resource_data = data[resource.id]
                    if pd.api.types.is_string_dtype(resource_data.values):
                        data[resource.id] = pd.to_datetime(resource_data)
        return data
