# -*- coding: utf-8 -*-
"""
lori.connectors.context
~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from typing import Any, Callable, Collection, Optional, Type, TypeVar

from lori.connectors.core import _Connector
from lori.core import Configurations, Context, Registrator, RegistratorContext, Registry

C = TypeVar("C", bound=_Connector)

registry = Registry[_Connector]()


# noinspection PyShadowingBuiltins
def register_connector_type(
    type: str,
    *alias: str,
    factory: Callable[[Context | Registrator, Optional[Configurations]], C] = None,
    replace: bool = False,
) -> Callable[[Type[C]], Type[C]]:
    # noinspection PyShadowingNames
    def _register(cls: Type[C]) -> Type[C]:
        registry.register(cls, type, *alias, factory=factory, replace=replace)
        return cls

    return _register


class ConnectorContext(RegistratorContext[C]):
    def __init__(self, context: Context, **kwargs) -> None:
        super().__init__(context, "connectors", **kwargs)

    @property
    def _registry(self) -> Registry[C]:
        return registry

    def load(self, configs: Optional[Configurations] = None, **kwargs: Any) -> Collection[C]:
        if configs is None:
            configs = self._get_registrator_section()
        return self._load(self, configs, includes=_Connector.INCLUDES, **kwargs)
