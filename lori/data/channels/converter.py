# -*- coding: utf-8 -*-
"""
lori.data.channels.converter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, List, Optional

import pandas as pd
from lori.core import ResourceException


class ChannelConverter:
    __configs: OrderedDict[str, Any]

    # noinspection PyShadowingBuiltins
    def __init__(self, converter, **configs: Any) -> None:
        self.__configs = OrderedDict(configs)
        self._converter = self._assert_converter(converter)

        self.enabled = self.__configs.pop("enabled", converter is not None)

    # noinspection PyMethodMayBeStatic
    def _assert_converter(self, converter):
        from lori.converters import Converter

        if converter is None or not isinstance(converter, Converter):
            raise ResourceException(f"Invalid converter: {None if converter is None else type(converter)}")
        return converter

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, ChannelConverter)
            and self._converter == other._converter
            and self._get_vars() == other._get_vars()
        )

    def __hash__(self) -> int:
        return hash((self._converter, *self._get_vars()))

    def __contains__(self, attr: str) -> bool:
        return attr in self._get_attrs()

    def __getattr__(self, attr):
        # __getattr__ gets called when the item is not found via __getattribute__
        # To avoid recursion, call __getattribute__ directly to get components dict
        configs = ChannelConverter.__getattribute__(self, f"_{ChannelConverter.__name__}__configs")
        if attr in configs.keys():
            return configs[attr]
        raise AttributeError(f"'{type(self).__name__}' object has no configuration '{attr}'")

    def __getitem__(self, attr: str) -> Any:
        value = self.get(attr)
        if value is not None:
            return value
        raise KeyError(attr)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.key})"

    def __str__(self) -> str:
        return f"{type(self).__name__}:\n\tid={self.id}\n\t" + "\n\t".join(
            f"{k}={v}" for k, v in self._get_vars().items()
        )

    def __call__(self, value: Any) -> Any:
        return self._converter.to_dtype(value, **self._get_configs())

    @property
    def id(self) -> str:
        return self._converter.id

    @property
    def key(self) -> str:
        return self._converter.key

    def to_str(self, value: Any) -> str:
        return self._converter.to_str(value)

    def to_json(self, value: Any) -> str:
        return self._converter.to_json(value)

    def to_series(self, value: Any, timestamp: Optional[pd.Timestamp] = None, name: Optional[str] = None) -> pd.Series:
        return self._converter.to_series(value, timestamp=timestamp, name=name)

    def get(self, attr: str, default: Optional[Any] = None) -> Any:
        return self._get_vars().get(attr, default)

    # noinspection PyShadowingBuiltins
    def _get_vars(self) -> Dict[str, Any]:
        vars = self._copy_configs()
        vars["enabled"] = self.enabled
        return vars

    def _get_attrs(self) -> List[str]:
        return [*self._copy_configs().keys(), "enabled"]

    def _get_configs(self) -> Dict[str, Any]:
        return self.__configs

    def _copy_configs(self) -> Dict[str, Any]:
        return OrderedDict(**self._get_configs())

    def copy(self) -> ChannelConverter:
        configs = self._copy_configs()
        configs["enabled"] = self.enabled
        return type(self)(self._converter, **configs)
