# -*- coding: utf-8 -*-
"""
lori.predictors.prediction
~~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import datetime as dt
from abc import abstractmethod
from collections import OrderedDict
from functools import wraps
from threading import Lock
from typing import Any, Dict, Optional

import pandas as pd
from lori.core import Context, Registrator, Resource, ResourceException, Resources
from lori.core.configs import ConfigurationException, Configurations
from lori.core.configs.configurator import Configurator, ConfiguratorMeta
from lori.data.channels import Channel, Channels, ChannelState
from lori.data.validation import validate_index
from lori.predictors.core import PredictorException, _Predictor
from lori.typing import TimestampType


class PredictorMeta(ConfiguratorMeta):
    # noinspection PyProtectedMember
    def __call__(cls, *args, **kwargs):
        prediction = super().__call__(*args, **kwargs)
        cls._wrap_method(prediction, "prediction")

        return prediction


class Predictor(_Predictor, metaclass=PredictorMeta):

    __resources: Resources

    def __init__(
        self,
        context: Context | Registrator,
        configs: Optional[Configurations] = None,
        **kwargs,
    ) -> None:
        super().__init__(context=context, configs=configs, **kwargs)
        self.__resources = Resources()

    def __enter__(self) -> Predictor:
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
    def predict(
            self,
            resources: Resources,
    ) -> pd.DataFrame:
        pass

    # noinspection PyUnresolvedReferences, PyTypeChecker
    @wraps(predict, updated=())
    def _do_predict(self, resources: Resources, *args, **kwargs) -> pd.DataFrame:
        data = self._run_prediction(resources, start, end, *args, **kwargs) #TODO: is _run_prediction a workaround for the @wraps decorator
        #prediction correction from util
        data = self._validate(resources, data)
        return data

    # noinspection PyMethodMayBeStatic
    def _validate(self, resources: Resources, data: pd.DataFrame) -> pd.DataFrame:
        if not data.empty:
            data = validate_index(data)
            for resource in resources:
                if resource.id in data and resource.type in TimestampType: #TODO: TimestampType
                    resource_data = data[resource.id]
                    if pd.api.types.is_string_dtype(resource_data.values):
                        data[resource.id] = pd.to_datetime(resource_data)
        return data
