# -*- coding: utf-8 -*-
"""
lori.forecast.access
~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from typing import Any, Collection, Optional, TypeVar

from lori.forecast.core import _Forecast
from lori.core import Configurations, Directory, Registrator, RegistratorAccess, RegistratorContext, ResourceException
from lori.util import get_context

F = TypeVar("F", bound=_Forecast)


class ForecastAccess(RegistratorAccess[F]):
    # noinspection PyUnresolvedReferences
    def __init__(self, registrar: Registrator, **kwargs) -> None:
        context = get_context(registrar, RegistratorContext).context.forecasts
        super().__init__(context, registrar, "connectors", **kwargs)

    # noinspection PyShadowingBuiltins
    def _set(self, id: str, forecast: F) -> None:
        if not isinstance(forecast, _Forecast):
            raise ResourceException(f"Invalid connector type: {type(forecast)}")

        super()._set(id, forecast)

    def load(
        self,
        configs: Optional[Configurations] = None,
        configs_file: Optional[str] = None,
        configs_dir: Optional[str | Directory] = None,
        configure: bool = False,
        **kwargs: Any,
    ) -> Collection[F]:
        if configs is None:
            configs = self._get_registrator_section()
        if configs_file is None:
            configs_file = configs.name
        if configs_dir is None:
            configs_dir = configs.dirs.conf.joinpath(configs.name.replace(".conf", ".d"))
        return self._load(
            self._registrar,
            configs=configs,
            configs_file=configs_file,
            configs_dir=configs_dir,
            configure=configure,
            includes=_Forecast.INCLUDES,
            **kwargs,
        )
