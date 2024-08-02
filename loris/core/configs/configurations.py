# -*- coding: utf-8 -*-
"""
loris.core.configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import datetime as dt
import os
import shutil
from collections import OrderedDict
from collections.abc import Mapping, MutableMapping
from copy import deepcopy
from pathlib import Path
from typing import Any, List, Optional

import pandas as pd
from loris.core import ResourceException, ResourceUnavailableException
from loris.core.configs import Directories
from loris.util import to_bool, to_date, to_float, to_int


class Configurations(MutableMapping[str, Any]):
    @classmethod
    def load(
        cls,
        conf_file: str,
        conf_dir: str = None,
        data_dir: str = None,
        tmp_dir: str = None,
        log_dir: str = None,
        lib_dir: str = None,
        flat: bool = False,
        require: bool = True,
        **kwargs,
    ) -> Configurations:
        if not conf_dir and flat:
            conf_dir = ""

        conf_dirs = Directories(lib_dir, log_dir, tmp_dir, data_dir, conf_dir)
        conf_path = Path(conf_dirs.conf, conf_file)

        if conf_dirs.conf.is_dir():
            if not conf_path.is_file():
                config_default = str(conf_path).replace(".conf", ".default.conf")
                if os.path.isfile(config_default):
                    shutil.copy(config_default, conf_path)
        elif require:
            raise ConfigurationUnavailableException(f"Invalid configuration directory: {conf_dirs.conf}")

        configs = cls(conf_file, conf_dirs, **kwargs)
        configs._load(require)
        return configs

    # noinspection PyProtectedMember
    def _load(self, require: bool = True) -> None:
        if self.__path.is_file():
            try:
                # TODO: Implement other configuration parsers
                self._load_toml(str(self.__path))
            except Exception as e:
                raise ConfigurationUnavailableException(f"Error loading configuration file '{self.__path}': {str(e)}")

        elif require:
            raise ConfigurationUnavailableException(f"Invalid configuration file '{self.__path}'")

        for section in self.sections:
            self[section]._load(require=False)

        self.__dirs.update(self.get_section(Directories.SECTION, defaults={}))

    def _load_toml(self, config_path: str) -> None:
        from .toml import load_toml

        self.update(load_toml(config_path))

    def __init__(
        self,
        name: str,
        dirs: Directories,
        defaults: Optional[Mapping[str, Any]] = None,
        **kwargs
    ) -> None:
        super().__init__()
        self.__configs = OrderedDict()
        self.__dirs = dirs
        self.__path = Path(dirs.conf, name)

        if defaults is not None:
            self.__update(defaults)
        self.__update(kwargs)

    def __repr__(self) -> str:
        return f"{Configurations.__name__}({self.__path})"

    def __str__(self) -> str:
        configs = deepcopy(self.__configs)
        for section in [s for s, c in self.__configs.items() if isinstance(c, Mapping)]:
            configs.move_to_end(section)

        # noinspection PyShadowingNames
        def parse_section(header: str, section: Mapping[str, Any]) -> str:
            string = f"[{header}]\n"
            for k, v in section.items():
                if isinstance(v, Mapping):
                    string += "\n" + parse_section(f"{header}.{k}", v)
                else:
                    string += f"{k} = {v}\n"
            return string

        return parse_section(self.name.replace(".conf", ""), configs)

    def __delitem__(self, key: str) -> None:
        del self.__configs[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def set(self, key: str, value: Any) -> None:
        self.__configs[key] = value

    def __getitem__(self, key: str) -> Any:
        return self.__configs[key]

    def get(self, key: str, default: Any = None) -> Any:
        if default is None:
            return self.__configs.get(key)
        return self.__configs.get(key, default)

    def get_bool(self, key, default: bool = None) -> bool:
        return to_bool(self.get(key, default))

    def get_int(self, key, default: int = None) -> int:
        return to_int(self.get(key, default))

    def get_float(self, key, default: float = None) -> float:
        return to_float(self.get(key, default))

    def get_date(self, key, default: dt.datetime | pd.Timestamp = None) -> pd.Timestamp:
        return to_date(self.get(key, default))

    def __iter__(self):
        return iter(self.__configs)

    def __len__(self) -> int:
        return len(self.__configs)

    def move_to_top(self, key: str) -> None:
        self.__configs.move_to_end(key, False)

    def move_to_bottom(self, key: str) -> None:
        self.__configs.move_to_end(key, True)

    def copy(self) -> Configurations:
        return Configurations(self.name, self.dirs, deepcopy(self.__configs))

    @property
    def name(self) -> str:
        return str(self.__path.name)

    @property
    def path(self) -> str:
        return str(self.__path)

    @property
    def dirs(self) -> Directories:
        return self.__dirs

    @property
    def enabled(self) -> bool:
        return to_bool(self.get("enabled", default=True)) and not to_bool(self.get("disabled", default=False))

    @property
    def sections(self) -> List[str]:
        return [k for k, v in self.items() if isinstance(v, Configurations)]

    def has_section(self, section: str) -> bool:
        if section in [k for k, v in self.items() if isinstance(v, Configurations)]:
            return True
        return False

    def get_section(self, section: str, defaults: Optional[Mapping[str, Any]] = None) -> Configurations:
        if self.has_section(section):
            section = self[section]
        elif defaults is not None:
            section = self.__new_section(section, defaults)
        else:
            raise ConfigurationUnavailableException(f"Unknown configuration section: {section}")
        return section

    def _add_section(self, section, configs: Mapping[str, Any]) -> None:
        if self.has_section(section):
            raise ConfigurationUnavailableException(f"Unable to add existing configuration section: {section}")
        self[section] = self.__new_section(section, configs)

    def __new_section(self, section, configs: Mapping[str, Any]) -> Configurations:
        if not isinstance(configs, Mapping):
            raise ConfigurationException(f"Invalid configuration '{section}': {type(configs)}")
        section_name = f"{section}.conf"
        section_dirs = self.__dirs.copy()
        section_dirs.conf = str(self.__path).replace(".conf", ".d")
        return Configurations(section_name, section_dirs, configs)

    def __update(self, u: Mapping[str, Any], replace: bool = True) -> Configurations:
        for k, v in u.items():
            if isinstance(v, Mapping):
                if k not in self.keys():
                    self[k] = self.__new_section(k, v)
                self[k] = Configurations.__update(self[k], v)
            elif k not in self or replace:
                self[k] = v
        return self

    def update(self, u: Mapping[str, Any], replace: bool = True) -> None:
        self.__update(u, replace)


class ConfigurationException(ResourceException):
    """
    Raise if a configuration is invalid.

    """


class ConfigurationUnavailableException(ResourceUnavailableException, ConfigurationException):
    """
    Raise if a configuration file can not be found.

    """
