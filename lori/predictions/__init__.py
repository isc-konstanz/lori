# -*- coding: utf-8 -*-
"""
lori.predictions
~~~~~~~~~~~~~~~~


"""

from .core import (  # noqa: F401
    _Prediction,
    PredictionException,
    PredictionUnavailableException,
)

from . import access  # noqa: F401
from .access import PredictionAccess  # noqa: F401

from . import context  # noqa: F401
from .context import (  # noqa: F401
    PredictionContext,
    register_prediction_type,
    registry,
)

from . import prediction  # noqa: F401
from .prediction import Prediction  # noqa: F401

import importlib

for import_prediction in ["dummy"]:
    try:
        importlib.import_module(f".{import_prediction}", "lori.prediction")

    except ModuleNotFoundError:
        # TODO: Implement meaningful logging here
        pass

del importlib
