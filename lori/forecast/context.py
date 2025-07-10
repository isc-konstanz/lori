# -*- coding: utf-8 -*-
"""
lori.forecast.context
~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from typing import Any, Callable, Collection, Optional, Type, TypeVar

from lori.forecast.core import _Forecast
from lori.core import Configurations, Context, Registrator, RegistratorContext, Registry

F = TypeVar("F", bound=_Forecast)

registry = Registry[_Forecast]()


# noinspection PyShadowingBuiltins
def register_forecast_type(
    type: str,
    *alias: str,
    factory: Callable[[Context | Registrator, Optional[Configurations]], F] = None,
    replace: bool = False,
) -> Callable[[Type[F]], Type[F]]:
    # noinspection PyShadowingNames
    def _register(cls: Type[F]) -> Type[F]:
        registry.register(cls, type, *alias, factory=factory, replace=replace)
        return cls

    return _register


class ForecastContext(RegistratorContext[F]):
    def __init__(self, context: Context, **kwargs) -> None:
        super().__init__(context, "forecasts", **kwargs)

    @property
    def _registry(self) -> Registry[F]:
        return registry

    def load(self, configs: Optional[Configurations] = None, **kwargs: Any) -> Collection[F]:
        if configs is None:
            configs = self._get_registrator_section()
        return self._load(self, configs, includes=_Forecast.INCLUDES, **kwargs)
