# -*- coding: utf-8 -*-
"""
lori.predictions.core
~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import List

import pandas as pd
from lori.core import Registrator, ResourceException, Resources, ResourceUnavailableException
from lori.data import Channels
from lori.typing import TimestampType




class _Prediction(Registrator):
    SECTION: str = "prediction"
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
    def predict(self, resources: Resources) -> pd.DataFrame:
        pass



class PredictionException(ResourceException):
    """
    Raise if an error occurred accessing the prediction.

    """

    # noinspection PyArgumentList
    def __init__(self, prediction: _Prediction, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.prediction = prediction


class PredictionUnavailableException(ResourceUnavailableException, PredictionException):
    """
    Raise if an accessed prediction can not be found.

    """
