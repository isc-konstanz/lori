# -*- coding: utf-8 -*-
"""
lori.forecast
~~~~~~~~~~~~~


"""

from .core import (  # noqa: F401
    _Forecast,
    ForecastException,
    ForecastUnavailableException,
)

from . import access  # noqa: F401
from .access import ForecastAccess  # noqa: F401

from . import context  # noqa: F401
from .context import (  # noqa: F401
    ForecastContext,
    register_forecast_type,
    registry,
)

from . import forecast  # noqa: F401
from .forecast import Forecast  # noqa: F401

import importlib

for import_forecast in ["dummy"]:
    try:
        importlib.import_module(f".{import_forecast}", "lori.forecast")

    except ModuleNotFoundError:
        # TODO: Implement meaningful logging here
        pass

del importlib
