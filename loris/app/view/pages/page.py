# -*- coding: utf-8 -*-
"""
loris.app.view.pages.page
~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import logging
import re
from abc import ABC, ABCMeta, abstractmethod
from functools import wraps
from typing import Collection, Optional

import dash
from dash.development.base_component import Component as DashComponent
from dash_bootstrap_components import Container

from loris.app import ServerException


class PageMeta(ABCMeta):
    # noinspection PyProtectedMember
    def __call__(cls, *args, **kwargs):
        page = super().__call__(*args, **kwargs)

        page._Page__create_layout = page.create_layout
        page.create_layout = page._do_create_layout

        page._Page__register = page.register
        page.register = page._do_register

        return page


# noinspection PyShadowingBuiltins
class Page(ABC, metaclass=PageMeta):
    id: str
    name: str
    title: str
    description: Optional[str]

    layout: PageLayout

    _created: bool = False
    _registered: bool = False

    def __init__(
        self,
        id: str,
        name: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        *args, **kwargs
    ) -> None:
        super().__init__()
        self._logger = logging.getLogger(self.__module__)

        self.id = self._encode_id(id)
        self.name = name
        self.title = title if title is not None else name
        self.description = description

    @property
    @abstractmethod
    def path(self) -> str:
        pass

    def is_created(self) -> bool:
        return self._created

    @abstractmethod
    def create_layout(self) -> PageLayout:
        pass

    # noinspection PyUnresolvedReferences
    @wraps(create_layout, updated=())
    def _do_create_layout(self) -> PageLayout:
        if self.is_registered():
            raise PageException(f"Trying to create layout of already registered {type(self).__name__}: {self.name}")
        if self.is_created():
            self._logger.warning(f"{type(self).__name__} '{self.id}' layout already created")
        else:
            self.layout = self.__create_layout()
            self._on_create_layout(self.layout)
            self._created = True

        return self.layout

    def _on_create_layout(self, layout: PageLayout) -> None:
        pass

    def is_registered(self) -> bool:
        return self._registered

    # noinspection PyMethodMayBeStatic
    def register(self, **kwargs) -> None:
        dash.register_page(
            self.id,
            path=self.path,
            name=self.name,
            title=self.title,
            description=self.description,
            layout=Container(
                self.layout.content,
                id=f"{self.id}-content",
                style={"padding-top": "1rem", "padding-bottom": "1rem"},
            ),
            **kwargs,
        )

    # noinspection PyUnresolvedReferences
    @wraps(register, updated=())
    def _do_register(self) -> None:
        if not self.is_created():
            raise PageException(f"Trying to register {type(self).__name__} without layout: {self.name}")
        if self.is_registered():
            self._logger.warning(f"{type(self).__name__} '{self.id}' already registered")
            return

        self._logger.debug(f"Registering {type(self).__name__} '{self.id}': {self.name}")

        self.__register()
        self._on_register()
        self._registered = True

    def _on_register(self) -> None:
        pass

    @staticmethod
    def _encode_id(id) -> str:
        # TODO: Implement correct URI encoding
        return re.sub("[^\\w]+", "-", id).lower()


class PageException(ServerException):
    """
    Raise if an error occurred accessing a page.

    """


class PageLayoutException(PageException):
    """
    Raise if an error occurred handling a page layout.

    """


class PageLayout:
    menu: Optional[DashComponent]
    focus: Optional[DashComponent]

    content: DashComponent | Collection[DashComponent]

    def __init__(
        self,
        content: DashComponent | Collection[DashComponent],
        focus: Optional[DashComponent] = None,
        menu: Optional[DashComponent] = None,
    ) -> None:
        self.content = content
        self.focus = focus
        self.menu = menu

    def has_menu_item(self) -> bool:
        return self.menu is not None

    def has_focus_view(self) -> bool:
        return self.focus is not None