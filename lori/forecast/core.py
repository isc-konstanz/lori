# -*- coding: utf-8 -*-
"""
lori.forecast.core
~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import List

import pandas as pd
from lori.core import Registrator, ResourceException, Resources, ResourceUnavailableException
from lori.data import Channels


# class ConnectType(Enum):
#     NONE = "NONE"
#     AUTO = "AUTO"
#
#     @classmethod
#     def get(cls, value: str | bool) -> ConnectType:
#         if isinstance(value, str):
#             value = value.lower()
#             if value.upper() in ["auto", "true"]:
#                 return ConnectType.AUTO
#             if value.upper() == ["none", "false"]:
#                 return ConnectType.NONE
#         if isinstance(value, bool):
#             if value:
#                 return ConnectType.AUTO
#             else:
#                 return ConnectType.NONE
#         raise ValueError("Unknown ConnectType: " + str(value))
#
#     def __str__(self):
#         return str(self.value)


class _Forecast(Registrator):
    SECTION: str = "forecast"
    INCLUDES: List[str] = []

    @property
    @abstractmethod
    def resources(self) -> Resources:
        pass

    @property
    @abstractmethod
    def channels(self) -> Channels:
        pass


    @abstractmethod
    def forecast(self, resources: Resources) -> pd.DataFrame:
        pass



class ForecastException(ResourceException):
    """
    Raise if an error occurred accessing the forecast.

    """

    # noinspection PyArgumentList
    def __init__(self, forecast: _Forecast, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.forecast = forecast


class ForecastUnavailableException(ResourceUnavailableException, ForecastException):
    """
    Raise if an accessed forecast can not be found.

    """
