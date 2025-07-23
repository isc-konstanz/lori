# -*- coding: utf-8 -*-
"""
lori.predictorss.core
~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import List

import pandas as pd
from lori.core import Registrator, ResourceException, Resources, ResourceUnavailableException, Activator
from lori.data import Channels
from lori.typing import TimestampType




class _Predictor(Registrator):
    SECTION: str = "predictor"
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



class PredictorException(ResourceException):
    """
    Raise if an error occurred accessing the predictor.

    """

    # noinspection PyArgumentList
    def __init__(self, predictor: _Predictor, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.predictor = predictor
