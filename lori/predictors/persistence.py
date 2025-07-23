# -*- coding: utf-8 -*-
"""
lori.predictors.persistence
~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import random
from typing import Optional
from collections import OrderedDict

import numpy as np
import pandas as pd
import pytz as tz
from pandas import TimedeltaIndex

from lori import Channel, ConfigurationException, Resource, Resources, Configurations
from lori.predictors import Predictor, PredictorException, register_predictor_type
from lori.util import parse_freq, to_timedelta

from lori.typing import TimestampType

# noinspection PyShadowingBuiltins
@register_predictor_type("persistence")
class Persistence(Predictor):
    _index: list[TimedeltaIndex]
    _data: np.ndarray

    _aggregate: str = "mean"

    def configure(self, configs: Configurations) -> None:
        super().configure(configs)

        aggregate = configs.get("aggregate", default="mean")
        if aggregate not in ["mean", "std"]:
            raise ConfigurationException(
                f"Invalid aggregate function '{aggregate}', must be one of 'mean' or 'std'",
            )
        self.aggregate = aggregate

        period = configs.get("period", default="1week")
        period_freq = parse_freq(period)
        period_time = to_timedelta(period_freq).seconds

        period_count = configs.get_int("period_count", default=3)

        bin_length = configs.get("bin_length", default="1h")
        bin_length_freq = parse_freq(bin_length)
        bin_length_time = to_timedelta(bin_length_freq).seconds

        if period_time % bin_length_time != 0:
            raise ConfigurationException(
                f"Period '{period}' must be a multiple of bin length '{bin_length}'",
            )

        bin_count = period_time // bin_length_time
        index = [bin_length_time * i for i in range(bin_count)]

        self._period_s = period_time
        self._bin_length_freq = bin_length_freq
        self._index = [TimedeltaIndex(index, unit="s") for _ in range(bin_count)]

        resources_len = 2 #TODO: get from resources??? not an activator
        resources_list = [] #TODO: for ordering
        self._data = np.zeros((resources_len, bin_count, period_count), dtype=float)

        pass

    def activate(self) -> None:
        super().activate()




    def update(
        self,
        resources: Resources,
        start: TimestampType = None,
    ) -> None:
        # called once a period at the start of the period to update the predictor
        if not resources:
            raise PredictorException(self, "No resources provided for updating")
        if start is None:
            start = pd.Timestamp.now(tz=tz.UTC)
        read_end = start.floor(freq="week")
        read_start = read_end - pd.Timedelta(seconds=self._period_s)

        #last_period = self.data.from_logger([System.POWER_EL], start=read_start, end=read_end)
        last_period = self.data.to_frame(unique=False)
        if last_period.empty:
            raise PredictorException(self, "No data available for updating")

        last_period = last_period.resample(self._bin_length_freq).mean()
        last_period_array = last_period.to_numpy()


        self._data[:,:,:-1] = self._data[:,:,1:]
        self._data[:,:,-1] = last_period_array

        #TODO: test if this works
        if self.aggregate == "mean":
            aggr_data = self._data.mean(axis=2, keepdims=True)
        elif self.aggregate == "std":
            aggr_data = self._data.std(axis=2, keepdims=True)
        else:
            raise PredictorException(self, f"Invalid aggregate function '{self.aggregate}'")

        df = pd.DataFrame(
            data=aggr_data,
            index=self._index,
            columns=[resource.id for resource in resources],
        )




    def predict(
        self,
        resources: Resources,
        start: TimestampType = None,
        end: TimestampType = None,
    ) -> pd.DataFrame:
        pass
        #TODO: just return the correct df part!

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