# -*- coding: utf-8 -*-
"""
lori.forecast.util
~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import hashlib
import re
from copy import copy, deepcopy
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import pytz as tz
from pandas.tseries.frequencies import to_offset

# FIXME: Remove this once Python >= 3.9 is a requirement
try:
    from typing import Literal

except ImportError:
    from typing_extensions import Literal


def forecast_correction(
        current,
        forecast_values:pd.Series,
        t_half,
        dt=1):
    """
    F = external forecast values
    R = model results
    R_k+1 = F_k+1 + kappa * (R_k - F_k)
    kappa = 2^dt/t_half
    """
    kappa = 2 ** -(dt / t_half)
    results = [current]
    for index in range(1, len(forecast_values)):
        results.append(forecast_values.iloc[index] + kappa * (results[index - 1] - forecast_values.iloc[index - 1]))
    return pd.Series(results, index=forecast_values.index, name=forecast_values.name)
