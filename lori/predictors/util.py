# -*- coding: utf-8 -*-
"""
lori.predictors.util
~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import numpy as np
import pandas as pd


def prediction_correction(
        prediction_in: pd.Series,
        current: float,
        t_half: int = 12,
) -> pd.Series:
    """
    F = external prediction
    R = results
    R_k+1 = F_k+1 + kappa * (R_k - F_k)
    kappa = 2^dt/t_half
    """
    index = prediction_in.index
    values = prediction_in.values
    times = index.to_series().diff().dt.total_seconds().fillna(0).values / 3600.0
    kappas = 2 ** -(times / t_half)

    prediction_out = np.empty_like(values, dtype=float)
    prediction_out[0] = current

    for i in range(1, len(values)):
        prediction_out[i] = values[i] + kappas[i] * (prediction_out[i - 1] - values[i - 1])

    return pd.Series(prediction_out, index=index, name=prediction_in.name)


def prediction_correction_slow(
        prediction_values: pd.Series,
        current: float,
        t_half: int = 12,
) -> pd.Series:
    """
    F = external prediction
    R = results
    R_k+1 = F_k+1 + kappa * (R_k - F_k)
    kappa = 2^dt/t_half
    """

    results = [current]
    for index in range(1, len(prediction_values)):
        dt = (prediction_values.index[index] - prediction_values.index[index - 1]).total_seconds() / 3600.0
        kappa = 2 ** -(dt / t_half)
        results.append(prediction_values.iloc[index] + kappa * (results[index - 1] - prediction_values.iloc[index - 1]))
    return pd.Series(results, index=prediction_values.index, name=prediction_values.name)
