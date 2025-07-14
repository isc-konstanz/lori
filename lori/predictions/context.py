# -*- coding: utf-8 -*-
"""
lori.prediction.context
~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from typing import Any, Callable, Collection, Optional, Type, TypeVar

from lori.predictions.core import _Prediction
from lori.core import Configurations, Context, Registrator, RegistratorContext, Registry

P = TypeVar("P", bound=_Prediction)

registry = Registry[_Prediction]()


# noinspection PyShadowingBuiltins
def register_prediction_type(
    type: str,
    *alias: str,
    factory: Callable[[Context | Registrator, Optional[Configurations]], P] = None,
    replace: bool = False,
) -> Callable[[Type[P]], Type[P]]:
    # noinspection PyShadowingNames
    def _register(cls: Type[P]) -> Type[P]:
        registry.register(cls, type, *alias, factory=factory, replace=replace)
        return cls

    return _register


class PredictionContext(RegistratorContext[P]):
    def __init__(self, context: Context, **kwargs) -> None:
        super().__init__(context, "predictions", **kwargs)

    @property
    def _registry(self) -> Registry[P]:
        return registry

    def load(self, configs: Optional[Configurations] = None, **kwargs: Any) -> Collection[P]:
        if configs is None:
            configs = self._get_registrator_section()
        return self._load(self, configs, includes=_Prediction.INCLUDES, **kwargs)
