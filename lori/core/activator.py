# -*- coding: utf-8 -*-
"""
lori.core.activator
~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from functools import wraps
from typing import Dict

from lori.core.configs import ConfigurationException
from lori.core.configs.configurator import Configurator, ConfiguratorMeta


class ActivatorMeta(ConfiguratorMeta):
    # noinspection PyProtectedMember
    def __call__(cls, *args, **kwargs):
        activator = super().__call__(*args, **kwargs)
        cls._wrap_method(activator, "activate")
        cls._wrap_method(activator, "deactivate")

        return activator


# noinspection PyAbstractClass
class Activator(Configurator, metaclass=ActivatorMeta):
    _active: bool = False

    def __enter__(self) -> Activator:
        self.activate()
        return self

    # noinspection PyShadowingBuiltins
    def __exit__(self, type, value, traceback):
        self.deactivate()

    # noinspection PyShadowingBuiltins
    def _convert_vars(self, convert: callable = str) -> Dict[str, str]:
        values = super()._convert_vars(convert)
        values["active"] = str(self.is_active())
        return values

    def is_active(self) -> bool:
        return self._active

    def activate(self) -> None:
        pass

    # noinspection PyUnresolvedReferences
    @wraps(activate, updated=())
    def _do_activate(self, *args, **kwargs) -> None:
        if not self.is_enabled():
            raise ConfigurationException(f"Trying to activate disabled '{type(self).__name__}': {self.id}")
        if not self.is_configured():
            raise ConfigurationException(f"Trying to activate unconfigured '{type(self).__name__}': {self.id}")
        if self.is_active():
            self._logger.warning(f"Trying to activate already active '{type(self).__name__}': {self.id}")
            return

        self._at_activate()
        self._run_activate(*args, **kwargs)
        self._on_activate()
        self._active = True

    def _at_activate(self) -> None:
        pass

    def _on_activate(self) -> None:
        pass

    def deactivate(self) -> None:
        pass

    # noinspection PyUnresolvedReferences
    @wraps(deactivate, updated=())
    def _do_deactivate(self) -> None:
        if not self.is_active():
            return

        self._at_deactivate()
        self._run_deactivate()
        self._on_deactivate()
        self._active = False

    def _at_deactivate(self) -> None:
        pass

    def _on_deactivate(self) -> None:
        pass
