# -*- coding: utf-8 -*-
"""
lori.core.resources
~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any, Callable, Generic, Iterable, Iterator, List, Tuple, TypeVar

import numpy as np
from lori.core import Resource

R = TypeVar("R", bound=Resource)


class Resources(Generic[R], Sequence[R]):
    _resources: List[R]

    def __init__(self, resources=()) -> None:
        self._logger = logging.getLogger(__name__)
        self._resources = [*resources]

    def __repr__(self) -> str:
        return f"{type(self).__name__}({[c.id for c in self._resources]})"

    def __str__(self) -> str:
        return f"{type(self).__name__}:\n\t" + "\n\t".join([f"{c.id} = {repr(c)}" for c in self._resources])

    def __contains__(self, __x: object) -> bool:
        return __x in self._resources

    def __getitem__(self, index: int) -> R:
        return self._resources[index]

    def __iter__(self) -> Iterator[R]:
        return iter(self._resources)

    def __len__(self) -> int:
        return len(self._resources)

    def append(self, resource: R) -> None:
        self._resources.append(resource)

    def extend(self, resources: Iterable[R]) -> None:
        self._resources.extend(resources)

    def update(self, resources: Iterable[R]) -> None:
        resource_ids = [r.id for r in resources]
        for resource in [r for r in self._resources if r.id in resource_ids]:
            self._resources.remove(resource)
        self._resources.extend(resources)

    def copy(self):
        return type(self)([resource.copy() for resource in self._resources])

    def apply(self, apply: Callable[[R], R]):
        return type(self)([apply(resource.copy()) for resource in self._resources])

    # noinspection PyShadowingBuiltins
    def filter(self, filter: Callable[[R], bool]):
        return type(self)([resource for resource in self._resources if filter(resource)])

    # noinspection SpellCheckingInspection
    def groupby(self, by: str) -> Iterator[Tuple[Any, Sequence[R]]]:
        for group_by in np.unique([getattr(r, by) for r in self]):
            yield group_by, self.filter(lambda r: getattr(r, by) == group_by)
