# -*- coding: utf-8 -*-
"""
lori.components.context
~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from typing import Callable, Optional, Type, TypeVar, overload

from lori.components import Component
from lori.core import Context, Registrator, RegistratorContext, Registry
from lori.core.configs import ConfigurationException, Configurations, Configurator

C = TypeVar("C", bound=Component)

registry = Registry[Component]()


@overload
def register_component_type(cls: Type[C]) -> Type[C]: ...


@overload
def register_component_type(
    *alias: Optional[str],
    factory: Callable[..., Type[C]] = None,
    replace: bool = False,
) -> Type[C]: ...


def register_component_type(
    *args: Optional[Type[C], str],
    **kwargs,
) -> Type[C] | Callable[[Type[C]], Type[C]]:
    args = list(args)
    if len(args) > 0 and isinstance(args[0], type):
        cls = args.pop(0)
        registry.register(cls, *args, **kwargs)
        return cls

    # noinspection PyShadowingNames
    def _register(cls: Type[C]) -> Type[C]:
        registry.register(cls, *args, **kwargs)
        return cls

    return _register


class ComponentContext(RegistratorContext[Component], Configurator):
    SECTION: str = "components"

    def __init__(self, context: Context, *args, **kwargs) -> None:
        from lori.data.context import DataContext

        if context is None or not isinstance(context, DataContext):
            raise ConfigurationException(f"Invalid data context: {None if context is None else type(context)}")
        super().__init__(context, *args, **kwargs)

    @property
    def _registry(self) -> Registry[Component]:
        return registry

    def configure(self, configs: Configurations) -> None:
        super().configure(configs)
        self._load(self, configs)

    def _load(
        self,
        context: Registrator | RegistratorContext,
        configs: Configurations,
        configs_file: str = "components.conf",
    ) -> None:
        defaults = {}
        configs = configs.copy()
        if configs.has_section(self.SECTION):
            components = configs.get_section(self.SECTION)
            for section in self._get_type().SECTIONS:
                if section in components:
                    defaults.update(components.pop(section))

            self._load_sections(context, components, defaults)

        context_dirs = [
            str(c.configs.dirs.conf)
            for c in self.context.components.values()
            if c != self and isinstance(c, RegistratorContext)
        ]
        if str(configs.dirs.conf) not in context_dirs:
            self._load_from_file(context, configs.dirs, configs_file, defaults)
            self._load_from_dir(context, str(configs.dirs.conf), defaults)
