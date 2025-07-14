# -*- coding: utf-8 -*-
"""
lori.predictions.dummy
~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import random
from typing import Optional

import pandas as pd
import pytz as tz
from lori import Channel, ConfigurationException, Resource, Resources
from lori.core import Configurations
from lori.predictions import Prediction, PredictionException, register_prediction_type
from lori.typing import TimestampType


# noinspection PyShadowingBuiltins
@register_prediction_type("dummy", "random")
class DummyPrediction(Prediction):
    _data: pd.Series

    def configure(self, configs: Configurations) -> None:
        super().configure(configs)

    def prediction(
        self,
        resources: Resources,
        start: TimestampType = None,
        end: TimestampType= None,
    ) -> pd.DataFrame:
        for resource in resources:
            generator = resource.get("generator", default="virtual")
            if generator == "random":
                self._read_random(resource)
            elif generator != "virtual":
                raise PredictionException(
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
