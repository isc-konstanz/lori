# -*- coding: utf-8 -*-
"""
lori.components.access
~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import glob
import os.path
from collections.abc import Callable
from typing import Any, Collection, Mapping, Optional, Type, TypeVar

from lori import Context
from lori.components.core import _Component
from lori.core import Configurations, Directory, ResourceException
from lori.core.register import Registrator, RegistratorAccess, RegistratorContext
from lori.util import get_context, update_recursive

C = TypeVar("C", bound=_Component)


class ComponentAccess(RegistratorAccess[C]):
    # noinspection PyUnresolvedReferences
    def __init__(self, registrar: Registrator, **kwargs) -> None:
        context = get_context(registrar, RegistratorContext).context.components
        super().__init__(context, registrar, "components", **kwargs)

    # noinspection PyShadowingBuiltins
    def _set(self, id: str, component: C) -> None:
        if not isinstance(component, _Component):
            raise ResourceException(f"Invalid component type: {type(component)}")

        super()._set(id, component)

    # noinspection PyProtectedMember
    def load(
        self,
        configs: Optional[Configurations] = None,
        configs_file: Optional[str] = None,
        configs_dir: Optional[str | Directory] = None,
        configure: bool = False,
        **kwargs: Any,
    ) -> Collection[C]:
        defaults = _Component._build_defaults(self._registrar.configs, strict=True)
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
            includes=_Component.INCLUDES,
            defaults=defaults,
            **kwargs,
        )

    # noinspection PyShadowingBuiltins, PyProtectedMember
    def load_from_type(
        self,
        type: Type[C],
        configs: Configurations,
        section: str,
        key: str,
        name: Optional[str] = None,
        includes: Optional[Collection[str]] = (),
        defaults: Optional[Mapping[str, Any]] = None,
        configure: bool = False,
        sort: bool = True,
        **kwargs,
    ) -> Collection[C]:
        kwargs["factory"] = type
        components = []
        if defaults is None:
            defaults = _Component._build_defaults(self._registrar.configs, strict=True)
        if any(i in configs.sections for i in includes):
            configs["key"] = key
            configs["name"] = name
        configs = configs.get_section(section, defaults={**configs.get_sections(includes), **defaults})
        if any(i in configs.sections for i in includes):
            components.append(self._load_from_configs(self._registrar, configs, **kwargs))

        update_recursive(defaults, _Component._build_defaults(configs, includes))

        configs_dirs = configs.dirs.copy()
        configs_sections = configs.get_sections([s for s in configs.sections if s not in defaults])

        components.extend(self._load_from_sections(self._registrar, configs_sections, defaults=defaults, **kwargs))

        if "alias" in configs:
            key = configs.get("alias")
        for configs_path in glob.glob(str(configs_dirs.conf.joinpath(f"{key}*.conf"))):
            if configs.name == os.path.basename(configs_path):
                continue

            configs = Configurations.load(
                configs_path,
                **configs_dirs.to_dict(),
                **defaults,
            )
            components.append(self._load_from_configs(self._registrar, configs, **kwargs))

        if sort:
            self.sort()
        if configure:
            self.configure(components)
        return components

    def _create(
        self,
        context: Context | Registrator,
        configs: Configurations,
        factory: Optional[Callable[..., C]] = None,
        **kwargs: Any,
    ) -> C:
        if factory is None:
            factory = super()._create
        return factory(context, configs, **kwargs)
