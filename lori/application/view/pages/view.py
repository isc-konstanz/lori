# -*- coding: utf-8 -*-
"""
lori.application.view.pages.view
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from functools import wraps
from typing import Callable, Dict, Optional, Type, TypeVar

import dash_bootstrap_components as dbc
from dash import html

from lori.application.view.pages import PageFooter, PageHeader, PageLayout
from lori.application.view.pages.components import ComponentGroup, ComponentPage, ComponentRegistry
from lori.components import Component, ComponentContext
from lori.system import System

G = TypeVar("G", bound=ComponentGroup)
P = TypeVar("P", bound=ComponentPage)
C = TypeVar("C", Component, System)

registry = ComponentRegistry()


# noinspection PyShadowingBuiltins
def register_component_page(
    *types: Type[C],
    factory: Optional[Callable] = None,
    replace: bool = False,
) -> Callable[[Type[P]], Type[P]]:
    # noinspection PyShadowingNames
    def _register(cls: Type[P]) -> Type[P]:
        registry.register_page(cls, *types, factory=factory, replace=replace)
        return cls

    return _register


# noinspection PyShadowingBuiltins
def register_component_group(
    *types: Type[C],
    key: Optional[str] = None,
    name: Optional[str] = None,
    factory: Optional[Callable] = None,
    replace: bool = False,
) -> Callable[[Type[G]], Type[G]]:
    # noinspection PyShadowingNames
    def _register(cls: Type[G]) -> Type[G]:
        registry.register_group(cls, *types, key=key, name=name, factory=factory, replace=replace)
        return cls

    return _register


class View(ComponentGroup):
    groups: Dict[str, ComponentGroup]

    # noinspection PyShadowingBuiltins
    def __init__(self, id: str, header: PageHeader, footer: PageFooter, *args, **kwargs) -> None:
        super().__init__(id=f"{id}-view", name="View", path="/", *args, **kwargs)
        self.header = header
        self.footer = footer

        self.groups = dict[str, ComponentGroup]()

    @property
    def key(self) -> str:
        return "view"

    @property
    def path(self) -> str:
        return "/"

    # noinspection PyProtectedMember
    def create_layout(self, layout: PageLayout) -> None:
        if all(isinstance(p._component, System) for p in self):
            label = "Systems"
        else:
            label = "Select"

        layout.menu = dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem(label, header=True),
                *[dbc.DropdownMenuItem(p.name, href=p.path) for p in self],
            ],
            nav=True,
            in_navbar=True,
            label=label,
        )

        layout.container.class_name = "card-container card-focus"
        layout.container.children = []
        for page in self._pages:
            page_cards = []
            if isinstance(page, ComponentGroup):
                layout.append(
                    dbc.Row(dbc.Col(html.A(html.H4(f"{page.name}:"), className="card-header", href=page.path)))
                )
                for page_group in page:
                    if page_group.layout.has_card_items():
                        page_cards.append(page_group.layout.card)
            else:
                if page.layout.has_card_items():
                    page_cards.append(page.layout.card)

            layout.append(dbc.Row([dbc.Col(card, width="auto") for card in page_cards]))

    # noinspection PyTypeChecker, PyUnresolvedReferences, PyArgumentList
    @wraps(create_layout, updated=())
    def _do_create_layout(self) -> PageLayout:
        for page in self:
            page._do_create_layout()
        for group in self.groups.values():
            group_layout = group._do_create_layout()
            if group_layout.has_menu_item():
                self.header.menu.append(group_layout.menu)

        layout = super()._do_create_layout()
        self.header.menu.insert(0, layout.menu)

        return layout

    # noinspection PyTypeChecker, PyUnresolvedReferences
    def _do_create_pages(self, components: ComponentContext) -> None:
        systems = [s for s in components.filter(lambda c: isinstance(c, System))]
        for system in systems:
            system_page = self._new_page(self, system)
            for component in system.values():
                self._new_page(system_page, component)

        for component in components.filter(lambda c: all(c != s and c not in s for s in systems)):
            self._new_page(self, component)

    def _new_page(self, view: ComponentGroup, component: Component) -> Optional[ComponentPage]:
        if not component.is_enabled():
            self._logger.debug(f"Skipping page creation for disabled {type(component).__name__} '{component.id}'")
            return

        _type = type(component)
        if not registry.has_page(_type):
            return

        page = registry.get_page(_type).initialize(component)
        if page is not None:
            group = self._get_group(component)
            if group is not None:
                group.append(page)
                page.group = group
            view.append(page)
        return page

    def _new_group(self, component: Component) -> Optional[ComponentGroup]:
        _type = type(component)
        if not registry.has_group(_type):
            return

        registration = registry.get_group(_type)
        group = registration.initialize(id=f"{self.id}-{registration.key}", key=registration.key, name=registration.name)
        if group is not None:
            self.groups[registration.key] = group
        return group

    def _get_group(self, component: Component) -> Optional[ComponentGroup]:
        _type = type(component)
        if not registry.has_group(_type):
            return
        group = self.groups.get(registry.get_group(_type).key, None)
        if group is None:
            group = self._new_group(component)
        return group

    def _do_register(self) -> None:
        groups = self.groups.values()
        for page in [p for p in self if p not in groups]:
            if page.is_active():
                page._do_register()
        for group in groups:
            group._do_register()
        return super()._do_register()
