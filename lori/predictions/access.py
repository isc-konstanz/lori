# -*- coding: utf-8 -*-
"""
lori.predictions.access
~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from typing import Any, Collection, Optional, TypeVar

from lori.predictions.core import _Prediction
from lori.core import Configurations, Directory, Registrator, RegistratorAccess, RegistratorContext, ResourceException
from lori.util import get_context

P = TypeVar("P", bound=_Prediction)


class PredictionAccess(RegistratorAccess[P]):
    # noinspection PyUnresolvedReferences
    def __init__(self, registrar: Registrator, **kwargs) -> None:
        context = get_context(registrar, RegistratorContext).context.predictions
        super().__init__(context, registrar, "connectors", **kwargs)

    # noinspection PyShadowingBuiltins
    def _set(self, id: str, prediction: P) -> None:
        if not isinstance(prediction, _Prediction):
            raise ResourceException(f"Invalid connector type: {type(prediction)}")

        super()._set(id, prediction)

    def load(
        self,
        configs: Optional[Configurations] = None,
        configs_file: Optional[str] = None,
        configs_dir: Optional[str | Directory] = None,
        configure: bool = False,
        **kwargs: Any,
    ) -> Collection[P]:
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
            includes=_Prediction.INCLUDES,
            **kwargs,
        )
