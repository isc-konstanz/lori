# -*- coding: utf-8 -*-
"""
lori.predictions.persistence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import random
from typing import Optional
from collections import OrderedDict

import pandas as pd
import pytz as tz
from lori import Channel, ConfigurationException, Resource, Resources, Configurations
from lori.predictions import Prediction, PredictionException, register_prediction_type
from lori.typing import TimestampType
from lori.util import parse_freq, to_timedelta


# noinspection PyShadowingBuiltins
@register_prediction_type("persistence")
class Persistence(Prediction):
    _data: dict[str, pd.DataFrame] = {}

    def configure(self, configs: Configurations) -> None:
        super().configure(configs)

        period = configs.get("period", default="1week")
        period_freq = parse_freq(period)
        period_time = to_timedelta(period_freq).seconds

        period_count = configs.get_int("period_count", default=3)

        bin_length = configs.get("bin_length", default="1h")
        bin_length_freq = parse_freq(bin_length)
        bin_length_time = to_timedelta(bin_length_freq).seconds

        if period_time % bin_length_time != 0:
            raise ConfigurationException(
                self,
                f"Period '{period}' must be a multiple of bin length '{bin_length}'",
            )

        bin_count = period_time // bin_length_time
        self._data = OrderedDict((str(i), pd.DataFrame()) for i in range(bin_count))

        pass







    def predict(
        self,
        resources: Resources,
    ) -> pd.DataFrame:
        pass
        # if not resources:
        #     raise PredictionException(self, "No resources provided for predictioning")
        # fetch_start = start.floor(freq="h")
        # fetch_end = end.ceil(freq="h")
        #
        #
        # for resource in resources:
        #     resource_id = resource.id
        #     if self._data[resource_id] is None:
        #         self._data[resource_id] = pd.Series(dtype=float)
        #
        #     if resource_id not in self._data:
        #         fetch_start = fetch_start - pd.Timedelta(weeks=3)
        #         self._data[resource_id] = self.channels[resource_id].read(
        #             start=fetch_start,
        #             end=fetch_end,
        #         ).resample("1h").mean()
        #     else:
        #         self._data[resource_id] = self._data[resource_id].loc[fetch_start:fetch_end]
        #         fetch_start = self._data[resource_id].index[-1]
        #         self._data[resource_id].loc[fetch_start:fetch_end] = self.channels[resource_id].read(
        #             start=fetch_start,
        #             end=fetch_end,
        #         ).resample("1h").mean()
        #
        #
        # return self._data.to_frame(pd.Timestamp.now(tz.UTC).floor(freq="s")).T


def _timestamp_to_week(timestamp: TimestampType) -> int:
    """
    Convert a timestamp to a bin index.
    """
    if isinstance(timestamp, pd.Timestamp):
        timestamp = timestamp.to_pydatetime()
    return int(timestamp.timestamp() // 3600)