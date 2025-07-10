# -*- coding: utf-8 -*-
"""
lori.forecast.dummy
~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import random
from typing import Optional

import pandas as pd
import pytz as tz
from lori import Channel, ConfigurationException, Resource, Resources
from lori.forecast import Forecast, ForecastException, register_forecast_type
from lori.typing import TimestampType


# noinspection PyShadowingBuiltins
@register_forecast_type("dummy", "random")
class DummyForecast(Forecast):
    _data: pd.Series

    def forecast(
        self,
        resources: Resources,
        start: Optional[TimestampType] = None,
        end: Optional[TimestampType] = None,
    ) -> pd.DataFrame:
        for resource in resources:
            generator = resource.get("generator", default="virtual")
            if generator == "random":
                self._read_random(resource)
            elif generator != "virtual":
                raise ForecastException(
                    self, f"Trying to read dummy channel '{resource.id}' with generator: {generator}"
                )
        return self._data.to_frame(pd.Timestamp.now(tz.UTC).floor(freq="s")).T

    def _read_random(self, resource: Resource) -> None:
        range = int(abs(resource.max - resource.min))
        value = float(random.randrange(-range * 100, range * 100)) / 1000.0 + self._data[resource.id]
        if value < resource.min:
            value = resource.min
        if value > resource.max:
            value = resource.max
        self._data[resource.id] = value
